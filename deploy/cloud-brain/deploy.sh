#!/bin/bash
set -euo pipefail

echo "=== LabClaw Cloud Brain Deploy ==="

# Check required env vars
if [ -z "${CF_TUNNEL_TOKEN:-}" ]; then
    echo "WARNING: CF_TUNNEL_TOKEN not set. Cloudflare tunnel will not start."
fi

# Build and start
docker compose build --no-cache
docker compose up -d

# Wait for health
echo "Waiting for health check..."
for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/brain/health > /dev/null 2>&1; then
        echo "Cloud Brain is ONLINE!"
        curl -s http://localhost:8000/brain/skills | python3 -m json.tool
        exit 0
    fi
    sleep 2
done

echo "ERROR: Health check failed after 60s"
docker compose logs brain | tail -20
exit 1
