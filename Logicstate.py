#2.5-D game engine
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

background = [122, 209, 233, 255]
bg_floats = [bg/255 for bg in background]

size = (448, 256)
width, height = size[0],size[1]
ratio = height/width

print(bg_floats)

map_size = (400, 450)

fov = 45
camera_lookdown_angle = 20

sea_level = 0
camera_altitude = 20

camera_distance_to_rotation = 20

player_start_pos = (100, 300, 10)

class Player_Model:
    def get_texture(self, file):
        
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 90, 126, 0, GL_RGBA, GL_UNSIGNED_BYTE, file);
        
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT);
        tex = pyglet.image.load(file).get_texture()
        return pyglet.graphics.TextureGroup(tex)

    def __init__(self):
        self.sprite = self.get_texture('sprites\\-2.png')

        self.batch = pyglet.graphics.Batch()

        s, t = 0.0, 0.0
        S, T = 90/126, 1
        tex_coords = ('t2f', [s, t, S, t, S, T, s, T])

        x, y, z = player_start_pos[0], player_start_pos[1] + camera_altitude*math.sin(camera_lookdown_angle)/math.cos(camera_lookdown_angle),3#self.set_player_on_land()
        X, Y, Z = x + 1, y+1, z+1.2

        self.batch.add(4, GL_QUADS,self.sprite,('v3f', (x, y, z, X, y, z, X, y, Z, x, y, Z)),tex_coords)

    def draw(self):
        self.batch.draw()

class Model2:
    def get_texture(self, file):
        tex = pyglet.image.load(file).get_texture()
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT);
        return pyglet.graphics.TextureGroup(tex)
    
    def __init__(self):
        self.batch = pyglet.graphics.Batch()

        #self.water_tex_file = "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python38\\Environment\\pygame-folder\\data\\sprites\\sprite workfile\\resize60\\water-files\\water-plain-0.png"
                                        
        #self.myTexture = self.get_texture(self.water_tex_file)

        model_shape = map_size

        self.amplitude = 50
        self.depth = 12

        x, y, z = 0,0,-self.depth
        
        ix, iy = int(x), int(y)
        iX, iY = ix + model_shape[0], iy+model_shape[1]
        
        self.X_range = range(ix,iX)
        self.Y_range = range(iy,iY)

        self.perl_array = perlin_array((len(self.X_range)+1, len(self.Y_range)+1), amplitude=self.amplitude)          
            
        s, t = 0.0, 0.0
        S, T = 1.0, 1.0
        tex_coords = ('t2f', [s, t, S, t, S, T, s, T])
        
        for i, I in zip(range(model_shape[0]), range(1,model_shape[0])):
            for j, J in zip(range(model_shape[1]), range(1,model_shape[1])):
                
                
                Zij = self.perl_array[i][j]
                ZIj = self.perl_array[I][j]
                ZiJ = self.perl_array[i][J]
                ZIJ = self.perl_array[I][J]

                #shaders
                rednorm = lambda red: red - (Zij-ZIJ)**2
                greenorm = lambda green: green-50*(Zij-ZIJ)
                bluenorm = lambda blue: blue-50*(Zij-ZIJ)

                color_code = [rednorm(240),greenorm(230),bluenorm(140)] #light yellow with shader
                color_floats = [cc/255 for cc in color_code]
                color_coords = ('c3f',color_floats*3)

                self.batch.add(3, GL_TRIANGLES, None, ('v3f', (x + i, y + J, z + ZiJ, x + I, y + j, z + ZIj, x + I, y + J, z + ZIJ)),
                                                        color_coords)

                self.batch.add(3, GL_TRIANGLES, None, ('v3f', (x + i, y + j, z + Zij, x + I, y + j, z + ZIj, x + i, y + J, z + ZiJ)),
                                                        color_coords)
                  
    def draw(self):
        self.batch.draw()

