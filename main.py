import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import cv2
import mediapipe as mp

class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.hand_position = [0.5, 0.5, 0]
        
    def process_frame(self, frame):
        """Process frame and return hand tracking results"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)
        
        # Update hand position
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            # Use palm center (approximately landmark 9)
            palm = hand_landmarks.landmark[9]
            self.hand_position = [palm.x, palm.y, palm.z]
        
        return results
    
    def draw_landmarks(self, frame, results):
        """Draw hand landmarks on frame"""
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                    self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    self.mp_draw.DrawingSpec(color=(255, 0, 0), thickness=2)
                )
        return frame
    
    def get_rotation_angles(self):
        """Convert hand position to rotation angles"""
        # Map hand position (0-1) to rotation angles
        rotation_y = (self.hand_position[0] - 0.5) * 360  # -180 to 180
        rotation_x = (self.hand_position[1] - 0.5) * 360  # -180 to 180
        zoom = self.hand_position[2] * -10  # Use Z for zoom
        return rotation_x, rotation_y, zoom
    
    def cleanup(self):
        self.hands.close()

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

def draw_camera_overlay(frame, width, height, cam_width=320, cam_height=240):
    """Draw camera feed in bottom right corner"""
    # Resize frame
    frame_small = cv2.resize(frame, (cam_width, cam_height))
    frame_rgb = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
    frame_flipped = cv2.flip(frame_rgb, 0)  # Flip vertically for OpenGL
    
    # Switch to 2D orthographic projection
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Disable depth test and lighting for 2D overlay
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    # Draw semi-transparent background
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0, 0, 0, 0.3)
    glBegin(GL_QUADS)
    glVertex2f(width - cam_width - 20, 10)
    glVertex2f(width - 10, 10)
    glVertex2f(width - 10, cam_height + 20)
    glVertex2f(width - cam_width - 20, cam_height + 20)
    glEnd()
    
    # Draw camera feed
    texture_data = frame_flipped.tobytes()
    glRasterPos2f(width - cam_width - 15, 15)
    glDrawPixels(cam_width, cam_height, GL_RGB, GL_UNSIGNED_BYTE, texture_data)
    
    glDisable(GL_BLEND)
    
    # Re-enable depth test and lighting
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    # Restore 3D projection
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

def draw_text_overlay(width, height, text_lines):
    """Draw text information on screen"""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)
    
    # Render text using pygame font
    font = pygame.font.SysFont('Arial', 18)
    y_offset = height - 30
    
    for text in text_lines:
        text_surface = font.render(text, True, (255, 255, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glRasterPos2f(10, y_offset)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                    GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        y_offset -= 25
    
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

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
    pygame.display.set_caption("3D Hand Model with Hand Tracking")
    
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
    
    # Initialize hand tracker
    hand_tracker = HandTracker()
    
    # Initialize webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    if not cap.isOpened():
        print("Error: Could not open webcam")
        pygame.quit()
        return
    
    # Rotation angles
    rotation_x = 0
    rotation_y = 0
    zoom = 0
    
    # Control mode
    use_hand_tracking = True
    
    # Mouse control
    mouse_down = False
    last_mouse_pos = None
    
    clock = pygame.time.Clock()
    running = True
    
    print("\nControls:")
    print("- T: Toggle hand tracking / mouse control")
    print("- Left Mouse: Rotate model (when hand tracking off)")
    print("- Mouse Wheel: Zoom in/out")
    print("- R: Reset view")
    print("- ESC: Exit")
    print("\nHand Tracking Active - Move your hand to control the model!")
    
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
                elif event.key == pygame.K_t:
                    # Toggle hand tracking
                    use_hand_tracking = not use_hand_tracking
                    print(f"Hand tracking: {'ON' if use_hand_tracking else 'OFF'}")
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
                if mouse_down and last_mouse_pos and not use_hand_tracking:
                    mouse_pos = pygame.mouse.get_pos()
                    dx = mouse_pos[0] - last_mouse_pos[0]
                    dy = mouse_pos[1] - last_mouse_pos[1]
                    rotation_y += dx * 0.5
                    rotation_x += dy * 0.5
                    last_mouse_pos = mouse_pos
        
        # Capture and process webcam frame
        ret, frame = cap.read()
        if ret:
            # Process hand tracking
            results = hand_tracker.process_frame(frame)
            frame_with_landmarks = hand_tracker.draw_landmarks(frame.copy(), results)
            
            # Update rotation based on hand tracking
            if use_hand_tracking:
                track_x, track_y, track_z = hand_tracker.get_rotation_angles()
                rotation_x = track_x
                rotation_y = track_y
                zoom = track_z
        else:
            frame_with_landmarks = np.zeros((480, 640, 3), dtype=np.uint8)
        
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
        
        # Draw camera overlay
        draw_camera_overlay(frame_with_landmarks, display[0], display[1])
        
        # Draw info text
        info_text = [
            f"Mode: {'Hand Tracking' if use_hand_tracking else 'Mouse Control'}",
            f"FPS: {int(clock.get_fps())}",
            "Press T to toggle mode"
        ]
        draw_text_overlay(display[0], display[1], info_text)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)
    
    # Cleanup
    hand_tracker.cleanup()
    cap.release()
    pygame.quit()

if __name__ == "__main__":
    # Required installations:
    # pip install pygame PyOpenGL opencv-python mediapipe numpy
    main()