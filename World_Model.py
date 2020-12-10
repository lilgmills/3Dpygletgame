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

 #??????????

class World_Model:
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

    def height_mask_norm(self, seed):
        print("height mask array")
        random.seed(seed)
        scale = random.random()*world_size/4 + world_size*1/4
        random.seed(seed)
        persistence = random.random()*.35 + .25
        high_perl_array = perlin_array((len(self.X_range)+1,
                                        len(self.Y_range)+1),
                                        amplitude=self.amplitude,
                                        scale = scale,
                                        persistence = persistence,
                                        lacunarity = 3.5,
                                        seed = seed,
                                        norm = "normalized")

        for i, row in enumerate(self.perl_array):
            for j, zij in enumerate(row):
                if self.perl_array[i][j] > -0.5:
                    self.perl_array[i][j] = self.perl_array[i][j] - 2*self.height/3*pow(abs((i - world_size/2)/(world_size/2))**4 + abs((j - world_size/2)/(world_size/2))**4, 0.25)
                    self.perl_array[i][j] = self.perl_array[i][j] + 1 - 2/(world_size/2)*(abs(i - world_size/2) + abs(j - world_size/2))

    def another_height_mask(self, seed):
        x, y, z = 0,0,0
        ix, iy = int(x), int(y)
        iX, iY = ix + self.model_shape[0], iy+self.model_shape[1]
        
        self.X_range = range(ix,iX)
        self.Y_range = range(iy,iY)

        print ("height mask 2")

        random.seed(seed)
        scale = scale = random.random()*world_size/4 + world_size*1/8

        random.seed(seed)
        octaves = random.randint(4, 5)

        random.seed(seed)
        persistence = random.randint(16, 34)/100

        random.seed(seed)
        lacunarity = random.randint(34, 40)/10

        height_mask_array = perlin_array((len(self.X_range)+1,
                                        len(self.Y_range)+1),
                                        amplitude=self.amplitude,
                                        scale = scale,
                                        octaves = octaves,
                                        persistence = persistence,
                                        lacunarity = lacunarity,
                                        seed = seed, norm = render_mode)

        for i in range(len(self.perl_array)):
            for j in range(len(self.perl_array[0])):
                self.perl_array[i][j] = self.perl_array[i][j] + (height_mask_array[i][j] - self.depth)

    def flatland_norm(self):
        for i in range(len(self.perl_array)):
            for j in range(len(self.perl_array[0])):
                if self.perl_array[i][j] < sea_level:
                    self.perl_array[i][j] = -1
                else: self.perl_array[i][j] = 1
                    
    
    def render(self, seed):
                
        self.perl_array = np.asarray(self.perl_array)
        
        
        self.flatland_norm()
        
        self.another_height_mask(seed)
        

        self.height_mask_norm(seed)
        

        


    def lerp(self, color1, color2, index, grades):
        lerp = []
        for x, y in zip(color1, color2):
            lerp.append((y*index + (x)*(grades-index))/grades)
        return lerp

    def diffuse_shader(self, color):
        ambient_strength = 1.2
        ambient_color = [c*ambient_strength for c in color]

        return ambient_color

    def create_world_vertex_color(self):
        grass_color = (37.6, 110, 22)
        for i in range(self.model_shape[0] + 1):
            new_vertex_color_row = []
            for j in range(self.model_shape[1] + 1):
 
                if self.perl_array[i][j] < self.grass_height:
                    grades = 1
                    color = self.lerp(sand_color, dirt_color, max(self.perl_array[i][j], self.grass_height - 2)/self.grass_height, grades)

                elif self.perl_array[i][j] > self.grass_height:

                    fix_prob = random.random()
                    if self.grass_array[i][j] == 1 and fix_prob < 0.6:
                        color = grass_color
                    else:
                        
                        color = grass_color
                    grades = 2
                    color = self.lerp(dirt_color, color, min(self.perl_array[i][j] - (self.grass_height), grades), grades)

                color = self.diffuse_shader(color)
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

    def create_decorations(self, gem_spawn):
        
        number_of_textures = 2
        
        for i in range(self.model_shape[0] + 1):
            for j in range(self.model_shape[1] + 1):
                if len(self.decoration_model.dec_holder) < self.decoration_model.texture_max:
                    
                    z = self.perl_array[i][j]
                    if z > sea_level:
                        grassy_val = self.decoration_model.grass_dec_perl[i][j]
                        leafy_val = self.decoration_model.leafy_dec_perl[i][j]
                        
                            
                        fix_prob = random.random()
                        small_prob = 0.015 * number_of_textures
                        

                        if fix_prob < small_prob:
                            if grassy_val == 4 and leafy_val == 2:
                                if fix_prob < 0.015:
                                    w = random.uniform(1, 3)
                                    h = random.uniform(0.75, 4)
                                    self.decoration_model.dec_holder.append(("grass",i, j, z, w, h))
                                else:
                                    w = random.uniform(1, 2)
                                    h = random.uniform(1, 4)
                                    self.decoration_model.dec_holder.append(("leafy",i, j, z, w, h))
                                    
                            elif grassy_val == 4:
                                w = random.uniform(1, 3)
                                h = random.uniform(0.75, 4)
                                self.decoration_model.dec_holder.append(("grass",i, j, z, w, h))
                                
                            elif leafy_val == 2:
                                w = random.uniform(1, 2)
                                h = random.uniform(1, 4)
                                self.decoration_model.dec_holder.append(("leafy",i, j, z, w, h))
                                
        for i in range(self.model_shape[0] + 1):
            for j in range(self.model_shape[1] + 1):
                if gem_spawn:
                    
                    z = self.perl_array[i][j]
                    if z > sea_level:
                        
                        if len(self.ruby_model.ruby_dec_holder) < self.ruby_model.texture_max:
                            ruby_val = self.ruby_model.ruby_dec_perl[i][j]
                            
                            fix_prob = random.random()
                            ruby_prob = 0.01
                            if ruby_val == 1 and fix_prob < ruby_prob:
                                self.ruby_model.ruby_dec_holder.append(("ruby", i, j, z, 1.5, 2))

                        
    def __init__(self, seed, gem_spawn):
        self.batch = pyglet.graphics.Batch()
        
        self.model_shape = map_size

        self.height = 8#random.randint(int(map_size[0]/35), int(map_size[0]/15))
        
        self.depth = 2#random.randint(2, max(self.height // 4, 2))

        print("---------------------------------------------")
        print (f"height was {self.height}, depth was {self.depth}")
        self.amplitude = self.height + self.depth

        x, y, z = 0,0,0

        self.grass_height = sea_level + 2
        self.vertex_color_matrix = []
        
        ix, iy = int(x), int(y)
        iX, iY = ix + self.model_shape[0], iy+self.model_shape[1]
        
        self.X_range = range(ix,iX)
        self.Y_range = range(iy,iY)

        print ("world model")

        random.seed(seed)
        scale = scale = random.random()*world_size/2 + world_size*1/2

        random.seed(seed)
        octaves = random.randint(10, 10)

        random.seed(seed)
        persistence = random.randint(16, 34)/100

        random.seed(seed)
        lacunarity = random.randint(34, 40)/10

        self.perl_array = perlin_array((len(self.X_range)+1,
                                        len(self.Y_range)+1),
                                        amplitude=self.amplitude,
                                        scale = scale,
                                        octaves = octaves,
                                        persistence = persistence,
                                        lacunarity = lacunarity,
                                        seed = seed, norm = render_mode)

        

        print("grass array")

        self.grass_array = perlin_array((len(self.X_range)+1,
                                        len(self.Y_range)+1),
                                       amplitude = 1,
                                       scale = 60,
                                       octaves = 5,
                                       persistence = .6,
                                       lacunarity = .3,
                                       seed =seed, norm = "ternary")
        
        self.decoration_model = Decoration_Model(gem_spawn)

        print("decoration array")
        self.decoration_model.grass_dec_perl = perlin_array((len(self.X_range)+1, len(self.Y_range)+1),
                                                     scale = 50,
                                                     octaves=4,
                                                     lacunarity = 3,
                                                     seed = seed, norm = "grade8")

        print("decoration 2 array")

        self.decoration_model.leafy_dec_perl = perlin_array((len(self.X_range)+1, len(self.Y_range)+1),
                                                            scale = 50,
                                                            octaves=4,
                                                            lacunarity = 3,
                                                            seed = seed, norm = "grade8")
        if gem_spawn:
            self.ruby_model = Ruby_Model()
            
            self.ruby_model.ruby_dec_perl = perlin_array((len(self.X_range)+1, len(self.Y_range)+1),
                                                                scale = 50,
                                                                octaves=4,
                                                                lacunarity = 3,
                                                                seed = seed, norm = "binary")

            


        self.real_altitude_norm()

        #self.height_mask_norm(seed)

        

        self.create_world_vertex_color()

        self.render(seed)
        
        self.create_world_model(x, y, z) #x, y, z is lower left corner

        self.create_decorations(gem_spawn)
        if gem_spawn:
           self.ruby_model.ruby_draw()
        
        self.ready_decoration_to_draw(s = 0, t = 0, S = 1, T = 1)

        self.enemy = Enemy(x = random.randint(0, world_size), y = random.randint(0, world_size))
        self.enemy2 = Enemy(x = world_size/2 + 16, y = world_size/2 - 10, z = 7, w = 0.9, h = 3, file='sprites\\sprite workfile\\onua2.png')

    def ready_decoration_to_draw(self, s = .3, t = 0, S = .7, T = 1):     
        
        tex_coords = ('t2f', [s, t, S, t, S, T, s, T])

        for coord in self.decoration_model.dec_holder:
            
            label, x, y, z, w, h = coord
            if label == "grass":
                file = 'sprites\\sprite workfile\\standing grass texture.png'
            elif label == "leafy":
                file = "sprites\\sprite workfile\\leafy.png"
            

            self.sprite = self.get_texture(file)          

            x = x - w /3
            z = z - 0.15            #hides grass under ground just slightly

            X, Y, Z = x + w, y, z+h

            self.batch.add(4, GL_QUADS,self.sprite,('v3f', (x, y, z, X, y, z, X, Y, Z, x, Y, Z)),tex_coords)

            x = x + width/3
            y = y - width/4
            Y = y + width/2

            #self.batch.add(4, GL_QUADS,self.sprite,('v3f', (x, y, z, x, Y, z, x, Y, Z, x, y, Z)),tex_coords)



        
                  
    def draw(self):
        self.batch.draw()

