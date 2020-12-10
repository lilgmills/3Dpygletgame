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

        y = y - (self.player_height*math.cos(camera_lookdown_angle/180*math.pi))/2
        z = z + 0.1
        X, Y, Z = x + self.player_width, y + self.player_height* math.sin(camera_lookdown_angle/180*math.pi), z+self.player_height*math.cos(camera_lookdown_angle/180*math.pi), 

        self.batch.add(4, GL_QUADS,self.sprite,('v3f', (x, y, z, X, y, z, X, Y, Z, x, Y, Z)),tex_coords)

    def __init__(self, x = player_start_pos[0], y = player_start_pos[1] + camera_distance, z = 0):
        
        self.x = x
        self.y = y
        self.z = z

        self.player_width = 0.7
        self.player_height = 1.2*self.player_width

        self.swim_depth = 0.55 *self.player_height* math.cos(camera_lookdown_angle/180*math.pi)
        self.foot_room = 0.1 *self.player_height* math.cos(camera_lookdown_angle/180*math.pi)

        self.swim_cutoff = sea_level - self.swim_depth - self.foot_room
        
    def draw(self):
        self.batch.draw()

class Player:
    def __init__(self):
        self.position = [0,0,0]
        self.camera_position = [0,0,0]
    
        self.rotation = [0,0] #the "player" position is always zero (because we are always at the center of our world)
        self.world_coords = list(player_start_pos[:])
        self.world_rot = [0, -camera_lookdown_angle]

        self.velocity_matrix = walking_velocity
        self.velocity = [0,0,0]

        self.player_model = Player_Model()
        self.direction = UP
        self.swim_state = False
        self.falling = True
        self.on_land = False
        self.jumping = False

        self.moving = None
        self.speedup = None
        self.slowdown = None

        self.was_moving = None

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
        return abs(self.velocity_matrix[0][0])

    def update_movement(self):
                
        if self.moving is not None:
                            
            if self.swim_state:
                self.update_position(swimming_velocity, self.moving)
            else:
                self.update_position(self.velocity_matrix, self.moving)
            if self.vel_norm() < .17:
                vel_norm = .004
                self.update_velocity(vel_norm)
                
        elif self.was_moving is not None and self.vel_norm() > 0:
            vel_norm = -.0045
            self.update_velocity(vel_norm)
            self.update_position(self.velocity_matrix, self.was_moving)

            if self.vel_norm() < 0.01:
                self.was_moving = None
                self.velocity_matrix = walking_velocity
            

        if self.jumping:
            self.falling_velocity = .16*self.player_model.player_height
            self.jumping = False
            self.falling = True

        if self.falling:
            self.fall()
            self.update_vertical(self.falling_velocity)
        
    def update_sprite(self, anim_index):
        if (self.moving is not None or self.was_moving is not None) and not self.swim_state:
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
        self.falling_velocity += -.007

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

        if self.moving is not None: self.was_moving = self.moving

        

