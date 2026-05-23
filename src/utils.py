# Utility functions for math, camera, and UI drawing
import pygame
import math
from src.config import TILE_SIZE

# Font cache to avoid loading fonts repeatedly
_font_cache = {}

def get_font(name, size):
    """Retrieves or creates a pygame Font of specific size."""
    key = (name, size)
    if key not in _font_cache:
        try:
            _font_cache[key] = pygame.font.SysFont(name, size)
        except:
            _font_cache[key] = pygame.font.Font(None, size)
    return _font_cache[key]

def draw_text(surface, text, x, y, size=18, color=(230, 230, 240), font_name="Consolas", align="left"):
    """Helper to draw text easily with font caching and alignments."""
    font = get_font(font_name, size)
    text_surf = font.render(str(text), True, color)
    rect = text_surf.get_rect()
    if align == "left":
        rect.topleft = (x, y)
    elif align == "center":
        rect.center = (x, y)
    elif align == "right":
        rect.topright = (x, y)
    surface.blit(text_surf, rect)
    return rect

def draw_rounded_rect(surface, rect, color, radius=10, border_color=None, border_width=1):
    """Draws a premium rounded rectangle with optional transparent borders."""
    rect = pygame.Rect(rect)
    shape_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    
    # Fill main body
    pygame.draw.rect(shape_surf, color, (0, 0, rect.width, rect.height), border_radius=radius)
    
    # Border
    if border_color:
        pygame.draw.rect(shape_surf, border_color, (0, 0, rect.width, rect.height), width=border_width, border_radius=radius)
        
    surface.blit(shape_surf, rect.topleft)

def world_to_screen(world_x, world_y, camera_x, camera_y):
    """Converts grid-based tile coordinates into actual screen pixels based on camera offset."""
    screen_x = int(world_x * TILE_SIZE - camera_x)
    screen_y = int(world_y * TILE_SIZE - camera_y)
    return screen_x, screen_y

def screen_to_world(screen_x, screen_y, camera_x, camera_y):
    """Converts screen pixel coordinates into world grid tile coordinates."""
    world_x = int((screen_x + camera_x) / TILE_SIZE)
    world_y = int((screen_y + camera_y) / TILE_SIZE)
    return world_x, world_y

def distance(x1, y1, x2, y2):
    """Standard Euclidean distance."""
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

def distance_manhattan(x1, y1, x2, y2):
    """Manhattan distance."""
    return abs(x1 - x2) + abs(y1 - y2)
