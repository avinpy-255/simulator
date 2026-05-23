# Configuration constants for Nexus: Neural Survival Sandbox

# Window Settings
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60

# Simulation Grid Settings
GRID_WIDTH = 3200
GRID_HEIGHT = 3200
CHUNK_SIZE = 32  # 32x32 tiles per chunk
TILE_SIZE = 24   # Render size of a tile in pixels

# Offscreen chunk updates throttle (number of frames between updates)
OFFSCREEN_UPDATE_INTERVAL = 120  # ~2 seconds at 60fps

# Presets
PRESET_DEFAULT = "default"
PRESET_NUCLEAR = "nuclear"
PRESET_ZOMBIE = "zombie"
PRESET_NO_SUN = "no_sun"
PRESET_NO_HUMANS = "no_humans"
PRESET_NO_ANIMALS = "no_animals"

# Tile Types
TILE_VOID = 0
TILE_GRASS = 1
TILE_DIRT = 2
TILE_WATER = 3
TILE_WALL = 4
TILE_WASTELAND = 5  # Radioactive soil
TILE_FLOOR = 6
TILE_ROAD = 7

# Premium Color Palette (RGB/RGBA)
# Using curated dark-mode theme colors instead of raw primary colors
COLORS = {
    # Tiles
    TILE_VOID: (10, 10, 12),
    TILE_GRASS: (34, 59, 39),      # Moss green
    TILE_DIRT: (89, 72, 60),       # Warm dirt brown
    TILE_WATER: (26, 73, 92),      # Deep ocean blue
    TILE_WALL: (48, 51, 56),       # Slate gray
    TILE_WASTELAND: (99, 107, 49), # Radioactive olive
    TILE_FLOOR: (28, 30, 33),      # Dark concrete
    TILE_ROAD: (60, 62, 66),       # Asphalt gray

    # Entities
    "human": (77, 179, 255),       # Cyan-blue
    "zombie": (90, 160, 90),       # Rotten green
    "animal": (217, 125, 75),      # Soft copper orange
    "android": (255, 77, 240),     # Vibrant cyber magenta
    "charger": (255, 215, 0),      # Power / Gold
    "food": (230, 80, 80),         # Food / Red
    "wolf": (150, 75, 0),          # Predator brown
    "beacon": (0, 255, 255),       # Neon Cyan
    
    # UI Design System - Classic CRT terminal style
    "ui_bg": (10, 15, 10, 240),         # Dark green-black screen
    "ui_border": (0, 200, 0, 255),      # Solid phosphor green border
    "ui_text": (50, 255, 50),           # Phosphor green text
    "ui_text_dim": (35, 175, 35),       # Muted green text
    "ui_accent": (255, 165, 0),         # Alert Amber
    "ui_button": (15, 35, 15, 255),     # Deep green button
    "ui_button_hover": (25, 60, 25, 255), # Active green on hover
    "ui_button_active": (255, 165, 0, 100),
    "reward_green": (50, 255, 50),      # Match terminal theme
    "punish_red": (255, 50, 50),        # Alert Red
    
    # Environment Effects
    "ambient_darkness": (5, 5, 8),      # Base dark color for Without Sun mode
    "radiation_glow": (57, 255, 20, 30) # Neon green overlay for radioactive chunks (RGBA)
}

# UI Layout Configurations
SIDEBAR_WIDTH = 340
BOTTOM_PANEL_HEIGHT = 160

# Simulation Parameters
STARTING_HUMANS = 40
STARTING_ANIMALS = 40
STARTING_ZOMBIES = 10
STARTING_ANDROIDS = 1
STARTING_CHARGERS = 15
STARTING_FOOD = 30
STARTING_WOLVES = 8

# Expanded Simulation Rates
FLASHLIGHT_DECAY_RATE = 0.05       # Flashlight drain per frame
GRASS_REGROW_CHANCE = 0.001        # Chance per frame for dirt -> grass
ZOMBIE_WALL_DAMAGE_RATE = 0.4      # Damage dealt to Wall tiles per frame
ANIMAL_BREED_THRESHOLD = 80.0      # Energy required for mating

