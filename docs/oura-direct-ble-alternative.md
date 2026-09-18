# Alternative: Direct BLE Tap on the Ring (bypassing app + cloud)

## Status: real, documented, more effort — not the recommended starting point

A community reverse-engineering effort (**open_oura**, Rust) connects directly to the Oura ring over BLE, bypassing the phone app and Oura's cloud entirely. Confirmed working against Ring 3 (Horizon) and Ring 5 — covers both the current ring and the incoming one.

## What's recoverable directly from the ring

- Raw PPG samples
- IBI (inter-beat interval) → derivable heart rate
- Raw accelerometer data
- Temperature events
- SpO2
- Battery status

**Not recoverable this way:** the 0–100 Readiness/Sleep/Activity/Stress scores. These are computed on-device in the phone app via Oura's proprietary PyTorch models, not in the cloud, and the model files aren't published or reimplemented by the open-source project. Direct BLE gets you the raw signals only, not Oura's composite scores.

## Protocol specifics

- Not a standard/documented BLE profile — proprietary characteristic handles, not standard GATT UUIDs.
- Connecting requires the ring's 16-byte AES authentication key, obtained by the community via app decompilation (Ghidra) + live BLE capture analysis — not published by Oura.
- Reverse-engineering notes/tooling: [Th0rgal/open_oura](https://github.com/Th0rgal/open_oura), protocol notes at [ringverse/protocol](https://github.com/ringverse/protocol/blob/main/oura/BLE.md).

## Trade-offs vs. the cloud API + webhook path

- **Effort**: porting/re-implementing a Rust-documented BLE auth handshake (or running a bridge box that does the BLE work and re-serves JSON locally, same relay pattern as the webhook approach) is a materially bigger project than calling a documented REST API.
- **BLE connection is exclusive**: most BLE peripherals support one active central at a time — a second device holding a connection to the ring likely blocks the official app from syncing normally at the same time.
- **Battery impact**: a frequent/persistent second BLE connection would stress the current Gen 3 ring's already-failing battery further; less of a concern once the Gen 5 (fresh battery) is in hand.
- **ToS/legal**: reverse-engineering the protocol is very likely outside Oura's Terms of Service, even though it's personal hardware and personal data. Not flagged as malicious/unsafe, but a real gray area worth knowing about — not a legal opinion, just a heads-up.

## Recommendation

Treat this as the "true real-time, no-cloud-dependency" upgrade path to revisit once the Gen 5 ring arrives and the OAuth/webhook pipeline is already working end-to-end — not the starting point.
