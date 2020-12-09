import sys, os
import numpy as np
import math
from PIL import Image
import tkinter as tk
from tkinter import filedialog
import pyglet
from pyglet.gl import *
import pyrr
from pyglet.window import key
from perlin_noise import *
import random
from initials import *
from Logicstate import *

class Window(pyglet.window.Window):
    def Projection(self): glMatrixMode(GL_PROJECTION); glLoadIdentity()
    def Model(self): glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    def set2d(self): self.Projection(); gluOrtho2D(0, self.width, 0, self.height); self.Model()
    
    def set3d(self):
        self.Projection()
        gluPerspective(fov,self.width/self.height,0.05, 1000) #min and max render distance
        self.Model()

    def setLock(self,state): self.lock = state; self.set_exclusive_mouse(state)
    lock = False; mouse_lock = property(lambda self:self.lock, setLock)
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_minimum_size(160, 160)
        
        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)
        pyglet.clock.schedule(self.update)

        self.State = LogicState()
             
        self.set3d()
        
        glRotatef(camera_lookdown_angle-90,1,0,0)
        glTranslatef(*[-x for x in player_start_pos])
 
    def on_key_press(self,KEY,MOD):
        if KEY == key.ESCAPE or KEY == key.ENTER: self.mouse_lock = not self.mouse_lock
    
    def update(self, dt):
        self.State.update(dt, self.keys)
        
    def on_draw(self):
        self.clear()
        self.State.draw()
        
    def on_resize(self, width, height):
        self.set_size(width, math.floor(width*ratio))
        glViewport(0, 0, width, math.floor(width*ratio))
