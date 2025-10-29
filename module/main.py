# main.py
# Integrates all modules and runs the program

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import cv2
import numpy as np
from setup_module import setup_opengl, setup_lighting
from render_module import draw_camera_overlay, draw_text_overlay
from model_module import OBJLoader
from hand_tracking_module import HandTracker
from math_module import get_rotation_angles

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
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    clock = pygame.time.Clock()

    rotation_x, rotation_y, zoom = 0, 0, 0
    use_hand_tracking = True
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE: running = False
                elif event.key == K_t: use_hand_tracking = not use_hand_tracking
                elif event.key == K_r: rotation_x = rotation_y = zoom = 0

        ret, frame = cap.read()
        if ret:
            results = hand_tracker.process_frame(frame)
            frame_with_landmarks = hand_tracker.draw_landmarks(frame.copy(), results)
            if use_hand_tracking:
                rotation_x, rotation_y, zoom = get_rotation_angles(hand_tracker.hand_position)
        else:
            frame_with_landmarks = np.zeros((480, 640, 3), dtype=np.uint8)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        glTranslatef(0, 0, zoom)
        glRotatef(rotation_x, 1, 0, 0)
        glRotatef(rotation_y, 0, 1, 0)
        glColor3f(0.9, 0.8, 0.7)
        hand_model.render()
        glPopMatrix()

        draw_camera_overlay(frame_with_landmarks, display[0], display[1])
        draw_text_overlay(display[0], display[1], [f"Tracking: {use_hand_tracking}", f"FPS: {int(clock.get_fps())}"])
        pygame.display.flip()
        clock.tick(60)

    hand_tracker.cleanup()
    cap.release()
    pygame.quit()

if __name__ == "__main__":
    main()
