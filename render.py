import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

class OBJLoader:
    def __init__(self, filename):
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        self.vbo_vertices = None
        self.vbo_normals = None
        self.vertex_count = 0
        self.load_obj(filename)
        self.create_vbo()
    
    def load_obj(self, filename):
        """Load OBJ file and parse vertices, normals, and faces"""
        try:
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
            
            print(f"Loaded {len(self.vertices)} vertices, {len(self.faces)} faces")
        except FileNotFoundError:
            print(f"Error: Could not find {filename}")
            raise
    
    def create_vbo(self):
        """Create Vertex Buffer Objects for efficient rendering"""
        print("Creating VBOs for efficient rendering...")
        
        # Flatten vertices and normals for each face
        vertex_data = []
        normal_data = []
        
        for face in self.faces:
            for vertex in face:
                if vertex[0]:
                    vertex_data.extend(self.vertices[vertex[0] - 1])
                else:
                    vertex_data.extend([0, 0, 0])
                
                if vertex[2] and self.normals:
                    normal_data.extend(self.normals[vertex[2] - 1])
                else:
                    normal_data.extend([0, 0, 1])  # Default normal
        
        self.vertex_count = len(vertex_data) // 3
        
        # Convert to numpy arrays
        vertex_array = np.array(vertex_data, dtype=np.float32)
        normal_array = np.array(normal_data, dtype=np.float32)
        
        # Create VBOs
        self.vbo_vertices = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glBufferData(GL_ARRAY_BUFFER, vertex_array.nbytes, vertex_array, GL_STATIC_DRAW)
        
        self.vbo_normals = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_normals)
        glBufferData(GL_ARRAY_BUFFER, normal_array.nbytes, normal_array, GL_STATIC_DRAW)
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        
        print(f"VBOs created with {self.vertex_count} vertices")
    
    def render(self):
        """Render the 3D model using VBOs"""
        if self.vbo_vertices is None:
            return
        
        # Enable client states
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        
        # Bind and draw vertices
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_vertices)
        glVertexPointer(3, GL_FLOAT, 0, None)
        
        # Bind and draw normals
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_normals)
        glNormalPointer(GL_FLOAT, 0, None)
        
        # Draw all triangles
        glDrawArrays(GL_TRIANGLES, 0, self.vertex_count)
        
        # Cleanup
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)
    
    def __del__(self):
        """Cleanup VBOs"""
        if self.vbo_vertices:
            glDeleteBuffers(1, [self.vbo_vertices])
        if self.vbo_normals:
            glDeleteBuffers(1, [self.vbo_normals])

def setup_lighting():
    """Configure OpenGL lighting"""
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    # Light position
    glLightfv(GL_LIGHT0, GL_POSITION, [5, 5, 5, 1])
    # Ambient light
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1])
    # Diffuse light
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
    # Specular light
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1, 1, 1, 1])

def setup_opengl():
    """Initialize OpenGL settings"""
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)
    glShadeModel(GL_SMOOTH)
    
    # Material properties
    glMaterialfv(GL_FRONT, GL_SPECULAR, [1, 1, 1, 1])
    glMaterialfv(GL_FRONT, GL_SHININESS, [50])
    
    # Background color
    glClearColor(0.1, 0.1, 0.15, 1)

def main():
    # Initialize Pygame
    pygame.init()
    display = (1200, 800)
    print(pygame.display.get_driver())
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("3D Hand Model Viewer")
    
    # Setup perspective
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)
    
    # Setup OpenGL
    setup_opengl()
    setup_lighting()
    
    # Load the hand model
    try:
        hand_model = OBJLoader('hand_model.obj')
    except FileNotFoundError:
        print("Please make sure 'hand_model.obj' is in the same directory as this script")
        pygame.quit()
        return
    
    # Rotation angles
    rotation_x = 0
    rotation_y = 0
    zoom = 0
    
    # Mouse control
    mouse_down = False
    last_mouse_pos = None
    
    clock = pygame.time.Clock()
    running = True
    
    print("\nControls:")
    print("- Left Mouse: Rotate model")
    print("- Mouse Wheel: Zoom in/out")
    print("- R: Reset view")
    print("- ESC: Exit")
    print("\nRendering...")
    
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
                    glLoadIdentity()
                    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
                    glTranslatef(0.0, 0.0, -5)
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
        
        # Clear screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Apply transformations
        glPushMatrix()
        glTranslatef(0, 0, zoom)
        glRotatef(rotation_x, 1, 0, 0)
        glRotatef(rotation_y, 0, 1, 0)
        
        # Set model color
        glColor3f(0.9, 0.8, 0.7)  # Skin-like color
        
        # Render the hand model
        hand_model.render()
        
        glPopMatrix()
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()