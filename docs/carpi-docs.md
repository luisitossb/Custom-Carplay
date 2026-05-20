# CarPi — Full Setup & Troubleshooting Guide

A custom Raspberry Pi 4 car head unit. Streams Bluetooth audio from an iPhone,
displays live AVRCP track info in a Kivy UI, and outputs audio through the Pi's
3.5mm jack to car speakers.

---

## System Stack

```
iPhone (Spotify)
    │
    └── Bluetooth A2DP ──▶ Pi 4 (BlueZ + PipeWire + WirePlumber)
                                │
                                ├── AVRCP metadata ──▶ dbus ──▶ Kivy UI
                                │
                                └── PipeWire loopback ──▶ 3.5mm jack ──▶ speakers
```

---

## Hardware

| Component | Detail |
|---|---|
| Pi | Raspberry Pi 4 |
| OS | Raspberry Pi OS 64-bit (Bookworm / Debian 13) |
| Hostname | LuisitoPi |
| Username | luisito |
| Local IP | 10.0.0.53 |
| Audio out | Pi 3.5mm jack → car aux / headphones |
| Phone | iPhone (Verizon — hotspot blocked at carrier level) |
| Planned | 7–10" capacitive touchscreen |

---

## Pi Setup

### SSH access
```bash
ssh luisito@10.0.0.53
```

### VNC (remote desktop to Pi from Windows/Mac)
```bash
sudo systemctl enable vncserver-x11-serviced
sudo systemctl start vncserver-x11-serviced
```
Then connect with **RealVNC Viewer** (free) on Windows/Mac to `10.0.0.53`.

**Set VNC resolution** (run once, then reboot):
```bash
sudo raspi-config nonint do_vnc_resolution 1024x600
```
1024x600 matches most 7" touchscreens and runs smoothly on the Pi.

**Check current VNC resolution:**
```bash
sudo raspi-config nonint get_vnc_resolution
```

> **Important:** Always run the Kivy app from a terminal inside the VNC session,
> not from SSH. SSH has no display — the app will fail with "Unable to connect
> to X server" when launched over SSH.

---

## Bluetooth Setup

### iPhone MAC address
```
A0:4E:CF:79:28:38
```

### First-time rfkill fix (if Bluetooth won't power on)
```bash
sudo rfkill unblock bluetooth
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### Pairing
```bash
bluetoothctl
power on
agent on
default-agent
discoverable on
pairable on
# Pair from iPhone, then:
trust A0:4E:CF:79:28:38
exit
```

### Key UUIDs confirmed on iPhone connection
- `0000110a` — Audio Source (A2DP)
- `0000110d` — Advanced Audio Distribution
- `0000110e` — A/V Remote Control (AVRCP)
- `0000111f` — Handsfree Audio Gateway (HFP)

---

## Audio Configuration

### The core problem
By default WirePlumber only advertised `audio-gateway` to the iPhone, making
the Pi act as a hands-free kit rather than a Bluetooth speaker. The iPhone
won't offer A2DP streaming unless the Pi advertises `a2dp_sink`.

### Critical: WirePlumber config path
WirePlumber 0.5.x reads from `/etc/xdg/wireplumber/` — **NOT** `/etc/wireplumber/`.
Both `/etc/wireplumber/` and `/etc/pipewire/pipewire.conf.d/` are silently ignored.

**Correct file:**
```
/etc/xdg/wireplumber/wireplumber.conf.d/bluetooth.conf
```

**Contents:**
```
monitor.bluez.properties = {
  bluez5.roles = [ a2dp_sink a2dp_source hsp_hs hsp_ag hfp_hf hfp_ag ]
  bluez5.codecs = [ sbc sbc_xq aac ]
  bluez5.enable-sbc-xq = true
  bluez5.dummy-avrcp-player = true
}

monitor.bluez.rules = [
  {
    matches = [ { device.name = "~bluez_card.*" } ]
    actions = {
      update-props = {
        bluez5.auto-connect = [ a2dp_sink hfp_hf hsp_hs ]
      }
    }
  }
]
```

### Restart audio stack
```bash
systemctl --user restart pipewire pipewire-pulse wireplumber
```

### Verify Bluetooth audio is streaming
```bash
pw-top
# Look for: bluez_input.A0_4E_CF_79_28_38.2  running at 44100Hz
```

### Manual loopback (one-time test)
```bash
pactl load-module module-loopback \
  source=bluez_input.A0_4E_CF_79_28_38.2 \
  sink=alsa_output.platform-fe00b840.mailbox.stereo-fallback \
  latency_msec=30
