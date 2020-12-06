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

map_size = (150, 750)
fov = 55

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



ocean_color = [0.2,0.1,0.88]

base_grey = (150,150,150)
sand_color = (240,230,140)
grass_color = (37.6, 150.2, 22)
dirt_color = (210,105,30)

render_mode = "standard"


camera_lookdown_angle = 25
camera_headroom = 5
buffer_dist = 0.5 # creates a stable range of z values where the camra or player model does not need to be moved
camera_vel = .155
camera_altitude = 13
camera_distance = camera_altitude/math.tan(camera_lookdown_angle/180*math.pi)

sea_level = -1

player_start_pos = (.5*map_size[0], .25*map_size[1], camera_altitude)

SQRT2 = math.sqrt(2)

velocity_matrix = [[-1, 0, 0],
                    [0, -1, 0],
                    [1, 0, 0],
                    [0, 1, 0],
                    [-SQRT2/2 * 1, -SQRT2/2 * 1, 0],
                    [SQRT2/2 * 1, -SQRT2/2 * 1, 0],
                    [SQRT2/2 * 1, SQRT2/2 * 1, 0],
                    [-SQRT2/2 * 1, SQRT2/2 * 1, 0]]

velocity_matrix = np.asarray(velocity_matrix)

walking_velocity = [[-camera_vel, 0, 0],
                    [0, -camera_vel, 0],
                    [camera_vel, 0, 0],
                    [0, camera_vel, 0],
                    [-SQRT2/2 * camera_vel, -SQRT2/2 * camera_vel, 0],
                    [SQRT2/2 * camera_vel, -SQRT2/2 * camera_vel, 0],
                    [SQRT2/2 * camera_vel, SQRT2/2 * camera_vel, 0],
                    [-SQRT2/2 * camera_vel, SQRT2/2 * camera_vel, 0]]

swimming_velocity = [[vel[0]*.7, vel[1]*.7, 0] for vel in walking_velocity]