class Decoration_Model:
    def get_texture(self, file):
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT);
        tex = pyglet.image.load(file).get_texture()
        return pyglet.graphics.TextureGroup(tex)

    def __init__(self, gem_spawn):

        self.gem_spawn = gem_spawn
        
        self.texture_max = 20
        self.dec_holder = []
        
        self.on_screen_sprites = []
        self.off_screen_sprites = []
        
        self.grass_dec_perl = []
        self.leafy_dec_perl = []


class Ruby_Model:
    def get_texture(self, file):
        tex = pyglet.image.load(file).get_texture()
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT);
        return pyglet.graphics.TextureGroup(tex)

    def __init__(self):
        self.texture_max = 10
        self.ruby_dec_perl = []
        self.ruby_dec_holder = []
        

        self.sin_const = math.sin(camera_lookdown_angle/180*math.pi)
        self.cos_const = math.cos(camera_lookdown_angle/180*math.pi)

    def ruby_draw(self):
        self.batch = pyglet.graphics.Batch()
        file = "sprites\\sprite workfile\\ruby_gem.png"
        s, S, t, T = 0,1,0,1
        tex_coords = ('t2f', [s, t, S, t, S, T, s, T])
        for ruby in self.ruby_dec_holder:
            label, x, y, z, w, h = ruby
            self.sprite = self.get_texture(file)

            x = x - w /3
            z = z + 0.15

            X, Y, Z = x + w, y + h*self.sin_const, z+h*self.cos_const

            self.batch.add(4, GL_QUADS,self.sprite,('v3f', (x, y, z, X, y, z, X, Y, Z, x, Y, Z)),tex_coords)

    def draw(self):
        self.batch.draw()