```
> **Note:** Use `latency_msec=30` not 100. 100ms causes an audible echo/hollow
> sound. 30ms is clean. Update `~/autoloopback.sh` to match if re-creating.

### Auto loopback on boot
Script at `~/autoloopback.sh` polls for the BT source and creates the loopback
when the iPhone connects. Service: `~/.config/systemd/user/bt-loopback.service`
```bash
systemctl --user enable bt-loopback
systemctl --user start bt-loopback
systemctl --user status bt-loopback
```

---

## AVRCP Metadata (Track Info)

When iPhone connects and Spotify is playing, BlueZ exposes a MediaPlayer1
D-Bus object with live track metadata.

**Available fields:**
- `Track.Title`, `Track.Artist`, `Track.Album`
- `Track.Duration` — total length (ms)
- `Player.Position` — current position (ms)
- `Player.Status` — playing / paused / stopped
- `Transport.Volume` — 0–127

**Verified working — example bluetoothctl output:**
```
[CHG] Player .../player0 Track.Title: Freakin' Out
[CHG] Player .../player0 Track.Artist: Dexter and The Moonrocks
[CHG] Player .../player0 Status: playing
[CHG] Transport .../fd0 Volume: 0x0067 (103)
```

---

## Kivy App

### Project structure
```
Custom-Carplay/
├── main.py              # app entry point, ScreenManager
├── car.kv               # all Kivy layouts (auto-loaded by CarApp)
├── screens/
│   ├── home.py          # live clock, ticks every second
│   ├── music.py         # AVRCP track display + prev/play-pause/next
│   └── map.py           # placeholder
├── services/
│   ├── bluetooth.py     # dbus AVRCP polling; mock fallback on non-Pi
│   ├── audio.py         # PipeWire loopback (future)
│   └── obd.py           # OBD-II (future)
├── assets/fonts/
├── assets/icons/
├── docs/carpi-docs.md
├── requirements.txt         # kivy[full]==2.3.1
└── requirements-pi.txt      # adds dbus-python (Pi only)
```

### Cross-platform dev (how bluetooth.py handles Windows vs Pi)
`services/bluetooth.py` attempts `import dbus` at startup. If it fails
(Windows has no dbus), `_DBUS_AVAILABLE = False` and the service returns
rotating mock tracks so the UI can be built without a Pi. On the Pi it
polls the real BlueZ MediaPlayer1 object every 2 seconds.

---

## Dev Environment Setup

### Windows (development)
Uses the `voicebot2` conda environment (Python 3.11.14, Kivy 2.3.1).
```bash
conda activate voicebot2
pip install -r requirements.txt
python main.py
```

### Mac (development)
Python 3.12 via Homebrew (3.13+ not yet supported by Kivy).
```bash
source carpi-env/bin/activate
pip install -r requirements.txt
python3.12 main.py
```

### Pi — first-time setup
```bash
ssh luisito@10.0.0.53
cd ~/Desktop
git clone https://github.com/luisitossb/Custom-Carplay.git
cd Custom-Carplay
python3 -m venv carpi-env
source carpi-env/bin/activate
sudo apt install libdbus-1-dev libglib2.0-dev pkg-config python3-dev
pip install -r requirements-pi.txt
```

### Pi — running the app
Open a terminal **inside the VNC session** (not SSH):
```bash
cd ~/Desktop/Custom-Carplay
source carpi-env/bin/activate
python main.py
```

### Pi — pulling updates after a Windows push
```bash
cd ~/Desktop/Custom-Carplay
git pull
source carpi-env/bin/activate
python main.py
```

---

## Connectivity

Verizon blocks hotspot at the plan level — toggle is greyed out. Offline-first.

**Options if internet is ever needed:**
1. Call Verizon and add hotspot (~$10/month)
2. USB tethering via EasyTether (~$10 one-time, bypasses carrier check)
3. Dedicated SIM — Visible $25/month (Verizon towers, includes hotspot)

**Works perfectly offline:** Bluetooth audio, AVRCP track info, OBD-II.

---

## Troubleshooting

### Bluetooth won't power on
```bash
rfkill list
sudo rfkill unblock bluetooth
bluetoothctl power on
```

### PipeWire not starting
```bash
systemctl --user status pipewire pipewire-pulse wireplumber
systemctl --user restart pipewire pipewire-pulse wireplumber
```

### No Bluetooth sink in pactl
```bash
WIREPLUMBER_DEBUG=3 wireplumber 2>&1 | head -30
# Look for: opening fragment file: /etc/xdg/wireplumber/...
# Bad: section 'monitor.bluez.properties' is not defined
```

### Audio streaming but no sound from 3.5mm
```bash
pw-top   # bluez_input node should be R (running), not S (suspended)
# If suspended, create loopback manually:
pactl load-module module-loopback \
  source=bluez_input.A0_4E_CF_79_28_38.2 \
  sink=alsa_output.platform-fe00b840.mailbox.stereo-fallback \
  latency_msec=100
