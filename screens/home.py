from datetime import datetime
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock


class HomeScreen(Screen):
    def on_enter(self):
        self._tick = Clock.schedule_interval(self._update_clock, 1)
        self._update_clock(0)

    def on_leave(self):
        self._tick.cancel()

    def _update_clock(self, dt):
        now = datetime.now()
        self.ids.time_label.text = now.strftime("%I:%M")
        self.ids.ampm_label.text = now.strftime("%p")
        self.ids.date_label.text = now.strftime("%A, %B ") + str(now.day)
