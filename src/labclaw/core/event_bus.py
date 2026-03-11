"""Event bus — pub/sub wrapper around EventRegistry.

Provides a clean publish/subscribe interface for LabEvents with
wildcard support. For MVP this is in-memory; future versions will
use Redis Streams for persistence and cross-process delivery.

Spec: docs/specs/L2-gateway.md
Design doc: section 3 (Architecture)
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from labclaw.core.events import EventRegistry, event_registry
from labclaw.core.schemas import EventName, LabEvent, Layer

logger = logging.getLogger(__name__)


class EventBus:
    """Pub/sub event bus wrapping EventRegistry."""

    def __init__(self, registry: EventRegistry | None = None) -> None:
        self._registry = registry or event_registry
        self._handlers: dict[str, list[Callable[[LabEvent], None]]] = {}

    def publish(self, event: LabEvent) -> None:
        """Publish an event to all matching subscribers.

        Dispatches to EventRegistry handlers first (so handlers registered
        on the registry also receive events published via the bus), then
        delivers to bus-local subscribers.  Handlers registered on both
        are deduplicated by identity to prevent double-dispatch.

        Args:
            event: The LabEvent to publish.
        """
        event_name = event.event_name.full
        dispatched: set[int] = set()

        # Dispatch to EventRegistry handlers first (if event is registered)
        if self._registry.is_registered(event_name):
            with self._registry._lock:
                registry_handlers = list(self._registry._handlers.get(event_name, []))
                registry_wildcards = list(self._registry._handlers.get("*", []))
            for handler in registry_handlers:
                dispatched.add(id(handler))
                try:
                    handler(event)
                except Exception:
                    logger.exception("Registry handler error for event %s", event_name)
            for handler in registry_wildcards:
                dispatched.add(id(handler))
                try:
                    handler(event)
                except Exception:
                    logger.exception("Registry wildcard handler error for event %s", event_name)

        # Deliver to bus-local specific-name subscribers (skip already dispatched)
        for handler in self._handlers.get(event_name, []):
            if id(handler) in dispatched:
                continue
            dispatched.add(id(handler))
            try:
                handler(event)
            except Exception:
                logger.exception("Handler error for event %s", event_name)

        # Deliver to bus-local wildcard subscribers (skip already dispatched)
        for handler in self._handlers.get("*", []):
            if id(handler) in dispatched:
                continue
            try:
                handler(event)
            except Exception:
                logger.exception("Wildcard handler error for event %s", event_name)

    def subscribe(self, event_name: str, handler: Callable[[LabEvent], None]) -> None:
        """Subscribe a handler to events by name.

        Args:
            event_name: Event name to listen for, or '*' for all events.
            handler: Callback invoked with the LabEvent.
        """
        self._handlers.setdefault(event_name, []).append(handler)

    def unsubscribe(self, event_name: str, handler: Callable[[LabEvent], None]) -> None:
        """Remove a handler from an event name.

        Args:
            event_name: Event name the handler was registered for.
            handler: The handler to remove.

        Raises:
            ValueError: If the handler is not found for the event name.
        """
        handlers = self._handlers.get(event_name, [])
        try:
            handlers.remove(handler)
        except ValueError:
            raise ValueError(f"Handler not found for event {event_name!r}") from None

    def create_event(
        self,
        name: str,
        payload: dict | None = None,
        **kwargs: object,
    ) -> LabEvent:
        """Convenience: create a LabEvent from name string and publish it.

        Args:
            name: Event name in {layer}.{module}.{action} format.
            payload: Event payload dict.
            **kwargs: Additional LabEvent fields.

        Returns:
            The created LabEvent.
        """
        parsed = EventName.parse(name)

        # Ensure event is registered in the shared registry
        if not self._registry.is_registered(name):
            self._registry.register(name)

        try:
            source_layer = Layer(parsed.layer)
        except ValueError:
            source_layer = Layer.INFRA

        event = LabEvent(
            event_name=parsed,
            source_layer=source_layer,
            payload=payload or {},
            **kwargs,  # type: ignore[arg-type]
        )
        self.publish(event)
        return event
