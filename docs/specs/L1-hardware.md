# L1 Makerspace Hardware Spec

**Layer:** Hardware Drivers, Safety Interlocks & Simulators (L1)

## Purpose

The hardware layer manages 3D printers, CNC routers, laser cutters, and bench instruments in a makerspace. Every machine has a work envelope (`envelope_mm`), controller protocol (`gsender_rest`, `moonraker`, `bambu_mqtt`, `octoprint`), spindle/thermal limits, and pre-flight G-code safety validation.

## Core Tools (`DevicesSkill`)

- `device_list`: List registered 3D printers, CNCs, and bench instruments.
- `device_register`: Register a new printer, CNC machine, or robot arm.
- `device_status`: Query live machine telemetry via Moonraker, gSender REST, or OctoPrint.
- `device_validate_gcode`: Verify G-code bounding box, Z plunge vs. cutter flute length, spoilboard protection, spindle RPM, and thermal ceilings.
- `device_send_command`: Dispatch a safety-checked command (`home`, `jog`, `zero_wcs`, `run_gcode`, `emergency_stop`).
- `device_feeds_and_speeds`: Compute verified CNC RPM, feed rate, plunge rate, and stepdown for FR-4 PCBs, plywood, 6061 aluminum, and brass.
- `device_upload_job`: Validate G-code safety and upload/start a print or CNC job.
- `device_probe_heightmap`: Generate a snake-order `G38.2` copper/stock heightmap probe program and Z-warp target G-code.
- `device_render_gcode_svg`: Render a 2D SVG toolpath visualization against the machine's work envelope.
