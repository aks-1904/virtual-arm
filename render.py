import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import os
import sys

class OBJLoader:
    def __init__(self, filename):
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.load_obj(filename)
    
    def load_obj(self, filename):
        """Load OBJ file and parse vertices, normals, and faces"""
        # Check if file exists
        if not os.path.exists(filename):
            print(f"ERROR: Cannot find '{filename}'")
            print(f"Current directory: {os.getcwd()}")
            print(f"Looking for file at: {os.path.abspath(filename)}")
            sys.exit(1)
        
        print(f"Loading model from: {filename}")
        
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                values = line.split()
                if not values:
                    continue
                
                if values[0] == 'v':
                    # Vertex coordinates
                    self.vertices.append([float(x) for x in values[1:4]])
                elif values[0] == 'vn':
                    # Vertex normals
                    self.normals.append([float(x) for x in values[1:4]])
                elif values[0] == 'vt':
                    # Texture coordinates
                    self.texcoords.append([float(x) for x in values[1:3]])
                elif values[0] == 'f':
                    # Faces
                    face = []
                    for v in values[1:]:
                        w = v.split('/')
                        face.append([int(w[0]) if w[0] else 0,
                                   int(w[1]) if len(w) > 1 and w[1] else 0,
                                   int(w[2]) if len(w) > 2 and w[2] else 0])
                    self.faces.append(face)
        
        print(f"✓ Successfully loaded: {len(self.vertices)} vertices, {len(self.faces)} faces")
        
        # Auto-calculate normals if not present in OBJ
        if not self.normals and self.faces:
            print("Calculating normals...")
            self.calculate_normals()
    
    def calculate_normals(self):
        """Calculate normals for smooth shading"""
        self.normals = [[0.0, 0.0, 0.0] for _ in self.vertices]
        
        for face in self.faces:
            if len(face) >= 3:
                v1 = np.array(self.vertices[face[0][0] - 1])
                v2 = np.array(self.vertices[face[1][0] - 1])
                v3 = np.array(self.vertices[face[2][0] - 1])
                
                normal = np.cross(v2 - v1, v3 - v1)
                normal = normal / (np.linalg.norm(normal) + 1e-10)
                
                for vertex in face:
                    idx = vertex[0] - 1
                    self.normals[idx] = (np.array(self.normals[idx]) + normal).tolist()
        
        # Normalize all normals
        for i in range(len(self.normals)):
            n = np.array(self.normals[i])
            norm = np.linalg.norm(n)
            if norm > 0:
                self.normals[i] = (n / norm).tolist()
    
    def render(self):
        """Render the 3D model"""
        glBegin(GL_TRIANGLES)
        for face in self.faces:
            for vertex in face:
                # Use calculated or loaded normals
                if self.normals:
                    if vertex[2] and vertex[2] <= len(self.normals):
                        glNormal3fv(self.normals[vertex[2] - 1])
                    elif vertex[0] <= len(self.normals):
                        glNormal3fv(self.normals[vertex[0] - 1])
                
                if vertex[0]:
                    glVertex3fv(self.vertices[vertex[0] - 1])
        glEnd()

def setup_lighting():
    """Configure OpenGL lighting"""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    # Light position (top-right-front)
    glLightfv(GL_LIGHT0, GL_POSITION, [5, 5, 5, 1])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])

def setup_opengl():
    """Initialize OpenGL settings"""
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)
    glShadeModel(GL_SMOOTH)
    
    # Material properties
    glMaterialfv(GL_FRONT, GL_SPECULAR, [1, 1, 1, 1])
    glMaterialfv(GL_FRONT, GL_SHININESS, [50])
    
    # Background color (dark blue-gray)
    glClearColor(0.1, 0.1, 0.15, 1)

def main():
    print("=" * 50)
    print("3D HAND MODEL VIEWER")
    print("=" * 50)
    
    # Initialize Pygame
    pygame.init()
    display = (1200, 800)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("3D Hand Model Viewer - hand_model.obj")
    
    # Setup perspective
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)
    
    # Setup OpenGL
    setup_opengl()
    setup_lighting()
    
    # Load the hand model - AUTOMATICALLY RUNS ON STARTUP
    hand_model = OBJLoader('hand_model.obj')
    
    # Rotation angles
    rotation_x = 0
    rotation_y = 0
    zoom = 0
    auto_rotate = False
    
    # Mouse control
    mouse_down = False
    last_mouse_pos = None
    
    clock = pygame.time.Clock()
    running = True
    
    print("\n" + "=" * 50)
    print("CONTROLS:")
    print("=" * 50)
    print("• Left Mouse Drag: Rotate model")
    print("• Mouse Wheel: Zoom in/out")
    print("• SPACE: Toggle auto-rotation")
    print("• R: Reset view")
    print("• ESC: Exit")
    print("=" * 50 + "\n")
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # Reset view
                    rotation_x, rotation_y = 0, 0
                    zoom = 0
                    auto_rotate = False
                    glLoadIdentity()
                    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
                    glTranslatef(0.0, 0.0, -5)
                    print("View reset")
                elif event.key == pygame.K_SPACE:
                    auto_rotate = not auto_rotate
                    print(f"Auto-rotation: {'ON' if auto_rotate else 'OFF'}")
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_down = True
                    last_mouse_pos = pygame.mouse.get_pos()
                elif event.button == 4:  # Scroll up
                    zoom += 0.5
                elif event.button == 5:  # Scroll down
                    zoom -= 0.5
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_down = False
            elif event.type == pygame.MOUSEMOTION:
                if mouse_down and last_mouse_pos:
                    mouse_pos = pygame.mouse.get_pos()
                    dx = mouse_pos[0] - last_mouse_pos[0]
                    dy = mouse_pos[1] - last_mouse_pos[1]
                    rotation_y += dx * 0.5
                    rotation_x += dy * 0.5
                    last_mouse_pos = mouse_pos
        
        # Auto-rotation
        if auto_rotate:
            rotation_y += 0.5
        
        # Clear screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Apply transformations
        glPushMatrix()
        glTranslatef(0, 0, zoom)
        glRotatef(rotation_x, 1, 0, 0)
        glRotatef(rotation_y, 0, 1, 0)
        
        # Set model color (skin-like)
        glColor3f(0.9, 0.8, 0.7)
        
        # Render the hand model
        hand_model.render()
        
        glPopMatrix()
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    print("\nClosing viewer...")
    pygame.quit()
    print("Done!")

if __name__ == "__main__":
    main()