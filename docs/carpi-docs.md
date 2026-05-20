# CarPi Project Documentation

## Project Overview

A custom Raspberry Pi 4 car head unit that:
- Receives Bluetooth audio from an iPhone (Spotify, calls, etc.)
- Outputs audio through the Pi's 3.5mm jack to car speakers
- Displays a custom riced Kivy UI (Tesla-style dashboard)
- Shows live track info, artist, album via AVRCP Bluetooth metadata
- Eventually shows OBD-II data (speed, RPM, temp)

**Hardware:**
- Raspberry Pi 4
- iPhone (Verizon — hotspot blocked at carrier level)
- Future: 7-10" capacitive touchscreen, car aux wiring

**Development machine:** MacBook Pro M2 (Python 3.12 via Homebrew)

---

## System Stack

```
iPhone (Spotify)
    │
    └── Bluetooth A2DP ──▶ Pi 4 (BlueZ + PipeWire + WirePlumber)
                                │
                                ├── AVRCP metadata ──▶ Kivy UI (track info, volume)
                                │
                                └── PipeWire loopback ──▶ 3.5mm jack ──▶ Car speakers
```

---

## Pi Setup

**OS:** Raspberry Pi OS (full, 64-bit, Bookworm/Debian 13)
**Hostname:** LuisitoPi
**Username:** luisito
**Local IP:** 10.0.0.53 (SSH access)

**Audio stack:**
- PipeWire 1.4.2
- WirePlumber 0.5.8
- pipewire-pulse (PulseAudio compatibility layer)
- libspa-0.2-bluetooth

---

## Bluetooth Setup

### iPhone MAC Address
```
A0:4E:CF:79:28:38
```

### Bluetooth service
Pi 4 has built-in Bluetooth. Was blocked by rfkill on first boot.

**Fix rfkill block:**
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
# pair from iPhone, then:
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
By default WirePlumber only advertised `audio-gateway` profile to iPhone,
meaning the Pi acted as a hands-free kit rather than a Bluetooth speaker.
iPhone would not offer A2DP streaming unless the Pi advertised `a2dp_sink`.

### Fix: WirePlumber config
WirePlumber 0.5.x reads config from `/etc/xdg/wireplumber/` NOT `/etc/wireplumber/`.
The correct config file path is:
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

> **Note:** `/etc/wireplumber/` and `/etc/pipewire/pipewire.conf.d/` were also
> tried but ignored by WirePlumber 0.5.8. Only `/etc/xdg/wireplumber/` works.

### Restart audio stack
```bash
systemctl --user restart pipewire pipewire-pulse wireplumber
```

### Verify Bluetooth audio is streaming
```bash
pw-top
# Look for: bluez_input.A0_4E_CF_79_28_38.2  running at 44100Hz
```

```bash
pactl list cards | grep -A 20 "bluez_card"
# Should show: bluez5.auto-connect = "[ a2dp_sink hfp_hf hsp_hs ]"
```

### Manual loopback (one-time)
```bash
pactl load-module module-loopback \
  source=bluez_input.A0_4E_CF_79_28_38.2 \
  sink=alsa_output.platform-fe00b840.mailbox.stereo-fallback \
  latency_msec=100
```

### Auto loopback on boot
Script at `~/autoloopback.sh` polls for the Bluetooth source and creates
the loopback automatically when iPhone connects.

**Service:** `~/.config/systemd/user/bt-loopback.service`
```bash
systemctl --user enable bt-loopback
systemctl --user start bt-loopback
systemctl --user status bt-loopback  # check it's running
```

---

## AVRCP Metadata (Track Info)

When iPhone connects and Spotify is playing, BlueZ exposes a Player object
with live track metadata. This is what powers the UI music display.

**Available data via AVRCP:**
- `Track.Title` — song name
- `Track.Artist` — artist
- `Track.Album` — album
- `Track.Duration` — total track length (milliseconds)
- `Player.Position` — current playback position (milliseconds)
- `Player.Status` — playing / paused / stopped
- `Transport.Volume` — live volume (0-127)

**Verified working in bluetoothctl — example output:**
```
[CHG] Player .../player0 Track.Title: Freakin' Out
[CHG] Player .../player0 Track.Artist: Dexter and The Moonrocks
[CHG] Player .../player0 Status: playing
[CHG] Transport .../fd0 Volume: 0x0067 (103)
```

**Reading this in Python** using `dbus`:
```python
import dbus

bus = dbus.SystemBus()
manager = dbus.Interface(
    bus.get_object("org.bluez", "/"),
    "org.freedesktop.DBus.ObjectManager"
)
objects = manager.GetManagedObjects()

for path, interfaces in objects.items():
    if "org.bluez.MediaPlayer1" in interfaces:
        player = interfaces["org.bluez.MediaPlayer1"]
        track = player.get("Track", {})
        print("Title:", track.get("Title"))
        print("Artist:", track.get("Artist"))
        print("Status:", player.get("Status"))
```

