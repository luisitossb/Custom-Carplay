try:
    import dbus
    _DBUS_AVAILABLE = True
except ImportError:
    _DBUS_AVAILABLE = False

_MOCK_TRACKS = [
    {"title": "Freakin' Out", "artist": "Dexter and The Moonrocks", "album": "Space Hits", "status": "playing"},
    {"title": "Blinding Lights", "artist": "The Weeknd", "album": "After Hours", "status": "playing"},
    {"title": "Redbone", "artist": "Childish Gambino", "album": "Awaken, My Love!", "status": "paused"},
]
_mock_index = 0


def get_track():
    if _DBUS_AVAILABLE:
        return _dbus_get_track()
    return _MOCK_TRACKS[_mock_index % len(_MOCK_TRACKS)]


def send_play():
    _dbus_player_command("Play")


def send_pause():
    _dbus_player_command("Pause")


def send_next():
    global _mock_index
    _mock_index += 1
    _dbus_player_command("Next")


def send_previous():
    global _mock_index
    _mock_index = max(0, _mock_index - 1)
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
                }
        return {"title": "No device", "artist": "Connect iPhone via Bluetooth", "album": "", "status": "stopped"}
    except Exception:
        return {"title": "No device", "artist": "Connect iPhone via Bluetooth", "album": "", "status": "stopped"}


def _dbus_player_command(command):
    if not _DBUS_AVAILABLE:
        return
    try:
        player = _get_player_interface()
        if player:
            getattr(player, command)()
    except Exception:
        pass
