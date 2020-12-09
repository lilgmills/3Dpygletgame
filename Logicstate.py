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
from initials import *
from World_Model import *
from Player import *



class LogicState:
    def create_seed(self):
        x = self.island_location[0]
        y = self.island_location[1]

        return ( x**71 + y**73 + 67)%101
        
    def __init__(self):
        self.model = Model()
        
        self.player = Player()

        self.island_location = [0, 0]

        print("model array")

        seed = self.create_seed()

        random.seed(0)

        self.world_model = World_Model(seed)

        self.cull_distance = 40
        self.cull_frame_counter = 0
        self.cull_timing_skip = 60

        self.frame_counter_int = 0
        
        self.anim_frame_counter = 0
        self.anim_skip_len = 3
        self.anim_index = 0

   

    def animate_ocean(self, dt):
        self.model.redraw(dt)

    def update(self, dt, keys):
        
        
        self.player.update(dt, keys)
        #self.animate_ocean(dt)
        self.set_player_model_on_land()
        self.set_camera_follow_player()
        self.is_swimming()

##        if self.cull_frame_counter % self.cull_timing_skip == 0:
##            self.get_on_screen_sprites()
        
        if self.frame_counter_int % 5 == 0:
            self.touch_ruby()
        
        self.player.update_movement()
        self.go_off_screen()

    def touch_ruby(self):
        tmp_ruby_holder = []
        for ruby in self.world_model.decoration_model.ruby_model.ruby_dec_holder:
            label, x, y, z, w, h = ruby

            if abs(x - self.player.player_model.x) < w*3/4 and abs(y - self.player.player_model.y) < w*3/4:
                pass
            else: tmp_ruby_holder.append(ruby)

        self.world_model.decoration_model.ruby_model.ruby_dec_holder = tmp_ruby_holder
        
        self.world_model.decoration_model.ruby_model.ruby_draw()
                

    def go_off_screen(self):
        upper_bound = 1.5*world_size
        lower_bound = -(1/3)*upper_bound
        total_bound = upper_bound - lower_bound
        if self.player.player_model.x > upper_bound or self.player.player_model.x < lower_bound or self.player.player_model.y > upper_bound or self.player.player_model.y < lower_bound:
            if self.player.player_model.x > upper_bound:
                self.player.player_model.x -= total_bound
                self.player.position[0] -= total_bound
                self.island_location[0] += 1
                
                
            if self.player.player_model.x < lower_bound:
                self.player.player_model.x += total_bound
                self.player.position[0] += total_bound
                self.island_location[0] -= 1
                

            if self.player.player_model.y > upper_bound:
                self.player.player_model.y -= total_bound
                self.player.position[1] -= total_bound
                self.island_location[1] += 1
                
                
            if self.player.player_model.y < lower_bound:
                self.player.player_model.y += total_bound
                self.player.position[1] += total_bound
                self.island_location[1] -= 1
            self.player.player_model.z = -self.player.player_model.swim_depth + sea_level
                
            self.re_create_world()

    def re_create_world(self):
        seed = self.create_seed()
        
        self.world_model = World_Model(seed)
        
        

    def draw(self):
        self.model = Model(x = self.player.player_model.x - self.model.width/2, y = self.player.player_model.y - self.model.width/2)
       
        self.player.update_sprite(self.anim_index)
        
        glTranslatef(*[-x for x in self.player.position])

        glTranslatef(*[-x for x in self.player.camera_position])
       
        self.model.draw()
        self.world_model.draw()
        self.player.player_model.draw()

        self.world_model.decoration_model.draw()
        self.world_model.decoration_model.ruby_model.draw()

        self.player.position = [0,0,0]
        self.player.rotation = [0,0]
        self.player.camera_position = [0,0,0]

        self.frame_counter()

    def frame_counter(self):
        self.frame_counter_int+=1
        self.anim_frame_counter+=1
        self.cull_frame_counter +=1

        if self.anim_frame_counter == self.anim_skip_len:
            self.anim_index = (self.anim_index + 1)%4
            self.anim_frame_counter = 0

    def calculate_interpolation(self, x, y):

        ix, iy = int(round(x)), int(round(y))
        
        iX, iY = ix+1, iy+1

        if ix > 0 and iX < world_size + 1 and iy > 0 and iY < world_size+1:
            blob_hxy = self.world_model.perl_array[ix][iy]
            blob_hXy = self.world_model.perl_array[iX][iy]
            blob_hxY = self.world_model.perl_array[ix][iY]
            blob_hXY = self.world_model.perl_array[iX][iY]
            
            
            f_x = blob_hXy - blob_hxy
            f_y = blob_hxY - blob_hxy

            dx = x - ix
            dy = y - iy

        else: return 0, 0, 0, 0, self.player.player_model.swim_cutoff
            
        return f_x, f_y, dx, dy, blob_hxy

        

    def set_player_model_on_land(self):
        f_x1, f_y1, dx1, dy1, z = self.calculate_interpolation(self.player.player_model.x+.5, self.player.player_model.y)
        f_x2, f_y2, dx2, dy2, z = self.calculate_interpolation(self.player.player_model.x+.5, self.player.player_model.y)

        left_foot_z = f_x1*dx1 + f_y1*dy1 + z
        right_foot_z = f_x1*dx2 + f_y1*dy2 + z #use different dx an dy for left foot but same derivatives to hopefully reduce bounce

        new_z = max(left_foot_z, right_foot_z, self.player.player_model.swim_cutoff)
        
        if self.player.player_model.z < new_z:
            self.player.falling = False
            self.player.falling_velocity = 0
            self.player.player_model.z = new_z

        elif self.player.player_model.z > new_z and self.player.falling_velocity == 0: self.player.falling = True

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


        


        