class Decoration_Model:
    def get_texture(self, file):
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT);
        tex = pyglet.image.load(file).get_texture()
        return pyglet.graphics.TextureGroup(tex)

    def ready_batch_to_draw(self, s = .3, t = 0, S = .7, T = 1, file='sprites\\sprite workfile\\standing grass texture.png'):
        self.sprite = self.get_texture(file)

        self.batch = pyglet.graphics.Batch()

        tex_coords = ('t2f', [s, t, S, t, S, T, s, T])

        for coord in self.dec_holder:
            x, y, z = coord
            width = random.uniform(1, 5)
            height = random.uniform(0.5, 4)

            x = x - width /2
            z = z - 0.15

            X, Y, Z = x + width, y, z+height

            self.batch.add(4, GL_QUADS,self.sprite,('v3f', (x, y, z, X, y, z, X, Y, Z, x, Y, Z)),tex_coords)

            x = x + width/3
            y = y - width/2
            Y = y + width

            self.batch.add(4, GL_QUADS,self.sprite,('v3f', (x, y, z, x, Y, z, x, Y, Z, x, y, Z)),tex_coords)

    def __init__(self):
        self.dec_holder = []
        self.dec_perl = []
        
    def draw(self):
        self.batch.draw()

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

    def height_mask_norm(self):
        high_perl_array = perlin_array((len(self.X_range)+1,
                                        len(self.Y_range)+1),
                                        amplitude=self.amplitude,
                                        scale = min(self.model_shape[0], self.model_shape[1])/4,
                                        persistence = 0.3,
                                        lacunarity = 2.5,
                                        norm = "normalized")

        for i, row in enumerate(self.perl_array):
            for j, zij in enumerate(row):
                if self.perl_array[i][j] > 0:
                    self.perl_array[i][j] = self.perl_array[i][j]*high_perl_array[i][j]*1.7
        

        

    def deep_water_norm(self):
        for i, row in enumerate(self.perl_array):
            for j, zij in enumerate(row):
                if zij < sea_level -0.1:
                    self.perl_array[i][j] = (self.perl_array[i][j] - sea_level)*2 + sea_level

    def flatten_world_into_island(self):
        island_norm = lambda x, y: 1.5*math.exp(-((x - self.model_shape[0]/2))**2/(self.model_shape[0]/4)**2 -((y - self.model_shape[1]/2))**2/(self.model_shape[1]/4)**2 )
        for i,row in enumerate(self.perl_array):
            for j, z in enumerate(row):
                if self.perl_array[i][j] > sea_level - 0.5:
                    self.perl_array[i][j] = self.perl_array[i][j]*min(island_norm(i,j), self.height + 2) - 0.2

    def radial_norm_island(self):
        radial_norm = lambda i,j: pow((((i - self.model_shape[0]/2)/(self.model_shape[0]))**2 + ((j - self.model_shape[1]/2)/self.model_shape[1])**2),0.5)
        for i,row in enumerate(self.perl_array):
            for j, z in enumerate(row):
                self.perl_array[i][j] = self.perl_array[i][j] - radial_norm(i,j)*self.height*1.5

    def lerp(self, color1, color2, index, grades):
        lerp = []
        for x, y in zip(color1, color2):
            lerp.append((y*index + (x)*(grades-index))/grades)
        return lerp

    def create_world_vertex_color(self):
        for i in range(self.model_shape[0] + 1):
            new_vertex_color_row = []
            for j in range(self.model_shape[1] + 1):
                if self.perl_array[i][j] < self.grass_height:
                    grades = 1
                    color = self.lerp(sand_color, base_grey, max(self.perl_array[i][j], self.grass_height - 3)/self.grass_height, grades)

                elif self.perl_array[i][j] > self.grass_height:
                    grades = 2
                    color = self.lerp(base_grey, grass_color, min(self.perl_array[i][j] - (self.grass_height), grades), grades)
                else:
                    color = base_grey
                new_vertex_color_row.append(color)
            self.vertex_color_matrix.append(new_vertex_color_row)

    def color_vertices_on_quad(self, i, j, I, J, Z_list):

        Zij, ZIj, ZiJ, ZIJ, Zi3j, Zi3J = Z_list
    
        color = base_grey
                    
        rednorm = lambda red, z1, z2: red - 13*(z1-z2)
        greenorm = lambda green, z1, z2: green-12*(z1-z2)
        bluenorm = lambda blue, z1, z2: blue-12*(z1-z2)

        color_floats = lambda code: [cc/255 for cc in code]

        norm = lambda r,g,b, z1, z2: color_floats([rednorm(r, z1, z2), greenorm(g, z1, z2), bluenorm(b, z1, z2)])

        color1, color2, color3, color4 = self.vertex_color_matrix[i][j], self.vertex_color_matrix[I][j], self.vertex_color_matrix[i][J], self.vertex_color_matrix[I][J] 
        color_code_ij = norm(*color1, Zij, ZIj)
        color_code_Ij = norm(*color2, ZIj, Zi3j)
        color_code_iJ = norm(*color3, ZiJ, ZIJ)
        color_code_IJ = norm(*color4, ZIJ, Zi3J)

        return color_code_ij, color_code_Ij, color_code_iJ, color_code_IJ
        
    def create_world_model(self, x, y, z):
        for i, I in zip(range(self.model_shape[0]), range(1,self.model_shape[0])):
            
            for j, J in zip(range(self.model_shape[1]), range(1,self.model_shape[1])):

                Zij = self.perl_array[i][j]
                ZIj = self.perl_array[I][j]
                ZiJ = self.perl_array[i][J]
                ZIJ = self.perl_array[I][J]

                Zi3j = self.perl_array[I+1][j]
                Zi3J = self.perl_array[I+1][J]

                Z_list = [Zij, ZIj, ZiJ, ZIJ, Zi3j, Zi3J]

                color_code = self.color_vertices_on_quad(i, j, I, J, Z_list)
                color_code_ij, color_code_Ij, color_code_iJ, color_code_IJ = color_code
                

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

    def create_decorations(self):
        for i in range(self.model_shape[0]*self.model_shape[1]//4):
            x, y = random.randint(0, self.model_shape[0]), random.randint(0, self.model_shape[1])
            z = self.perl_array[x][y]

            if z > sea_level and self.decoration_model.dec_perl[x][y] == 3:
                self.decoration_model.dec_holder.append((x, y, z))
                    
                    
    def __init__(self):
        self.batch = pyglet.graphics.Batch()
        
        self.model_shape = map_size

        self.height = 12#random.randint(int(map_size[0]/20), int(map_size[0]/10))
        
        self.depth = random.randint(1, max(self.height // 4, 2))
        print (f"height was {self.height}, depth was {self.depth}")
        self.amplitude = self.height + self.depth

        x, y, z = 0,0,0

        self.grass_height = sea_level + 4
        self.vertex_color_matrix = []
        
        ix, iy = int(x), int(y)
        iX, iY = ix + self.model_shape[0], iy+self.model_shape[1]
        
        self.X_range = range(ix,iX)
        self.Y_range = range(iy,iY)

        print("model array")

        self.perl_array = perlin_array((len(self.X_range)+1,
                                        len(self.Y_range)+1),
                                       amplitude=self.amplitude,
                                       scale = random.randint(self.model_shape[0]//10, self.model_shape[0]//6),
                                       octaves = random.randint(4, 5),
                                       persistence = random.randint(16, 34)/100,
                                       lacunarity = random.randint(34, 40)/10,
                                       norm = render_mode)
        print("decoration array")
        self.decoration_model = Decoration_Model()

        self.decoration_model.dec_perl = perlin_array((len(self.X_range)+1, len(self.Y_range)+1),
                                                     scale = 50,
                                                     octaves=4,
                                                     lacunarity = 3,
                                                     norm = "grade8")


        self.real_altitude_norm()

        self.height_mask_norm()

        #self.flatten_world_into_island()
        self.deep_water_norm()

        self.radial_norm_island()
        
        self.create_world_vertex_color()
        self.create_world_model(x, y, z) #x, y, z is lower left corner
        self.create_decorations()
        self.decoration_model.ready_batch_to_draw()
                  
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
        self.width = 3*max(map_size[0], map_size[1])                   
        x, y, z = -self.width//3,-self.width//3,sea_level
        X, Y, Z = x+int(self.width), y+int(self.width), z
        #self.myTexture = self.get_texture(self.water_tex_file)

        s, t = 0.0, 0.0
        S, T = 1.0, 1.0
        tex_coords = ('t2f', [s, t, S, t, S, T, s, T])

        color_coords = ('c3f', ocean_color*2 + [1,1,1]*2)

        self.batch.add(4, GL_QUADS, None, ('v3f', (x, y, z, X, y, z, X, Y, z, x, Y, z)),
                       color_coords)

    def get_int_array_from_file(self, file):
        data_file = pyglet.resource.file(file)
        return data_file
         
    def draw(self):
        self.batch.draw()

    def redraw(self, dt):
        pass

class LogicState:
    def __init__(self):
        self.model = Model()
        self.model2 = Model2()

        self.player = Player()

        print(self.model2.model_shape[0]//2,
              self.model2.model_shape[1]//3,
              self.model2.perl_array[self.model2.model_shape[0]//2][self.model2.model_shape[1]//3])

        self.anim_frame_counter = 0
        self.anim_skip_len = 5
        self.anim_index = 0

    def animate_ocean(self, dt):
        self.model.redraw(dt)

    def update(self, dt, keys):
        self.player.update(dt, keys)
        self.animate_ocean(dt)
        self.set_player_model_on_land()
        self.set_camera_follow_player()
        self.is_swimming()
        self.player.update_movement()
        

    def draw(self):
        self.player.update_sprite(self.anim_index)
        
        glTranslatef(*[-x for x in self.player.position])

        glTranslatef(*[-x for x in self.player.camera_position])
       
        self.model.draw()
        self.model2.draw()
        self.player.player_model.draw()
        self.model2.decoration_model.draw()

        self.player.position = [0,0,0]
        self.player.rotation = [0,0]
        self.player.camera_position = [0,0,0]

        self.frame_counter()

    def frame_counter(self):
        self.anim_frame_counter+=1

        if self.anim_frame_counter == self.anim_skip_len:
            self.anim_index = (self.anim_index + 1)%4
            self.anim_frame_counter = 0

    def calculate_interpolation(self, x, y):

        ix, iy = int(x), int(y)
        
        iX, iY = ix+1, iy+1

        try:
            blob_hxy = self.model2.perl_array[ix][iy]
            blob_hXy = self.model2.perl_array[iX][iy]
            blob_hxY = self.model2.perl_array[ix][iY]
            blob_hXY = self.model2.perl_array[iX][iY]

        except: return 0,0,x-ix, y-iy,0

        f_x = blob_hXy - blob_hxy
        f_y = blob_hxY - blob_hxy

        dx = x - ix
        dy = y - iy

        return f_x, f_y, dx, dy, blob_hxy

    def set_player_model_on_land(self):
        f_x1, f_y1, dx1, dy1, z = self.calculate_interpolation(self.player.player_model.x+.5, self.player.player_model.y)
        f_x2, f_y2, dx2, dy2, z = self.calculate_interpolation(self.player.player_model.x + .5, self.player.player_model.y)

        left_foot_z = f_x1*dx1 + f_y1*dy1 + z
        right_foot_z = f_x1*dx2 + f_y1*dy2 + z #use different dx an dy for left foot but same derivatives to hopefully reduce bounce

        new_z = max(left_foot_z, right_foot_z, self.player.player_model.swim_cutoff)
        
        if self.player.player_model.z < new_z + .1:
            self.player.falling = False
            self.player.falling_velocity = 0
            self.player.player_model.z = new_z

        elif self.player.player_model.z > new_z + .2 and self.player.falling_velocity == 0: self.player.falling = True

    def set_camera_follow_player(self):
        if self.player.world_coords[2] < self.player.player_model.z + camera_altitude - buffer_dist:
            self.player.camera_position[2] += .04
            self.player.world_coords[2] += .04
            
        elif self.player.world_coords[2] > self.player.player_model.z + camera_altitude + buffer_dist:
            
            self.player.camera_position[2] += -.04
            self.player.world_coords[2] += -.04
            
            
       

    def is_swimming(self):
        
        if self.player.player_model.z < -self.player.player_model.swim_depth + sea_level:
            self.player.swim_state = True
        else: self.player.swim_state = False

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
        

class Player:
    def __init__(self):
        self.position = [0,0,0]
        self.camera_position = [0,0,0]
    
        self.rotation = [0,0] #the "player" position is always zero (because we are always at the center of our world)
        self.world_coords = list(player_start_pos[:])
        self.world_rot = [0, -camera_lookdown_angle]

        self.velocity_matrix = np.zeros(velocity_matrix.shape)

        self.player_model = Player_Model()
        self.direction = UP
        self.swim_state = False
        self.falling = True
        self.on_land = False
        self.jumping = False

        self.moving = None
        self.speedup = None
        self.slowdown = None

        self.speed_up_flag = False
        self.slow_down_flag = False
        self.stop_flag = True

        self.falling_velocity = 0

    def update_velocity(self, vel_norm):
        self.velocity_matrix = np.add(self.velocity_matrix, [[v*vel_norm for v in vel]for vel in velocity_matrix])

    def update_position(self, velocity, moving):
        self.position[0] += velocity[moving][0]
        self.position[1] += velocity[moving][1]
        self.world_coords[0] += velocity[moving][0]
        self.world_coords[1] += velocity[moving][1]
        self.player_model.x += velocity[moving][0]
        self.player_model.y += velocity[moving][1]

    def update_vertical(self, vel):
        self.player_model.z += vel

    def vel_norm(self):
        return -self.velocity_matrix[0][0]

    def set_stop_flag(self):
        if self.vel_norm() < .0001:
            self.stop_flag = True

    def update_movement(self):
                
        if self.moving is not None:
            if self.speedup is not None:
                self.update_velocity(.01)
                self.update_position(self.velocity_matrix, self.speedup)

            elif self.slow_down_flag:
                
                self.set_stop_flag()
                
                if self.stop_flag:
                    self.stop_flag = False
                    self.moving = None
                    self.velocity_matrix = np.zeros(velocity_matrix.shape)
                    
                else:
                    self.update_velocity(-.00001)
                    self.update_position(self.velocity_matrix, self.slowdown)
                
            if self.swim_state:
                self.update_position(swimming_velocity, self.moving)
            else:
                self.update_position(walking_velocity, self.moving)
            

        if self.jumping:
            self.falling_velocity = .175
            self.jumping = False
            self.falling = True

        if self.falling:
            self.fall()
            self.update_vertical(self.falling_velocity)
        
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

    def fall(self):
        self.falling_velocity += -.01

    def find_reverse_direction(self, speedup):
        if speedup == LEFT: return RIGHT
        if speedup == DOWN: return UP
        if speedup == RIGHT: return LEFT
        if speedup == UP: return DOWN
        if speedup == DOWNLEFT: return UPRIGHT
        if speedup == DOWNRIGHT: return UPLEFT
        if speedup == UPRIGHT: return DOWNLEFT
        if speedup == UPLEFT: return DOWNRIGHT

    def update(self,dt,keys):

        if keys[key.L] and not self.falling and not self.swim_state:
            self.jumping = True
    
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

        


