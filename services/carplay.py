import json
import threading
import time

try:
    import websocket
    _WS_AVAILABLE = True
except ImportError:
    _WS_AVAILABLE = False

_DEFAULT = {
    'title': '---',
    'artist': '---',
    'album': '',
    'status': 'stopped',
    'position': 0,
    'duration': 0,
    'albumart': None,
    'connected': False,
}

_state = dict(_DEFAULT)
_lock = threading.Lock()
_ws_thread = None
_ws = None          # live WebSocket connection for sending commands
_ws_lock = threading.Lock()


def get_track():
    with _lock:
        return dict(_state)


def get_albumart():
    with _lock:
        return _state.get('albumart')


def is_connected():
    with _lock:
        return _state['connected']


def send_key(action):
    """Send a playback command to the dongle via the node bridge.
    Valid actions: 'play', 'pause', 'next', 'prev'
    """
    with _ws_lock:
        if _ws:
            try:
                _ws.send(json.dumps({'type': 'key', 'action': action}))
            except Exception:
                pass


def _merge_media(data):
    # MediaLyrics is the field the dongle uses for song title on song changes;
    # MediaSongName only appears in the initial connection burst.
    name = data.get('MediaLyrics') or data.get('MediaSongName')
    artist = data.get('MediaArtistName')
    album = data.get('MediaAlbumName')
    duration = data.get('MediaSongDuration')
    position = data.get('MediaSongPlayTime')
    status_val = data.get('MediaPlayStatus')

    # Detect song change: artist changed OR duration changed by more than 2 seconds.
    # Clear stale identity so the UI shows --- during the brief transition.
    artist_changed = artist and artist != _state['artist']
    duration_changed = (duration is not None and _state['duration'] > 0 and
                        abs(duration - _state['duration']) > 2000)
    if artist_changed or duration_changed:
        _state['title'] = '---'
        _state['album'] = ''
        _state['duration'] = 0

    if name:
        _state['title'] = name
    if artist:
        _state['artist'] = artist
    if album:
        _state['album'] = album
    if duration:
        _state['duration'] = duration
    if position is not None:
        _state['position'] = position
    if status_val is not None:
        _state['status'] = 'playing' if status_val == 1 else 'paused' if status_val == 2 else 'stopped'


def _on_open(ws):
    global _ws
    with _ws_lock:
        _ws = ws


def _on_message(ws, raw):
    try:
        msg = json.loads(raw)
        with _lock:
            t = msg.get('type')
            if t == 'plugged':
                _state['connected'] = True
            elif t == 'unplugged':
                _state.update(_DEFAULT)
            elif t == 'media':
                _merge_media(msg.get('data', {}))
            elif t == 'albumart':
                _state['albumart'] = msg.get('data')
    except Exception:
        pass


def _on_close(ws, *args):
    global _ws
    with _ws_lock:
        _ws = None
    with _lock:
        _state['connected'] = False


def _run_ws():
    while True:
        try:
            ws = websocket.WebSocketApp(
                'ws://localhost:4000',
                on_open=_on_open,
                on_message=_on_message,
                on_close=_on_close,
            )
            ws.run_forever()
        except Exception:
            pass
        time.sleep(3)


def start():
    global _ws_thread
    if not _WS_AVAILABLE:
        return
    if _ws_thread is None or not _ws_thread.is_alive():
        _ws_thread = threading.Thread(target=_run_ws, daemon=True)
        _ws_thread.start()
