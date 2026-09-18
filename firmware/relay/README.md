# Relay firmware

Firmware for the dedicated, always-on ESP32 that owns the Oura API relationship: OAuth token refresh, data polling/webhook handling, a short rolling cache of recent readings, and a small local HTTP API the display firmware polls.

See [`../../docs/oura-webhook-architecture.md`](../../docs/oura-webhook-architecture.md) for the full design and build order (polling first, webhook + tunnel box layered in afterward).

Not started yet — placeholder so this folder exists in the repo ahead of the code.
