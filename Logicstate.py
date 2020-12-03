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

LEFT, DOWN, RIGHT, UP = 0, 1, 2, 3
DOWNLEFT, DOWNRIGHT, UPRIGHT, UPLEFT = 4, 5, 6, 7

sprite_file = lambda x: f"sprites\\-{x}.png"
base_sprite = [sprite_file(x) for x in [10, 7, 4, 1]]

sprite_matrix = [[sprite_file(x) for x in [9, 10, 11, 10]],
                 [sprite_file(x) for x in [6, 7, 8, 7]],
                 [sprite_file(x) for x in [3, 4, 5, 4]],
                 [sprite_file(x) for x in [0, 1, 2, 1]]]

map_size = (300, 450)

render_mode = "standard"

fov = 54
camera_lookdown_angle = 20
camera_headroom = 5
buffer_dist = 0.5 # creates a stable range of z values where the camra or player model does not need to be moved
camera_vel = .115
camera_altitude = 20
camera_distance = camera_altitude/math.tan(camera_lookdown_angle/180*math.pi)

sea_level = 0

player_start_pos = (55, 10, camera_altitude)

SQRT2 = math.sqrt(2)
print(SQRT2)
walking_velocity = [[-camera_vel, 0],
                    [0, -camera_vel],
                    [camera_vel, 0],
                    [0, camera_vel],
                    [-SQRT2/2 * camera_vel, -SQRT2/2 * camera_vel],
                    [SQRT2/2 * camera_vel, -SQRT2/2 * camera_vel],
                    [SQRT2/2 * camera_vel, SQRT2/2 * camera_vel],
                    [-SQRT2/2 * camera_vel, SQRT2/2 * camera_vel]]

swimming_velocity = [[vel[0]*.7, vel[1]*.7] for vel in walking_velocity] 

