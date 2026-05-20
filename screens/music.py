from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from services.bluetooth import get_track, send_play, send_pause, send_next, send_previous


class MusicScreen(Screen):
    def on_enter(self):
        self._tick = Clock.schedule_interval(self._update, 2)
        self._update(0)

    def on_leave(self):
        self._tick.cancel()

    def _update(self, dt):
        info = get_track()
        self.ids.title_label.text = info["title"]
        self.ids.artist_label.text = info["artist"]
        self.ids.album_label.text = info["album"]
        self.ids.playpause_btn.text = "||" if info["status"] == "playing" else ">"

    def on_playpause(self):
        info = get_track()
        if info["status"] == "playing":
            send_pause()
        else:
            send_play()
        self._update(0)

    def on_next(self):
        send_next()
        self._update(0)

    def on_previous(self):
        send_previous()
        self._update(0)