class Enemy:
    def get_texture(self, file):
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_MIRRORED_REPEAT);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_MIRRORED_REPEAT);
        tex = pyglet.image.load(file).get_texture()
        return pyglet.graphics.TextureGroup(tex)
    
    def ready_batch_to_draw(self, s = 0, t = 0, S = 1, T = 1, file='sprites\\sprite workfile\\onua.png'):
        
        self.sprite = self.get_texture(file)

        self.batch = pyglet.graphics.Batch()

        tex_coords = ('t2f', [s, t, S, t, S, T, s, T])
        x = self.x
        y = self.y
        z = self.z + 0.1
        X, Y, Z = x + self.w, self.y + self.h* math.sin(camera_lookdown_angle/180*math.pi), z+self.h*math.cos(camera_lookdown_angle/180*math.pi), 

        self.batch.add(4, GL_QUADS,self.sprite,('v3f', (x, y, z, X, y, z, X, Y, Z, x, Y, Z)),tex_coords)

    def __init__(self, x = world_size/2, y = world_size/2, z = 6, w = 2, h = 2.4, file='sprites\\sprite workfile\\onua.png'):
        self.file = file
        self.start_x = x
        self.start_y = y
        self.start_z = z

        self.osc_speed_z = random.randint(1, 4)
        self.osc_speed_y = random.randint(1, 10)
        self.osc_speed_x = random.randint(1, 10)

        self.x = self.start_x
        self.y = self.start_y
        self.z = self.start_z
        
        self.t = 0
        
        self.w = w
        self.h = h

        self.ready_batch_to_draw(file=file)

    def update(self, dt, player_x, player_y, perlin_z):
        self.t += dt
        self.z = perlin_z + 1.5+ math.sin(self.osc_speed_z*self.t)

        
        enemy_vel = .4
        if self.x > player_x + 5*math.cos(self.osc_speed_x*self.t):
            self.x -= .4
        elif self.x < player_x + 5*math.cos(self.osc_speed_x*self.t):
            self.x += .4
        if self.y > player_y + 5*math.sin(self.osc_speed_y*self.t):
            self.y -= .4
        else: self.y += .4
        
        self.ready_batch_to_draw(file = self.file)

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
    
    def __init__(self, x = -world_size,y=-world_size,z=sea_level):
        self.width = 9*max(map_size[0], map_size[1])
        self.batch = pyglet.graphics.Batch()

        self.water_tex_file = "C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python38\\Environment\\perlin noise\\0.txt"
                         
        self.x = x
        self.y = y
        self.z = z
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


