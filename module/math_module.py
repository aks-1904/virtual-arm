# math_module.py
# Handles mathematical mapping from hand movement to model rotation

def get_rotation_angles(hand_position):
    rotation_y = (hand_position[0] - 0.5) * 360
    rotation_x = (hand_position[1] - 0.5) * 360
    zoom = hand_position[2] * -10
    return rotation_x, rotation_y, zoom
