import sys, os
import numpy as np
import math
from PIL import Image
import tkinter as tk
from tkinter import filedialog
import pyglet
from pyglet.gl import *
from Logicstate import *

def main():
    window = Window(width = size[0], height =size[1], caption = "Wizard", resizable=True)
    glClearColor(0.6,0.71,1,1)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    #glEnable(GL_BLEND)
    #glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_ALPHA_TEST);
    glAlphaFunc(GL_GREATER,0.5)
    pyglet.app.run()
    #main_guy = Player()
    #State = 25DLogState(main_guy, screen)

    
        
if __name__ == "__main__":
    main()
