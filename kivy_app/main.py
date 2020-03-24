
# Importing kivy GUI modules
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import  Button
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.graphics import Color, Line, Rectangle
from kivy.lang import Builder
from kivy.config import Config
Config.set('graphics', 'width', 1200)
Config.set('graphics', 'height', 900)
Config.write()

import matplotlib
matplotlib.use('module://kivy.garden.matplotlib.backend_kivy')
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvas, NavigationToolbar2Kivy

# Importing required base modules
import sys
import struct
import io
import os
import math
import numpy as np
from numba import jit
import matplotlib.pyplot as plt
from scipy import optimize







class MainWindow(Screen):
    pass


class FileSelectorWindow(Screen):
    file_directory = ObjectProperty(None)



kv = Builder.load_file('gui/FLIM.kv')
windowManager = ScreenManager()

windows = [
    MainWindow(name = 'main'),
    FileSelectorWindow(name = 'file')
]

for window in windows:
    windowManager.add_widget(window)

windowManager.current = 'main'


class FLIMApp(App):

    def build(self):
        return(windowManager)


if __name__ == '__main__':
    FLIMApp().run()