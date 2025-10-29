# render_module.py
# Contains functions for drawing overlays and text on the screen

import pygame
from OpenGL.GL import *
import cv2

def draw_camera_overlay(frame, width, height, cam_width=320, cam_height=240):
    """Draw camera feed in bottom-right corner"""
    frame_small = cv2.resize(frame, (cam_width, cam_height))
    frame_rgb = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)
    frame_flipped = cv2.flip(frame_rgb, 0) # Flip vertically for OpenGL

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
    """Render text information using Pygame"""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)

    # *** ADDED for transparency ***
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Render text using pygame font
    font = pygame.font.SysFont('Arial', 18)
    y_offset = height - 30

    for text in text_lines:
        text_surface = font.render(text, True, (255, 255, 255)) # White text
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glRasterPos2f(10, y_offset)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                    GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        y_offset -= 25
    
    # *** ADDED to disable blend after use ***
    glDisable(GL_BLEND)

    # Re-enable depth test and lighting
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    
    # Restore 3D projection
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()