class Player_Model:
    def get_texture(self, file):
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT);
        tex = pyglet.image.load(file).get_texture()
        return pyglet.graphics.TextureGroup(tex)

    def ready_batch_to_draw(self, x, y, z, s = 0, t = 0, S = 90/126, T = 1, file='sprites\\-2.png'):
        self.sprite = self.get_texture(file)

        self.batch = pyglet.graphics.Batch()

        tex_coords = ('t2f', [s, t, S, t, S, T, s, T])

        player_height = 1.2
        y = y - (player_height*math.cos(camera_lookdown_angle/180*math.pi))/2
        z = z + 0.1
        X, Y, Z = x + 1, y + player_height* math.sin(camera_lookdown_angle/180*math.pi), z+player_height*math.cos(camera_lookdown_angle/180*math.pi), 

        self.batch.add(4, GL_QUADS,self.sprite,('v3f', (x, y, z, X, y, z, X, Y, Z, x, Y, Z)),tex_coords)

    def __init__(self, x = player_start_pos[0], y = player_start_pos[1] + camera_distance, z = 0):
        
        self.x = x
        self.y = y
        self.z = z

        self.swim_depth = 0.65 * math.cos(camera_lookdown_angle/180*math.pi)
        self.foot_room = 0.1 * math.cos(camera_lookdown_angle/180*math.pi)

        self.swim_cutoff = sea_level - self.swim_depth - self.foot_room
        
        self.ready_batch_to_draw(self.x, self.y, self.z, file='sprites\\-2.png')

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

    def real_altitude_norm(self):
        for i, row in enumerate(self.perl_array):
            for j, zij in enumerate(row):
                self.perl_array[i][j] = self.perl_array[i][j] - self.depth

    def deep_water_norm(self):
        for i, row in enumerate(self.perl_array):
            for j, zij in enumerate(row):
                if zij < -0.5:
                    self.perl_array[i][j] = -0.61  #sorrys
                elif zij < -0.2:
                    self.perl_array[i][j] = -0.4
                    
                    
                    
    
    def __init__(self):
        self.batch = pyglet.graphics.Batch()

        model_shape = map_size

        self.height = 10
        self.depth = 5
        self.amplitude = self.height + self.depth

        x, y, z = 0,0,0
        
        ix, iy = int(x), int(y)
        iX, iY = ix + model_shape[0], iy+model_shape[1]
        
        self.X_range = range(ix,iX)
        self.Y_range = range(iy,iY)

        self.perl_array = perlin_array((len(self.X_range)+1,
                                        len(self.Y_range)+1),
                                       amplitude=self.amplitude,
                                       persistence = 0.3,
                                       lacunarity = 3.5,
                                       norm = render_mode)

        self.real_altitude_norm()
        #self.flatten_shore_norm()
        #self.deep_water_norm()
            
        s, t = 0.0, 0.0
        S, T = 1.0, 1.0
        tex_coords = ('t2f', [s, t, S, t, S, T, s, T])

        
        
        for i, I in zip(range(model_shape[0]), range(1,model_shape[0])):
            vertex_color_row = []
            
            for j, J in zip(range(model_shape[1]), range(1,model_shape[1])):
                
                
                Zij = self.perl_array[i][j]
                ZIj = self.perl_array[I][j]
                ZiJ = self.perl_array[i][J]
                ZIJ = self.perl_array[I][J]

                Z3 = self.perl_array[I+1][j]
                Z4 = self.perl_array[I+1][J]

                #shaders
                rednorm = lambda red, z1, z2: red - 10*(z1-z2)
                greenorm = lambda green, z1, z2: green-34*(z1-z2)
                bluenorm = lambda blue, z1, z2: blue-5*(z1-z2)

                color_floats = lambda code: [cc/255 for cc in code]

                sand_color = (240,230,140)

                norm = lambda r,g,b, z1, z2: color_floats([rednorm(r, z1, z2), greenorm(g, z1, z2), bluenorm(b, z1, z2)])

                color_code_ij = norm(*sand_color, Zij, ZIj) #light yellow with shader
                color_code_Ij = norm(*sand_color, ZIj, Z3)
                color_code_iJ = norm(*sand_color, ZiJ, ZIJ)
                color_code_IJ = norm(*sand_color, ZIJ, Z4)

                if ( i - j )%2 == 0:
                    
                    color_coords_1 = ('c3f',color_code_ij + color_code_Ij + color_code_iJ)
                    color_coords_2 = ('c3f',color_code_iJ + color_code_Ij + color_code_IJ)

                    self.batch.add(3, GL_TRIANGLES, None, ('v3f', (x + i, y + j, z + Zij, x + I, y + j, z + ZIj, x + i, y + J, z + ZiJ)),
                                                            color_coords_1)

                    self.batch.add(3, GL_TRIANGLES, None, ('v3f', (x + i, y + J, z + ZiJ, x + I, y + j, z + ZIj, x + I, y + J, z + ZIJ)),
                                                            color_coords_2)

                else:
                    color_coords_1 = ('c3f',color_code_iJ + color_code_ij + color_code_IJ)
                    color_coords_2 = ('c3f',color_code_ij + color_code_Ij + color_code_IJ)

                    self.batch.add(3, GL_TRIANGLES, None, ('v3f', (x + i, y + J, z + ZiJ, x + i, y + j, z + Zij, x + I, y + J, z + ZIJ)),
                                                            color_coords_1)

                    self.batch.add(3, GL_TRIANGLES, None, ('v3f', (x + i, y + j, z + Zij, x + I, y + j, z + ZIj, x + I, y + J, z + ZIJ)),
                                                            color_coords_2)
                  
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

        self.water_tex_file = "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python38\\Environment\\perlin noise\\0.txt"
                                        
        x, y, z = -map_size[0],-map_size[1],sea_level
        X, Y, Z = x+3*map_size[0], y+3*map_size[1], z
        #self.myTexture = self.get_texture(self.water_tex_file)

        s, t = 0.0, 0.0
        S, T = 1.0, 1.0
        tex_coords = ('t2f', [s, t, S, t, S, T, s, T])

        color_coords = ('c3f', [0.2,0.1,0.88]*2 + [1,1,1]*2)

        self.batch.add(4, GL_QUADS, None, ('v3f', (x, y, z, X, y, z, X, Y, z, x, Y, z)),
                       color_coords)

    def get_int_array_from_file(self, file):
        data_file = pyglet.resource.file(file)
        return data_file
         
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

    def calculate_interpolation(self, x, y):

        ix, iy = int(x), int(y)
        
        iX, iY = ix+1, iy+1

        try:
            blob_hxy = self.model2.perl_array[ix][iy]
            blob_hXy = self.model2.perl_array[iX][iy]
            blob_hxY = self.model2.perl_array[ix][iY]
            blob_hXY = self.model2.perl_array[iX][iY]

        except: return

        f_x = blob_hXy - blob_hxy
        f_y = blob_hxY - blob_hxy

        dx = x - ix
        dy = y - iy

        return f_x, f_y, dx, dy, blob_hxy

    def set_player_model_on_land(self):
        f_x1, f_y1, dx1, dy1, z = self.calculate_interpolation(self.player.player_model.x, self.player.player_model.y)
        f_x2, f_y2, dx2, dy2, z = self.calculate_interpolation(self.player.player_model.x + 1, self.player.player_model.y)

        left_foot_z = f_x1*dx1 + f_y1*dy1 + z
        right_foot_z = f_x1*dx2 + f_y1*dy2 + z #use different dx an dy for left foot but same derivatives to hopefully reduce bounce

        self.player.player_model.z = max(left_foot_z, right_foot_z, self.player.player_model.swim_cutoff)

    def is_swimming(self):
        
        if self.player.player_model.z < -self.player.player_model.swim_depth:
            self.player.swim_state = True
        else: self.player.swim_state = False

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
        
        self.set3d()

        self.anim_frame_counter = 0
        self.anim_skip_len = 5
        self.anim_index = 0
        
        glRotatef(camera_lookdown_angle-90,1,0,0)
        glTranslatef(*[-x for x in player_start_pos])

        
        
    def on_key_press(self,KEY,MOD):
        if KEY == key.ESCAPE: self.mouse_lock = not self.mouse_lock
    
    def update(self, dt):
        self.player.update(dt, self.keys)
        self.player.update_movement()
        
        #self.set_player_on_land()
        self.set_player_model_on_land()
        self.is_swimming()

    def frame_counter(self):
        self.anim_frame_counter+=1

        if self.anim_frame_counter == self.anim_skip_len:
            self.anim_index = (self.anim_index + 1)%4
            self.anim_frame_counter = 0
        
    def on_draw(self):
        self.clear()

        self.player.update_sprite(self.anim_index)
        
        glTranslatef(*[-x for x in self.player.position])
       
        self.model.draw()
        self.model2.draw()
        self.player.player_model.draw()

        self.player.position = [0,0,0]
        self.player.rotation = [0,0]

        self.frame_counter()
        
    
    def on_resize(self, width, height):
        self.set_size(width, math.floor(width*ratio))
        glViewport(0, 0, width, math.floor(width*ratio))
        