```

### iPhone not showing Pi as audio output
1. Forget device on iPhone and remove on Pi: `bluetoothctl remove A0:4E:CF:79:28:38`
2. Reboot Pi
3. Re-pair fresh

### Music screen shows mock data instead of real track
`dbus-python` not installed in the venv:
```bash
sudo apt install libdbus-1-dev libglib2.0-dev pkg-config python3-dev
source ~/Desktop/Custom-Carplay/carpi-env/bin/activate
pip install dbus-python
```

### "Unable to connect to X server" when running the app
Launched from SSH — run from a terminal inside the VNC desktop instead.

### VNC shows "cannot currently show desktop"
Raspberry Pi OS Bookworm defaults to Wayland which RealVNC doesn't support.
Switch to X11:
```bash
sudo raspi-config nonint do_wayland W1 && sudo reboot
```

### VNC desktop appears as a tiny corner / mostly black screen
Overscan/underscan was enabled. Reset it:
```bash
sudo raspi-config nonint do_overscan 1
sudo raspi-config nonint do_vnc_resolution 1024x600
sudo reboot
```
If still broken, nuke all overscan settings from config:
```bash
sudo sed -i '/^overscan/d' /boot/firmware/config.txt && sudo reboot
```

### Audio sounds echoey or hollow through 3.5mm
The PipeWire loopback `latency_msec` is too high. Reload with 30ms:
```bash
pactl unload-module module-loopback
pactl load-module module-loopback \
  source=bluez_input.A0_4E_CF_79_28_38.2 \
  sink=alsa_output.platform-fe00b840.mailbox.stereo-fallback \
  latency_msec=30
```
Also update `~/autoloopback.sh` to use `latency_msec=30` permanently.

### Ground loop hum when connected to car speakers
A ground loop isolator inline between the Pi 3.5mm and the amp input fixes
this. Common when Pi and car amp share the same chassis ground.

### WirePlumber config not taking effect
```
~/.config/wireplumber/wireplumber.conf.d/   # user-level
/etc/xdg/wireplumber/wireplumber.conf.d/    # system-level ← THIS WORKS
/usr/share/wireplumber/wireplumber.conf.d/  # stock defaults
```
`/etc/wireplumber/` is NOT read by WirePlumber 0.5.x.

---

## Current Status

| Feature | Status |
|---|---|
| Bluetooth A2DP audio streaming | Working |
| WirePlumber bluetooth.conf | Working |
| PipeWire auto-loopback to 3.5mm (latency_msec=30) | Working |
| Clean audio — no echo through 3.5mm | Working |
| AVRCP metadata (title/artist/album/status) | Working |
| AVRCP track position + duration (progress bar) | Working |
| Playback controls (prev/play-pause/next) | Working |
| Kivy home screen with live clock | Working |
| Kivy music screen — Spotify dark theme | Working |
| Kivy fullscreen + maximized window | Working |
| VNC remote desktop (X11, 1024x600) | Working |
| Auto-boot Kivy on Pi startup | Working |
| iPhone BT reconnect attempt on boot | Working |
| Car speaker wiring | Planned |
| Album art (needs Spotify API / dongle) | Planned |
| Playlist browsing | Planned |
| OBD-II integration | Planned |

---

## Future Ideas

- **Car audio:** 3.5mm → car aux is the simplest path. No aux? FM transmitter
  or a Bluetooth-to-aux adapter plugged into the car stereo.
- **Progress bar:** Poll `Player.Position` + `Track.Duration` via AVRCP every second.
- **Volume control:** `Transport.Volume` is readable and writable over AVRCP.
- **OBD-II:** ELM327 Bluetooth adapter + `python-obd` library.
- **Touchscreen:** Most 7" Pi DSI screens are plug-and-play on Bookworm.
  Set `KIVY_BCM_DISPMANX_ID=4` if Kivy doesn't detect the display.
- **Performance:** Strip `kivy[full]` extras on Pi, remove unused providers.
- **Auto-pair:** `bluetoothctl` trust + connect in a boot script.

---

## Useful Commands Reference

```bash
# SSH
ssh luisito@10.0.0.53

# Bluetooth
bluetoothctl show
bluetoothctl info A0:4E:CF:79:28:38

# Audio
pactl list cards short && pw-top
systemctl --user restart pipewire pipewire-pulse wireplumber
systemctl --user status bt-loopback

# Run app (from VNC terminal)
cd ~/Desktop/Custom-Carplay && source carpi-env/bin/activate && python main.py

# Pull latest code on Pi
cd ~/Desktop/Custom-Carplay && git pull
```
