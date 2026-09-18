# Sickbay Health Display

A retro-futuristic health statistics display inspired by the sickbay vital-signs biobed monitor from the original Star Trek TV series. Runs on an ESP32-S3 and draws real-world data from an Oura ring (and eventually a Garmin watch) into a Star Trek TOS–styled gauge display.

## Hardware

- **Display**: Waveshare ESP32-S3-Touch-AMOLED-2.41 (600×450 px, AMOLED, capacitive touch)
- **Relay** (planned): a dedicated, always-on ESP32 on the home network that manages the Oura API connection, caches recent readings, and serves them locally to the display
- **Tunnel box** (planned): a small always-reachable box (e.g. Raspberry Pi Zero running Cloudflare Tunnel/ngrok) that terminates the public HTTPS endpoint Oura's webhooks POST to, and hands verified events to the relay ESP32 over the local network — see [`docs/oura-webhook-architecture.md`](docs/oura-webhook-architecture.md) for why the relay ESP32 doesn't do this part itself.

## Gauges

Modeled on the original prop: TEMP, BRAIN K%, LUNGS cfm, CELL RATE, BLOOD SYST., BLOOD DIAS. (vertical thermometer-style bars with danger/caution/normal/caution/danger zones), plus circular PULSE and RESPIRATION readouts. Only PULSE (heart rate), RESPIRATION (respiratory rate), and TEMP (skin temperature deviation) have a real Oura data source — the rest are TOS invention with no wearable equivalent, and are either left decorative or creatively mapped to other real metrics (HRV, SpO2, stress, activity, resilience).

## Data source: Oura API

Real-time-ish data comes from Oura's v2 REST API, not a raw Bluetooth tap on the ring (that alternative was considered and set aside for now — see [`docs/oura-direct-ble-alternative.md`](docs/oura-direct-ble-alternative.md)). Getting there requires a one-time OAuth2 registration and authorization flow — Oura's old single-user Personal Access Token shortcut is deprecated, so even this solo project needs the full OAuth dance. Practical note worth remembering: data isn't truly live — the ring only syncs to Oura's cloud when the phone app is open, so the display always shows "the most recent reading Oura has," not a continuous stream.

The full webhook-vs-polling architecture, the ESP32-as-webhook-manager design, and the reasoning behind each decision are written up in [`docs/oura-webhook-architecture.md`](docs/oura-webhook-architecture.md).

## Repository layout

```
docs/       Design and architecture notes (Oura API integration, alternatives considered)
firmware/
  display/  ESP32-S3 sickbay display firmware (LVGL UI, gauge rendering)
  relay/    Dedicated relay ESP32 firmware (Oura OAuth client, webhook handling, local caching/serving)
```

## Status

Early planning stage: Oura API architecture is scoped out, OAuth application registration in progress. No firmware written yet.
