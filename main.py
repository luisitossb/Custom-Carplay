from kivy.app import App
from kivy.lang import Builder

Builder.load_file("car.kv")


class CarApp(App):
    def build(self):
        pass


if __name__ == "__main__":
    CarApp().run()
