import random
import pygame
from pygame.math import Vector2
from typing import List

RED = (225, 0, 0)
BLUE = (0, 102, 255)
GREEN = (0, 204, 0)
YELLOW = (255, 204, 0)
colors = [BLUE, RED, GREEN, YELLOW]


directions_vectors = {(0, -1): "UP", (1, 0): "RIGHT", (0, 1): "DOWN", (-1, 0): "LEFT"}
directions = ["LEFT", "DOWN", "UP", "RIGHT"]


def reset_arrows():
    global directions
    directions = ["LEFT", "DOWN", "UP", "RIGHT"]


def update_arrow_directions(vectors: List[Vector2]):
    """
    Converts the vector list into a string list for the UI,
    making sure to use integers for the dictionary lookup.
    """
    global directions
    try:
        directions = [directions_vectors[(int(v.x), int(v.y))] for v in vectors]
    except KeyError as e:
        print(f"Error: A vector direction was passed that is not in the dictionary: {e}")
        directions = ["LEFT", "DOWN", "UP", "RIGHT"]


def draw_direction_buttons(screen, screen_width, screen_height, cell_size):
    margin_height = cell_size * 2
    margin_rect = pygame.Rect(
        0, screen_height - margin_height, screen_width, margin_height
    )
    pygame.draw.rect(screen, (0, 0, 0), margin_rect)

    button_width = screen_width // 4
    button_height = margin_height - 10  # Etwas Abstand zum oberen Rand

    for i in range(4):
        x = i * button_width + 5
        y = screen_height - button_height - 5
        rect = pygame.Rect(x, y, button_width - 10, button_height)
        pygame.draw.rect(screen, colors[i], rect, border_radius=10)
        arrow_color = (255, 255, 255)
        cx, cy = rect.center
        size = cell_size * 0.6
        
        if directions[i] == "LEFT":
            points = [
                (cx - size, cy),  # left tip
                (cx + size, cy - size),  # top right
                (cx + size, cy + size),  # bottom right
            ]
        elif directions[i] == "UP":
            points = [
                (cx, cy - size),  # top tip
                (cx - size, cy + size),  # bottom left
                (cx + size, cy + size),  # bottom right
            ]
        elif directions[i] == "DOWN":
            points = [
                (cx, cy + size),  # bottom tip
                (cx - size, cy - size),  # top left
                (cx + size, cy - size),  # top right
            ]
        elif directions[i] == "RIGHT":
            points = [
                (cx + size, cy),  # right tip
                (cx - size, cy - size),  # top left
                (cx - size, cy + size),  # bottom left
            ]
        pygame.draw.polygon(screen, arrow_color, points)
