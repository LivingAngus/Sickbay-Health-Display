# Oura Webhooks → ESP32: How They Work and How to Wire Them Up

## What an Oura webhook actually delivers

A webhook event is a *notification*, not the data itself. The POST payload is minimal:

```json
{
  "event_type": "update",
  "data_type": "daily_readiness",
  "object_id": "...",
  "event_time": "2026-09-16T08:12:00+00:00",
  "user_id": "..."
}
```

On receiving one, you still have to call the corresponding `usercollection` GET endpoint with `object_id` (using your stored OAuth access token) to fetch the actual reading. The webhook just tells you *when* to go look.

## Technical requirements to receive one

- A publicly reachable **HTTPS** endpoint (Oura does not deliver to plain HTTP or to anything behind a closed firewall).
- **Verification handshake**: when you create a subscription, Oura sends a GET to your callback URL with `verification_token` and `challenge` query params — you must respond `200` with `{"challenge": "<value>"}`.
- **Signature verification** on every event POST: headers `x-oura-signature` (HMAC-SHA256, hex, uppercase) and `x-oura-timestamp`. Compute `HMAC-SHA256(timestamp + raw_body, client_secret)` over the *raw* request body (not re-serialized JSON) and compare with a timing-safe comparison.
- Must respond `2xx` within 10 seconds or Oura retries (up to 10 times on failure/timeout).
- **Subscriptions expire** (each has an `expiration_time`) and need periodic renewal via a renew call — this has to run as an ongoing scheduled job, not a one-time setup step.

## Why a bare ESP32 shouldn't be the receiver directly

The ESP32 sits behind home NAT with no public IP, and making it directly reachable would mean port-forwarding + dynamic DNS + a real TLS certificate (kept renewed) + holding the OAuth client secret (needed for HMAC verification and for calling back to fetch data) on a bench-top embedded device. There's no mature, plug-and-play ACME/Let's-Encrypt client for ESP32 — what exists is scattered hobbyist tooling (e.g. an ESP32 ACME client on SourceForge), not something to drop in and forget. That's real, ongoing maintenance burden plus meaningful security exposure, on top of the flash/RAM overhead of a TLS server stack.

Important distinction: being an HTTPS **client** (outbound calls to Oura to fetch data, refresh tokens, renew subscriptions) is completely normal for an ESP32 and not a concern at all — it's the same thing OTA update checks or any weather-API sketch already does. It's specifically being the HTTPS **server** Oura's webhook POSTs *to* that's the hard part.

## Recommended architecture (revised 2026-09-16)

A dedicated, always-on ESP32 sitting on the home network as the "webhook manager + cache + local server for the display app" is a sound design — with one addition: don't expose that ESP32 directly to the internet. Front it with a small, dumb tunnel instead:

1. **Tunnel box** (e.g. a Raspberry Pi Zero or similar, running Cloudflare Tunnel or ngrok) — does nothing but terminate public HTTPS and the verification handshake, then hands the already-arrived webhook POST to the ESP32 over plain local HTTP. No OAuth logic, no caching, no data mapping lives here — just a dumb pipe solving the "be reachable with a valid cert" problem.
2. **Dedicated relay ESP32** (always-on, home network) — does everything originally planned:
   - Receives the forwarded webhook event from the tunnel box over local HTTP (no TLS/cert burden on the ESP32 itself).
   - Verifies the HMAC signature (still needs the client secret, but only ever sees traffic that's already reached the tunnel box first).
   - Calls back Oura over outbound HTTPS with the stored access token to fetch the real value via `object_id`.
   - Handles OAuth token refresh and periodic webhook subscription renewal (all outbound HTTPS client calls — no issue).
   - Caches recent readings (a short rolling window, not just "latest") so the display app can request a catch-up batch on startup, not just a single value.
   - Serves current + windowed history to the display app over the local network.
3. **Display app/ESP32** — on startup, requests current value + a time-bounded window of cached history from the relay; thereafter polls the relay every ~10s for refreshes. Pure local-network HTTP, no Oura credentials or TLS on this device at all.

This keeps the original design almost entirely intact — the only change is adding one small, purpose-built tunnel endpoint in front of the relay ESP32 rather than exposing it to the raw internet directly.

## Suggested build order

Given this is a hobby-pace build, prototype the relay with plain **polling** first (call `daily_readiness`/`heartrate` on a timer from the relay ESP32) to get the OAuth token handling, data reduction, caching, and display-side gauge-mapping pipeline proven end-to-end — this needs zero public reachability at all, since polling is pure outbound HTTPS client behavior. Layer in the webhook + tunnel box afterward as a latency/efficiency upgrade once the simpler path works.

## Sources
- [Oura Webhooks Skill — Hookdeck](https://hookdeck.com/webhooks/skills/oura-webhooks)
- [Guide to Oura Webhooks: Features and Best Practices — Hookdeck](https://hookdeck.com/webhooks/platforms/guide-to-oura-webhooks-features-and-best-practices)
- [Oura API Documentation (2.0)](https://cloud.ouraring.com/v2/docs)
- [Provider Webhook Subscriptions — Open Wearables](https://openwearables.io/docs/api-reference/guides/provider-webhook-subscriptions)
- [ESP32 ACME client (SourceForge) — evidence this is niche/hobbyist tooling, not turnkey](https://sourceforge.net/projects/esp32-acme-client/)
