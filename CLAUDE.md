# CarPi — Claude Code Project Context

Custom Raspberry Pi 4 car head unit. Acts as a CarPlay-style dashboard: streams Bluetooth audio from an iPhone, displays track info via AVRCP, and will eventually show OBD-II data. UI built in Kivy (Python).

## Hardware
- **Pi:** Raspberry Pi 4, hostname `LuisitoPi`, user `luisito`, local IP `10.0.0.53`
- **Phone:** iPhone on Verizon (hotspot blocked at carrier level — see Connectivity)
- **Audio out:** Pi 3.5mm jack → car aux
- **Planned:** 7–10" capacitive touchscreen

## Audio Stack
```
iPhone (Spotify) → Bluetooth A2DP → Pi (BlueZ + PipeWire 1.4.2 + WirePlumber 0.5.8)
                                         ├── AVRCP metadata → Kivy UI
                                         └── PipeWire loopback → 3.5mm → speakers
```

## Critical: WirePlumber config path
WirePlumber 0.5.x on this system reads from `/etc/xdg/wireplumber/` — NOT `/etc/wireplumber/`. The correct file:
```
/etc/xdg/wireplumber/wireplumber.conf.d/bluetooth.conf
```
`/etc/wireplumber/` and `/etc/pipewire/pipewire.conf.d/` are silently ignored.

## Project Structure
```
carpi/
├── CLAUDE.md
├── docs/carpi-docs.md   ← full troubleshooting history
├── main.py
├── car.kv
├── screens/
│   ├── home.py
│   ├── music.py
│   └── map.py
├── services/
│   ├── bluetooth.py     ← AVRCP metadata via dbus
│   ├── obd.py
│   └── audio.py
└── assets/
    ├── fonts/
    └── icons/
```

## Dev Environment
**Mac:** Python 3.12 via Homebrew (3.14 not yet supported by Kivy), venv `carpi-env`
- Run: `source carpi-env/bin/activate && python3.12 main.py`

**Windows:** conda env `voicebot2` (Python 3.11.14), Kivy 2.3.1 installed there
- Run: `conda activate voicebot2 && python main.py`

## iPhone Bluetooth
- MAC: `A0:4E:CF:79:28:38`
- Required profiles: `a2dp_sink`, `hfp_hf`, `hsp_hs`
- AVRCP exposes: Title, Artist, Album, Duration, Position, Status, Volume

## Connectivity
Verizon blocks hotspot entirely (toggle greyed out, TTL trick not applicable). Project is offline-first for now. Bluetooth audio, AVRCP, and OBD-II all work without internet.

## Current Status
- [x] Bluetooth A2DP audio streaming working
- [x] AVRCP metadata verified via bluetoothctl
- [x] WirePlumber bluetooth.conf working
- [x] Auto-loopback service (`bt-loopback.service`) set up
- [x] Kivy hello-world verified on Mac
- [ ] Kivy home screen with clock
- [ ] AVRCP dbus → Kivy live track display
- [ ] Music screen (album art, progress bar, controls)
- [ ] Auto-boot Kivy app on Pi startup
- [ ] Auto-reconnect to iPhone on boot
- [ ] OBD-II integration (ELM327 + python-obd)

## Key Commands
```bash
ssh luisito@10.0.0.53
systemctl --user restart pipewire pipewire-pulse wireplumber
pw-top                          # verify bluez_input running at 44100Hz
bluetoothctl info A0:4E:CF:79:28:38
systemctl --user status bt-loopback
```

See `docs/carpi-docs.md` for full troubleshooting history, pairing steps, and audio config details.
