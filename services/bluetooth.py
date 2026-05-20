import time

try:
    import dbus
    _DBUS_AVAILABLE = True
except ImportError:
    _DBUS_AVAILABLE = False

_MOCK_TRACKS = [
    {"title": "Freakin' Out", "artist": "Dexter and The Moonrocks", "album": "Space Hits", "status": "playing", "duration": 214000},
    {"title": "Blinding Lights", "artist": "The Weeknd", "album": "After Hours", "status": "playing", "duration": 200000},
    {"title": "Redbone", "artist": "Childish Gambino", "album": "Awaken, My Love!", "status": "paused", "duration": 326000},
]
_mock_index = 0
_mock_start = time.time()


def get_track():
    if _DBUS_AVAILABLE:
        return _dbus_get_track()
    track = _MOCK_TRACKS[_mock_index % len(_MOCK_TRACKS)]
    elapsed = int((time.time() - _mock_start) * 1000) % track["duration"]
    return {**track, "position": elapsed}


def send_play():
    _dbus_player_command("Play")


def send_pause():
    _dbus_player_command("Pause")


def send_next():
    global _mock_index, _mock_start
    _mock_index += 1
    _mock_start = time.time()
    _dbus_player_command("Next")


def send_previous():
    global _mock_index, _mock_start
    _mock_index = max(0, _mock_index - 1)
    _mock_start = time.time()
    _dbus_player_command("Previous")


def _get_player_interface():
    bus = dbus.SystemBus()
    manager = dbus.Interface(
        bus.get_object("org.bluez", "/"),
        "org.freedesktop.DBus.ObjectManager",
    )
    for path, interfaces in manager.GetManagedObjects().items():
        if "org.bluez.MediaPlayer1" in interfaces:
            return dbus.Interface(
                bus.get_object("org.bluez", path),
                "org.bluez.MediaPlayer1",
            )
    return None


def _dbus_get_track():
    try:
        bus = dbus.SystemBus()
        manager = dbus.Interface(
            bus.get_object("org.bluez", "/"),
            "org.freedesktop.DBus.ObjectManager",
        )
        for path, interfaces in manager.GetManagedObjects().items():
            if "org.bluez.MediaPlayer1" in interfaces:
                player = interfaces["org.bluez.MediaPlayer1"]
                track = player.get("Track", {})
                return {
                    "title": str(track.get("Title", "Unknown")),
                    "artist": str(track.get("Artist", "Unknown")),
                    "album": str(track.get("Album", "")),
                    "status": str(player.get("Status", "stopped")),
                    "position": int(player.get("Position", 0)),
                    "duration": int(track.get("Duration", 0)),
                }
        return {"title": "No device", "artist": "Connect iPhone via Bluetooth", "album": "", "status": "stopped", "position": 0, "duration": 0}
    except Exception:
        return {"title": "No device", "artist": "Connect iPhone via Bluetooth", "album": "", "status": "stopped", "position": 0, "duration": 0}


_IPHONE_MAC = "A0:4E:CF:79:28:38"


def get_battery():
    if not _DBUS_AVAILABLE:
        return 72  # mock
    try:
        bus = dbus.SystemBus()
        path = "/org/bluez/hci0/dev_" + _IPHONE_MAC.replace(":", "_")
        obj = bus.get_object("org.bluez", path)
        props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
        return int(props.Get("org.bluez.Battery1", "Percentage"))
    except Exception:
        return None


def is_connected():
    if not _DBUS_AVAILABLE:
        return True  # mock
    try:
        bus = dbus.SystemBus()
        path = "/org/bluez/hci0/dev_" + _IPHONE_MAC.replace(":", "_")
        obj = bus.get_object("org.bluez", path)
        props = dbus.Interface(obj, "org.freedesktop.DBus.Properties")
        return bool(props.Get("org.bluez.Device1", "Connected"))
    except Exception:
        return False


def _dbus_player_command(command):
    if not _DBUS_AVAILABLE:
        return
    try:
        player = _get_player_interface()
        if player:
            getattr(player, command)()
    except Exception:
        pass
