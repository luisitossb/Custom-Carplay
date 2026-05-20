from kivy.config import Config
Config.set('graphics', 'vsync', '0')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.clock import Clock

from screens.home import HomeScreen
from screens.music import MusicScreen
from screens.map import MapScreen
from services.bluetooth import get_battery, is_connected


class StatusBar(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 28
        self.padding = [20, 0]
        self.spacing = 8

        self._bt_label = Label(
            text='', font_size='12sp',
            size_hint_x=None, width=52,
            halign='left', valign='middle',
        )
        self._bt_label.bind(size=self._bt_label.setter('text_size'))

        self._bat_label = Label(
            text='', font_size='12sp',
            size_hint_x=None, width=52,
            halign='right', valign='middle',
        )
        self._bat_label.bind(size=self._bat_label.setter('text_size'))

        self.add_widget(self._bt_label)
        self.add_widget(Widget())
        self.add_widget(self._bat_label)

        with self.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0.05, 0.05, 0.05, 1)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

        Clock.schedule_interval(self._refresh, 30)
        self._refresh(0)

    def _update_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _refresh(self, dt):
        connected = is_connected()
        self._bt_label.text = '● BT' if connected else '○ BT'
        self._bt_label.color = (0.114, 0.725, 0.329, 1) if connected else (0.35, 0.35, 0.35, 1)

        pct = get_battery()
        if pct is not None:
            if pct > 20:
                color = (0.6, 0.6, 0.6, 1)
            else:
                color = (0.9, 0.3, 0.3, 1)  # red when low
            self._bat_label.color = color
            self._bat_label.text = f'{pct}%'
        else:
            self._bat_label.text = ''


class CarApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical')
        root.add_widget(StatusBar())

        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(MusicScreen(name="music"))
        sm.add_widget(MapScreen(name="map"))
        root.add_widget(sm)

        return root


if __name__ == "__main__":
    CarApp().run()
