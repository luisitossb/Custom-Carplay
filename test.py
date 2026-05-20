from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle


def make_screen(name, app):
    screen = Screen(name=name)
    with screen.canvas.before:
        Color(0.071, 0.071, 0.071, 1)
        rect = Rectangle(pos=screen.pos, size=screen.size)
    screen.bind(pos=lambda s, v: setattr(rect, 'pos', v))
    screen.bind(size=lambda s, v: setattr(rect, 'size', v))

    layout = BoxLayout(orientation='vertical', padding=40, spacing=20)

    clock_label = Label(text='--:--', font_size='80sp', bold=True, color=(1,1,1,1))
    date_label  = Label(text='---',   font_size='22sp', color=(0.114, 0.725, 0.329, 1))
    info_label  = Label(text=name.upper(), font_size='28sp', color=(0.7, 0.7, 0.7, 1))

    def update_clock(dt):
        now = datetime.now()
        clock_label.text = now.strftime("%I:%M %p")
        date_label.text  = now.strftime("%A, %B ") + str(now.day)

    if name == 'home':
        Clock.schedule_interval(update_clock, 1)
        update_clock(0)
        layout.add_widget(clock_label)
        layout.add_widget(date_label)
    else:
        layout.add_widget(info_label)
        layout.add_widget(Label(text='Mock screen — no connectivity', font_size='18sp', color=(0.4,0.4,0.4,1)))

    layout.add_widget(Widget())

    nav = BoxLayout(orientation='horizontal', size_hint_y=None, height=70, spacing=14)
    for dest, label in [('home','Home'), ('music','Music'), ('map','Map')]:
        if dest == name:
            continue
        btn = Button(text=label, font_size='18sp', bold=True,
                     background_normal='', background_color=(0.114, 0.725, 0.329, 1))
        btn.bind(on_press=lambda _, d=dest: setattr(app.root, 'current', d))
        nav.add_widget(btn)
    layout.add_widget(nav)

    screen.add_widget(layout)
    return screen


class TestApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(make_screen('home',  self))
        sm.add_widget(make_screen('music', self))
        sm.add_widget(make_screen('map',   self))
        return sm


if __name__ == '__main__':
    TestApp().run()
