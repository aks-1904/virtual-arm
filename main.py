# main.py
# Integrates all modules and runs the program

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import cv2
import numpy as np
from module.setup_module import setup_opengl, setup_lighting
from module.render_module import draw_camera_overlay, draw_text_overlay
from module.model_module import OBJLoader
from module.hand_tracking_module import HandTracker
from module.math_module import get_rotation_angles

def main():
    pygame.init()
    display = (1200, 800)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("3D Hand Model with Tracking")

    gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)

    setup_opengl()
    setup_lighting()

    hand_model = OBJLoader('hand_model.obj')
    hand_tracker = HandTracker()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video capture.")
        return
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    clock = pygame.time.Clock()

    rotation_x, rotation_y, zoom = 0, 0, 0
    use_hand_tracking = True
    running = True
    
    # Variables for mouse control
    mouse_dragging = False
    last_mouse_pos = (0, 0)
    zoom_speed = 0.5  # Controls zoom sensitivity
    rotate_speed = 0.5 # Controls rotation sensitivity

    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE or event.key == K_q: # Quit on 'q' or 'ESC'
                    running = False
                elif event.key == K_t: # Toggle tracking
                    use_hand_tracking = not use_hand_tracking
                    print(f"Hand tracking: {use_hand_tracking}")
                elif event.key == K_r: # Reset view
                    rotation_x = rotation_y = zoom = 0

            # --- Mouse controls (only if hand tracking is off) ---
            if not use_hand_tracking:
                mods = pygame.key.get_mods()
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 1 and (mods & KMOD_CTRL): # Ctrl + Left Click
                        mouse_dragging = True
                        last_mouse_pos = event.pos
                    elif (mods & KMOD_CTRL): # Ctrl + Scroll
                        if event.button == 4: # Scroll Up
                            zoom -= zoom_speed
                        elif event.button == 5: # Scroll Down
                            zoom += zoom_speed
                            
                elif event.type == MOUSEBUTTONUP:
                    if event.button == 1:
                        mouse_dragging = False
                        
                elif event.type == MOUSEMOTION:
                    if mouse_dragging:
                        dx = event.pos[0] - last_mouse_pos[0]
                        dy = event.pos[1] - last_mouse_pos[1]
                        rotation_y += dx * rotate_speed
                        rotation_x += dy * rotate_speed
                        last_mouse_pos = event.pos

        # --- Hand Tracking Logic ---
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hand_tracker.process_frame(frame_rgb)
            frame_with_landmarks = hand_tracker.draw_landmarks(frame.copy(), results)
            
            if use_hand_tracking and results.multi_hand_landmarks:
                # Update rotation/zoom based on hand position
                rotation_x, rotation_y, zoom = get_rotation_angles(hand_tracker.hand_position)
        else:
            # Show a black screen if camera fails
            frame_with_landmarks = np.zeros((480, 640, 3), dtype=np.uint8)

        # --- 3D Rendering ---
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        
        # Apply zoom and rotation
        glTranslatef(0, 0, zoom)
        glRotatef(rotation_x, 1, 0, 0)
        glRotatef(rotation_y, 0, 1, 0)
        
        # Render model
        glColor3f(0.9, 0.8, 0.7) # Hand color
        hand_model.render()
        
        glPopMatrix()

        # --- 2D Overlay Rendering ---
        mode_text = "Tracking: ON (Hand)" if use_hand_tracking else "Tracking: OFF (Mouse/KB)"
        draw_camera_overlay(frame_with_landmarks, display[0], display[1])
        draw_text_overlay(display[0], display[1], [
            mode_text,
            f"FPS: {int(clock.get_fps())}",
            "Controls:",
            " 'T' - Toggle Mode",
            " 'Q' - Quit",
            " 'R' - Reset View",
            " Ctrl+Drag - Rotate",
            " Ctrl+Scroll - Zoom"
        ])
        
        pygame.display.flip()
        clock.tick(60) # Limit to 60 FPS

    # --- Cleanup ---
    hand_tracker.cleanup()
    cap.release()
    pygame.quit()

if __name__ == "__main__":
    main()
    