class Player:
    def __init__(self):
        self.position = [0,0,0]
        
        self.rotation = [0,0] #the "player" position is always zero (because we are always at the center of our world)
        self.world_coords = list(player_start_pos[:])
        self.world_rot = [0, -camera_lookdown_angle]

        self.player_model = Player_Model()
        self.direction = UP
        self.swim_state = False

        self.moving = None

    def update_movement(self):
        if self.moving is not None:
            if self.swim_state:
                self.position[0] += swimming_velocity[self.moving][0]
                self.position[1] += swimming_velocity[self.moving][1]
                self.world_coords[0] += swimming_velocity[self.moving][0]
                self.world_coords[1] += swimming_velocity[self.moving][1]
                self.player_model.x += swimming_velocity[self.moving][0]
                self.player_model.y += swimming_velocity[self.moving][1]
            else:
                self.position[0] += walking_velocity[self.moving][0]
                self.position[1] += walking_velocity[self.moving][1]
                self.world_coords[0] += walking_velocity[self.moving][0]
                self.world_coords[1] += walking_velocity[self.moving][1]
                self.player_model.x += walking_velocity[self.moving][0]
                self.player_model.y += walking_velocity[self.moving][1]

    def update_sprite(self, anim_index):
        if self.moving is not None and not self.swim_state:
            self.player_model.ready_batch_to_draw(self.player_model.x,
                                                  self.player_model.y,
                                                  self.player_model.z,
                                                  file=sprite_matrix[self.direction][anim_index])
        else:
            self.player_model.ready_batch_to_draw(self.player_model.x,
                                                  self.player_model.y,
                                                  self.player_model.z,
                                                  file=base_sprite[self.direction])

    def update(self,dt,keys):

        if keys[key.A]:
            if keys[key.S]:
                self.moving = DOWNLEFT
                self.direction = DOWN
            elif keys[key.W]:
                self.moving = UPLEFT
                self.direction = UP
            else: self.moving = LEFT; self.direction = LEFT
            
            
        elif keys[key.S]:
            if keys[key.D]:
                self.moving = DOWNRIGHT
                self.direction = DOWN

            else: self.moving = self.direction = DOWN
                
        
        elif keys[key.D]:
            if keys[key.W]:
                self.moving = UPRIGHT
                self.direction = UP

            else: self.moving = self.direction = RIGHT
            
        elif keys[key.W]: self.moving = self.direction = UP

        else: self.moving = None


