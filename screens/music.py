from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from services.bluetooth import get_track, send_play, send_pause, send_next, send_previous, get_volume, set_volume


def _ms_to_mmss(ms):
    s = int(ms / 1000)
    return f"{s // 60}:{s % 60:02d}"


class MusicScreen(Screen):
    def on_enter(self):
        self._last_position = 0
        self._frozen_position = None
        self._volume = None
        self._tick = Clock.schedule_interval(self._update, 0.5)
        self._update(0)

    def on_leave(self):
        self._tick.cancel()

    def _update(self, dt):
        info = get_track()
        self.ids.title_label.text = info["title"]
        self.ids.artist_label.text = info["artist"]
        self.ids.album_label.text = info["album"]

        playing = info["status"] == "playing"
        self.ids.playpause_icon.source = 'assets/icons/pause.png' if playing else 'assets/icons/play.png'

        position = info.get("position", 0)
        duration = info.get("duration", 0)

        if not playing:
            if self._frozen_position is None:
                # Just paused — freeze the display here
                self._frozen_position = self._last_position
            elif abs(position - self._frozen_position) > 5000:
                # Seeked while paused — accept the new position
                self._frozen_position = position
            position = self._frozen_position
        else:
            self._frozen_position = None
            # Detect seek/restart: position jumped back by more than 2 seconds
            if self._last_position - position > 2000:
                self._last_position = position
                self._quick_refresh()

        self._last_position = position
        self.ids.time_current.text = _ms_to_mmss(position)
        self.ids.time_total.text = _ms_to_mmss(duration)
        self.ids.progress_fill.size_hint_x = (position / duration) if duration > 0 else 0

        vol = get_volume()
        if vol is not None:
            self._volume = vol
        if self._volume is not None:
            self.ids.volume_label.text = f'{self._volume}%'
            self.ids.volume_fill.size_hint_x = self._volume / 100

    def on_playpause(self):
        info = get_track()
        if info["status"] == "playing":
            send_pause()
        else:
            send_play()
        self._quick_refresh()

    def on_next(self):
        send_next()
        self._last_position = 0
        self._frozen_position = None
        self._update(0)
        self._quick_refresh()

    def on_previous(self):
        send_previous()
        self._last_position = 0
        self._frozen_position = None
        self._update(0)
        self._quick_refresh()

    def on_volume_up(self):
        self._volume = min(100, (self._volume or 50) + 10)
        set_volume(self._volume)
        self.ids.volume_label.text = f'{self._volume}%'
        self.ids.volume_fill.size_hint_x = self._volume / 100

    def on_volume_down(self):
        self._volume = max(0, (self._volume or 50) - 10)
        set_volume(self._volume)
        self.ids.volume_label.text = f'{self._volume}%'
        self.ids.volume_fill.size_hint_x = self._volume / 100

    def _quick_refresh(self):
        for delay in (0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
            Clock.schedule_once(self._update, delay)