class Model:
    def get_texture(self, file):
        tex = pyglet.image.load(file).get_texture()
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT);
        return pyglet.graphics.TextureGroup(tex)
    
    def __init__(self):
        self.batch = pyglet.graphics.Batch()

        self.water_tex_file = "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python38\\Environment\\pygame-folder\\data\\sprites\\sprite workfile\\resize60\\water-files\\water-plain-0.png"
                                        
        x, y, z = 0,0,0
        X, Y, Z = x+map_size[0], y+map_size[1], z
        self.myTexture = self.get_texture(self.water_tex_file)

        s, t = 0.0, 0.0
        S, T = 1.0, 1.0
        tex_coords = ('t2f', [s, t, S, t, S, T, s, T])

        color_coords = ('c3f', [0,0,1] + [1, 1, 1]*3)

        self.batch.add(4, GL_QUADS, self.myTexture, ('v3f', (x, y, z, X, y, z, X, Y, z, x, Y, z)),
                       color_coords)
         
    def draw(self):
        self.batch.draw()

class Window(pyglet.window.Window):
    def Projection(self): glMatrixMode(GL_PROJECTION); glLoadIdentity()
    def Model(self): glMatrixMode(GL_MODELVIEW); glLoadIdentity()

    def set2d(self): self.Projection(); gluOrtho2D(0, self.width, 0, self.height); self.Model()
    
    def set3d(self):
        self.Projection()
        gluPerspective(fov,self.width/self.height,0.05, 1000) #min and max render distance
        self.Model()

    def set_player_on_land(self):
        ix, iy, z = int(self.player.world_coords[0]), int(self.player.world_coords[1]), self.player.world_coords[2]
        try: blah = self.model2.perl_array[ix][iy]
        except: return
        if z < blah - self.model2.depth + camera_altitude :

            dz = .1
            self.player.position[2] += dz
            self.player.world_coords[2] += dz


        elif z - 0.5 > blah - self.model2.depth + camera_altitude: dz = .08; self.player.position[2] -= dz; self.player.world_coords[2] -= dz

        

                
        

    def setLock(self,state): self.lock = state; self.set_exclusive_mouse(state)
    lock = False; mouse_lock = property(lambda self:self.lock, setLock)
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_minimum_size(160, 160)
        
        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)
        pyglet.clock.schedule(self.update)
             
        self.model = Model()
        self.model2 = Model2()

        self.player = Player()
        self.player_model = Player_Model()

        self.set3d()
        
        glRotatef(camera_lookdown_angle-90,1,0,0)
        glTranslatef(*[-x for x in player_start_pos])        
        
    def on_key_press(self,KEY,MOD):
        if KEY == key.ESCAPE: self.mouse_lock = not self.mouse_lock
    
    def update(self, dt):
        self.player.update(dt, self.keys)
        
    def on_draw(self):
        self.clear()
        
        self.set_player_on_land()
        glTranslatef(*[-x for x in self.player.position])
        
        
        
       
        self.model.draw()
        self.model2.draw()
        self.player_model.draw()

        self.player.position = [0,0,0]
        self.player.rotation = [0,0]
        
        
        
        
    def on_resize(self, width, height):
        self.set_size(width, math.floor(width*ratio))
        glViewport(0, 0, width, math.floor(width*ratio))
        

class Player:
    def __init__(self):
        self.position = [0,0,0]
        
        self.rotation = [0,0] #the "player" position is always zero (because we are always at the center of our world)
        self.world_coords = list(player_start_pos[:])
        self.world_rot = [0, -camera_lookdown_angle]

    def update(self,dt,keys):

        ds = 45*dt

        rotZ = self.world_rot[0]/180*math.pi
        dy, dx = ds*math.cos(rotZ), ds*math.sin(rotZ)
        
        if keys[key.A]: self.position[0] -= dy; self.world_coords[0] -=dy; self.position[1] += dx; self.world_coords[1] +=dx;
        if keys[key.S] or keys[key.DOWN]: self.position[0] -= dx; self.world_coords[0] -=dx; self.position[1] -= dy; self.world_coords[1] -=dy;
        if keys[key.D]: self.position[0] += dy; self.world_coords[0] +=dy; self.position[1] -= dx; self.world_coords[1] -=dx;
        if keys[key.W] or keys[key.UP]: self.position[0] += dx; self.world_coords[0] +=dx; self.position[1] += dy; self.world_coords[1] +=dy;

