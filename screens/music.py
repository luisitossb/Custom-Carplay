from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from services.bluetooth import get_track, send_play, send_pause, send_next, send_previous


def _ms_to_mmss(ms):
    s = int(ms / 1000)
    return f"{s // 60}:{s % 60:02d}"


class MusicScreen(Screen):
    def on_enter(self):
        self._tick = Clock.schedule_interval(self._update, 1)
        self._update(0)

    def on_leave(self):
        self._tick.cancel()

    def _update(self, dt):
        info = get_track()
        self.ids.title_label.text = info["title"]
        self.ids.artist_label.text = info["artist"]
        self.ids.album_label.text = info["album"]
        self.ids.playpause_btn.text = "||" if info["status"] == "playing" else ">"

        position = info.get("position", 0)
        duration = info.get("duration", 0)

        self.ids.time_current.text = _ms_to_mmss(position)
        self.ids.time_total.text = _ms_to_mmss(duration)
        self.ids.progress_fill.size_hint_x = (position / duration) if duration > 0 else 0

    def on_playpause(self):
        info = get_track()
        if info["status"] == "playing":
            send_pause()
        else:
            send_play()
        self._quick_refresh()

    def on_next(self):
        send_next()
        self._quick_refresh()

    def on_previous(self):
        send_previous()
        self._quick_refresh()

    def _quick_refresh(self):
        # AVRCP metadata takes a few seconds to come back from the iPhone.
        # Poll aggressively after a control action to catch it as soon as it arrives.
        for delay in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
            Clock.schedule_once(self._update, delay)
