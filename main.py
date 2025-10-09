import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import pywavefront
import numpy as np

# ---------- Load 3D Model ----------
# Automatically loads materials/textures if .mtl file is present
scene = pywavefront.Wavefront('hand_model.obj', collect_faces=True, parse=True)

def draw_model():
    """Draw all meshes from the loaded .obj file"""
    glEnable(GL_TEXTURE_2D)
    glBegin(GL_TRIANGLES)
    for mesh in scene.mesh_list:
        for face in mesh.faces:
            for vertex_i in face:
                vertex = scene.vertices[vertex_i]
                glVertex3f(*vertex)
    glEnd()
    glDisable(GL_TEXTURE_2D)

# ---------- Lighting Setup ----------
def setup_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_NORMALIZE)

    # Light configuration
    light_position = [2.0, 2.0, 2.0, 1.0]
    ambient_light = [0.2, 0.2, 0.2, 1.0]
    diffuse_light = [0.7, 0.7, 0.7, 1.0]
    specular_light = [1.0, 1.0, 1.0, 1.0]

    # Apply light settings
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)
    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient_light)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse_light)
    glLightfv(GL_LIGHT0, GL_SPECULAR, specular_light)

    # Material reflection
    glMaterialfv(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
    glMaterialfv(GL_FRONT, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glMaterialf(GL_FRONT, GL_SHININESS, 50.0)

# ---------- Main Program ----------
def main():
    pygame.init()
    display = (1000, 700)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("3D Hand Model Viewer - Pygame + OpenGL")

    # Camera setup
    gluPerspective(45, (display[0] / display[1]), 0.1, 100.0)
    glTranslatef(0.0, 0.0, -5)
    glScalef(0.01, 0.01, 0.01)  # Scale down large Blender exports

    glEnable(GL_DEPTH_TEST)
    setup_lighting()
    glShadeModel(GL_SMOOTH)

    # Mouse interaction setup
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    x_rot, y_rot = 0, 0
    zoom = -5
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 4:  # scroll up
                    zoom += 0.5
                elif event.button == 5:  # scroll down
                    zoom -= 0.5

        # Keyboard controls
        keys = pygame.key.get_pressed()
        if keys[K_ESCAPE]:
            running = False
        if keys[K_LEFT]:
            y_rot -= 2
        if keys[K_RIGHT]:
            y_rot += 2
        if keys[K_UP]:
            x_rot -= 2
        if keys[K_DOWN]:
            x_rot += 2

        # Mouse control
        mouse_rel = pygame.mouse.get_rel()
        if pygame.mouse.get_pressed()[0]:
            x_rot += mouse_rel[1] * 0.5
            y_rot += mouse_rel[0] * 0.5

        # Clear and draw
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, zoom)
        glRotatef(x_rot, 1, 0, 0)
        glRotatef(y_rot, 0, 1, 0)

        draw_model()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()