---

## Connectivity

### Internet on the Pi
Verizon blocks hotspot at the plan level — the Personal Hotspot toggle is
completely greyed out. The TTL trick (iptables TTL=65) cannot be applied
because hotspot can't be enabled at all.

**Options:**
1. Call Verizon and add hotspot to the plan (~$10/month)
2. USB tethering via EasyTether (~$10 one-time, bypasses carrier hotspot check)
3. Dedicated data SIM (Visible $25/month, runs on Verizon towers, includes hotspot)
4. Build offline-first (recommended for now)

**Offline-first is fine for:**
- Bluetooth audio ✓
- AVRCP track info ✓
- OBD-II data ✓
- Offline maps (Organic Maps) ✓

**Needs internet for:**
- Google Maps API (live traffic)
- Weather widgets
- Spotify API metadata fallback

---

## UI Development

### Mac development environment
```bash
brew install python@3.12
brew install pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer
python3.12 -m venv carpi-env
source carpi-env/bin/activate
pip install kivy
python3.12 main.py
```

> **Important:** Use Python 3.12 specifically. Python 3.14 (Homebrew default)
> is not supported by Kivy yet.

### Project structure
```
carpi/
├── main.py              # app entry point
├── car.kv               # Kivy layouts and styles
├── screens/
│   ├── home.py          # main dashboard
│   ├── music.py         # music / AVRCP screen
│   └── map.py           # navigation screen
├── services/
│   ├── bluetooth.py     # AVRCP metadata via dbus
│   ├── obd.py           # OBD-II data (future)
│   └── audio.py         # PipeWire loopback management
└── assets/
    ├── fonts/
    └── icons/
```

### Hello world verified working
```python
from kivy.app import App
from kivy.uix.label import Label

class CarApp(App):
    def build(self):
        return Label(text="car pi", font_size=72, color=(1,1,1,1))

if __name__ == "__main__":
    CarApp().run()
```

---

## Troubleshooting

### Bluetooth won't power on
```bash
rfkill list          # check if soft/hard blocked
sudo rfkill unblock bluetooth
bluetoothctl power on
```

### PipeWire not starting
```bash
systemctl --user status pipewire pipewire-pulse wireplumber
systemctl --user restart pipewire pipewire-pulse wireplumber
```

### No Bluetooth sink appearing in pactl
Check WirePlumber is reading the correct config:
```bash
WIREPLUMBER_DEBUG=3 wireplumber 2>&1 | head -30
# Look for: opening fragment file: /etc/xdg/wireplumber/...
# Should NOT say: section 'monitor.bluez.properties' is not defined
```

### Audio streaming but no sound
```bash
pw-top   # check bluez_input node is running (R status, not S)
# Then manually create loopback:
pactl load-module module-loopback \
  source=bluez_input.A0_4E_CF_79_28_38.2 \
  sink=alsa_output.platform-fe00b840.mailbox.stereo-fallback \
  latency_msec=100
```

### iPhone not showing Pi as audio output
1. Forget device on iPhone and remove on Pi (`bluetoothctl remove MAC`)
2. Reboot Pi
3. Re-pair fresh — iPhone negotiates A2DP correctly on first pairing
   when Pi is already advertising `a2dp_sink`

### WirePlumber config not taking effect
Config priority order (highest to lowest):
```
~/.config/wireplumber/wireplumber.conf.d/   # user
/etc/xdg/wireplumber/wireplumber.conf.d/    # system (THIS IS THE ONE THAT WORKS)
/usr/share/wireplumber/wireplumber.conf.d/  # stock defaults
```
`/etc/wireplumber/` is NOT read by WirePlumber 0.5.x on this system.

---

## Next Steps

- [ ] Build Kivy home screen with clock and basic layout
- [ ] Hook AVRCP dbus events into Kivy UI (live track display)
- [ ] Add play/pause/skip controls via AVRCP
- [ ] Wire Pi 3.5mm to car aux input
- [ ] Set up auto-boot: Pi launches Kivy app on startup
- [ ] Set up auto-pair: Pi reconnects to iPhone on boot automatically
- [ ] Add OBD-II reader (ELM327 Bluetooth adapter + python-obd)
- [ ] Design music screen with album art and progress bar
- [ ] Solve internet connectivity (Verizon hotspot or dedicated SIM)
- [ ] Add Google Maps API integration once internet is solved

---

## Useful Commands Reference

```bash
# SSH into Pi
ssh luisito@10.0.0.53

# Check Bluetooth status
bluetoothctl show
bluetoothctl devices
bluetoothctl info A0:4E:CF:79:28:38

# Check audio
pactl list cards short
pactl list sinks short
pactl list sources short
pw-top

# Restart everything
systemctl --user restart pipewire pipewire-pulse wireplumber

# Check loopback service
systemctl --user status bt-loopback
journalctl --user -u bt-loopback -f

# Run Kivy app (Mac)
source carpi-env/bin/activate
python3.12 main.py
```
