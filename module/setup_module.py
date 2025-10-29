# setup_module.py
# Handles environment setup and OpenGL configuration

from OpenGL.GL import *
from OpenGL.GLU import *

def setup_opengl():
    """Initialize OpenGL settings"""
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)
    glShadeModel(GL_SMOOTH)
    glMaterialfv(GL_FRONT, GL_SPECULAR, [1, 1, 1, 1])
    glMaterialfv(GL_FRONT, GL_SHININESS, [50])
    glClearColor(0.1, 0.1, 0.15, 1)

def setup_lighting():
    """Configure OpenGL lighting"""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, [5, 5, 5, 1])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])
