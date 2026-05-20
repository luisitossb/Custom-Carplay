# CarPi

A custom Raspberry Pi 4 car head unit — a DIY CarPlay-style dashboard.

Streams Bluetooth audio from an iPhone, displays live track info via AVRCP, and will eventually show OBD-II vehicle data. UI built with [Kivy](https://kivy.org/) in Python.

## Stack

| Layer | Technology |
|---|---|
| Audio | BlueZ + PipeWire + WirePlumber |
| Metadata | AVRCP via dbus |
| UI | Kivy (Python) |
| Future | OBD-II (ELM327 + python-obd) |

## Hardware

- Raspberry Pi 4
- iPhone (Bluetooth source)
- 3.5mm aux → car speakers
- Planned: 7–10" capacitive touchscreen

## Project Structure

```
carpi/
├── main.py              # app entry point
├── car.kv               # Kivy layouts
├── screens/
│   ├── home.py          # main dashboard
│   ├── music.py         # music / AVRCP screen
│   └── map.py           # navigation screen
├── services/
│   ├── bluetooth.py     # AVRCP metadata via dbus
│   ├── audio.py         # PipeWire loopback
│   └── obd.py           # OBD-II (future)
├── assets/
│   ├── fonts/
│   └── icons/
└── docs/
    └── carpi-docs.md    # full setup & troubleshooting history
```

## Dev Setup (Mac/Windows)

```bash
# Python 3.11 or 3.12 required (3.13+ not yet supported by Kivy)
python3.11 -m venv carpi-env
source carpi-env/bin/activate   # Mac/Linux
# carpi-env\Scripts\activate    # Windows

pip install kivy[full]
python main.py
```

## Status

- [x] Bluetooth A2DP audio streaming
- [x] AVRCP metadata verified
- [x] PipeWire auto-loopback to 3.5mm
- [ ] Kivy home screen with clock
- [ ] Live AVRCP track display in UI
- [ ] Music screen (album art, controls)
- [ ] Auto-boot on Pi startup
- [ ] OBD-II integration
