# CarPi

A DIY CarPlay-style head unit on a Raspberry Pi 4. Streams audio from an iPhone
over Bluetooth, shows live Spotify track info via AVRCP, and outputs sound through
the Pi's 3.5mm jack. UI built with Kivy in Python, styled after Spotify's dark theme.

## Stack

| Layer | Technology |
|---|---|
| Audio streaming | BlueZ + A2DP |
| Audio output | PipeWire + WirePlumber → 3.5mm jack |
| Track metadata | AVRCP via dbus (BlueZ MediaPlayer1) |
| UI | Kivy 2.3.1 (Python) |
| Future | OBD-II via ELM327 + python-obd |

## Hardware

- Raspberry Pi 4 (Bookworm OS, 64-bit)
- iPhone (Bluetooth audio source, Spotify)
- 3.5mm aux → car speakers / headphones
- Planned: 7–10" capacitive touchscreen

## Project Structure

```
Custom-Carplay/
├── main.py                  # app entry point, ScreenManager
├── car.kv                   # all Kivy layouts and styles
├── screens/
│   ├── home.py              # live clock screen
│   ├── music.py             # AVRCP track display + controls
│   └── map.py               # placeholder
├── services/
│   ├── bluetooth.py         # dbus AVRCP polling; mock fallback on non-Pi
│   ├── audio.py             # PipeWire loopback (future)
│   └── obd.py               # OBD-II (future)
├── assets/fonts/
├── assets/icons/
├── docs/carpi-docs.md       # full setup & troubleshooting history
├── requirements.txt         # kivy[full]==2.3.1
└── requirements-pi.txt      # + dbus-python (Pi only)
```

## Dev Setup

### Windows (conda)
```bash
conda activate voicebot2
pip install -r requirements.txt
python main.py
```

### Mac
```bash
# Python 3.12 required — 3.13+ not yet supported by Kivy
source carpi-env/bin/activate
pip install -r requirements.txt
python3.12 main.py
```

### Raspberry Pi (first time)
```bash
git clone https://github.com/luisitossb/Custom-Carplay.git
cd Custom-Carplay
python3 -m venv carpi-env && source carpi-env/bin/activate
sudo apt install libdbus-1-dev libglib2.0-dev pkg-config python3-dev
pip install -r requirements-pi.txt
```

Run from a **VNC terminal** (not SSH):
```bash
source carpi-env/bin/activate && python main.py
```

Pull updates after pushing from Windows:
```bash
git pull && python main.py
```

## Status

| Feature | Status |
|---|---|
| Bluetooth A2DP audio streaming | Working |
| PipeWire auto-loopback to 3.5mm | Working |
| Live AVRCP track info in UI | Working |
| Playback controls (prev/pause/next) | Working |
| Home screen with live clock | Working |
| VNC remote desktop | Working |
| Auto-boot on Pi startup | Set up |
| Car speaker wiring | Planned |
| OBD-II integration | Planned |

See [`docs/carpi-docs.md`](docs/carpi-docs.md) for full setup, audio config, and troubleshooting.
