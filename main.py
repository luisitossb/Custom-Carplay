from kivy.config import Config
Config.set('graphics', 'window_state', 'maximized')
Config.set('graphics', 'maxfps', '30')

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager

from screens.home import HomeScreen
from screens.music import MusicScreen
from screens.map import MapScreen


class CarApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(MusicScreen(name="music"))
        sm.add_widget(MapScreen(name="map"))
        return sm


if __name__ == "__main__":
    CarApp().run()
