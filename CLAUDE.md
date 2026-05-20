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

## Pi Deploy Workflow
```bash
# First time
ssh luisito@10.0.0.53
cd ~/Desktop && git clone https://github.com/luisitossb/Custom-Carplay.git
cd Custom-Carplay && python3 -m venv carpi-env && source carpi-env/bin/activate
sudo apt install libdbus-1-dev libglib2.0-dev pkg-config python3-dev
pip install -r requirements-pi.txt

# Pull updates (from VNC terminal)
cd ~/Desktop/Custom-Carplay && git pull && source carpi-env/bin/activate && python main.py
```
> Always run from a VNC terminal, NOT SSH. SSH has no display.

## Current Status
- [x] Bluetooth A2DP audio streaming working
- [x] AVRCP metadata verified (title, artist, album, status, position, duration)
- [x] WirePlumber bluetooth.conf working
- [x] Auto-loopback service (`bt-loopback.service`) — use `latency_msec=30` (not 100, causes echo)
- [x] Kivy home screen with live clock (Spotify dark theme, #121212 / #1DB954)
- [x] Music screen — track info, progress bar, prev/play-pause/next
- [x] VNC remote desktop (X11 mode, 1024x600)
- [x] Auto-boot Kivy app on Pi startup (`scripts/setup-autostart.sh`)
- [x] iPhone BT reconnect attempt on boot (`scripts/start.sh`)
- [ ] Car speaker wiring (Metra harness + 4-ch amp + ground loop isolator)
- [ ] Album art (needs Spotify Web API or Carlinkit dongle)
- [ ] Playlist browsing (same as above)
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
