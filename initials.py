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

world_size = 80
map_size = (world_size, world_size)
fov = 30

print("size was", world_size)

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
sand_color = (200,180,100)
grass_color = (37.6, 110, 22)
dead_grass = (160,160,40)
dirt_color = (90,75,20)

render_mode = "standard"


camera_lookdown_angle = 35
camera_headroom = 5
buffer_dist = 0.5 # creates a stable range of z values where the camra or player model does not need to be moved
camera_vel = .2#.095
camera_altitude = 28
camera_distance = camera_altitude/math.tan(camera_lookdown_angle/180*math.pi)

sea_level = 0.5

player_start_pos = (world_size/2, world_size/2 - camera_distance, camera_altitude)

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
