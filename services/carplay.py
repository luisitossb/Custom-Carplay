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


def get_track():
    with _lock:
        return dict(_state)


def get_albumart():
    with _lock:
        return _state.get('albumart')


def is_connected():
    with _lock:
        return _state['connected']


def _merge_media(data):
    name = data.get('MediaSongName')
    artist = data.get('MediaArtistName')
    album = data.get('MediaAlbumName')
    duration = data.get('MediaSongDuration')
    position = data.get('MediaSongPlayTime')
    status_val = data.get('MediaPlayStatus')

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
    with _lock:
        _state['connected'] = False


def _run_ws():
    while True:
        try:
            ws = websocket.WebSocketApp(
                'ws://localhost:4000',
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
