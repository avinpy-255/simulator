# Chunk-Based World Engine for Nexus
import numpy as np
import random
import math
from src.config import (
    GRID_WIDTH, GRID_HEIGHT, CHUNK_SIZE,
    TILE_GRASS, TILE_DIRT, TILE_WATER, TILE_WALL, TILE_WASTELAND, TILE_FLOOR,
    PRESET_DEFAULT, PRESET_NUCLEAR, PRESET_ZOMBIE, PRESET_NO_SUN, PRESET_NO_HUMANS, PRESET_NO_ANIMALS,
    GRASS_REGROW_CHANCE
)

class Chunk:
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        
        # 32x32 grid arrays
        self.tiles = np.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=np.uint8)
        self.radiation = np.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=np.float32)
        self.light = np.ones((CHUNK_SIZE, CHUNK_SIZE), dtype=np.float32) * 100.0  # Default full light
        
        # Procedural generation
        self.generate_terrain()

    def generate_terrain(self):
        """Generates tiles using procedural mathematical noise."""
        world_x_offset = self.cx * CHUNK_SIZE
        world_y_offset = self.cy * CHUNK_SIZE
        
        for x in range(CHUNK_SIZE):
            wx = world_x_offset + x
            for y in range(CHUNK_SIZE):
                wy = world_y_offset + y
                
                # Combine multiple sine waves to simulate 2D noise
                val = (
                    math.sin(wx * 0.05) * math.cos(wy * 0.05) * 0.4 +
                    math.sin(wx * 0.15) * math.sin(wy * 0.15) * 0.2 +
                    math.sin(wx * 0.01) * math.cos(wy * 0.01) * 0.4
                )
                
                # Assign tiles based on noise values
                if val < -0.35:
                    self.tiles[x, y] = TILE_WATER
                elif val > 0.45:
                    self.tiles[x, y] = TILE_WALL
                elif val > 0.25:
                    self.tiles[x, y] = TILE_DIRT
                else:
                    self.tiles[x, y] = TILE_GRASS
                    
                # Occasional concrete ruins structure
                if 0.1 < val < 0.13 and wx % 16 == 0 and wy % 16 == 0:
                    # Draw a small 4x4 room/floor
                    for dx in range(4):
                        for dy in range(4):
                            rx, ry = x + dx, y + dy
                            if rx < CHUNK_SIZE and ry < CHUNK_SIZE:
                                if dx == 0 or dx == 3 or dy == 0 or dy == 3:
                                    # Create walls with doors
                                    if not (dx == 2 and dy == 0):
                                        self.tiles[rx, ry] = TILE_WALL
                                else:
                                    self.tiles[rx, ry] = TILE_FLOOR

class World:
    def __init__(self, preset=PRESET_DEFAULT):
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.preset = preset
        self.chunks = {}
        
        # Spatial hashing for entities
        # maps (cx, cy) -> list of entities
        self.entity_chunks = {}
        self.dirty_chunks = set()
        
        # Environmental variables
        self.time_of_day = 12.0  # 0.0 to 24.0 hours
        self.day_speed = 0.005
        self.global_light = 100.0
        
        # Radiation sources (cx, cy) -> base radiation
        self.radiation_sources = []

    def get_chunk(self, cx, cy):
        """Gets a chunk, generating it on the fly if it doesn't exist."""
        # Wrap coordinates around world boundaries to avoid crashes
        cx = cx % (self.width // CHUNK_SIZE)
        cy = cy % (self.height // CHUNK_SIZE)
        
        key = (cx, cy)
        if key not in self.chunks:
            chunk = Chunk(cx, cy)
            self.apply_preset_to_chunk(chunk)
            self.chunks[key] = chunk
        return self.chunks[key]

    def apply_preset_to_chunk(self, chunk):
        """Modifies chunk properties based on active preset."""
        if self.preset == PRESET_NUCLEAR:
            # Swap grass to wasteland tiles
            mask = chunk.tiles == TILE_GRASS
            chunk.tiles[mask] = TILE_WASTELAND
            
            # Place patches of high radiation
            if random.random() < 0.25:
                # Select a center point in chunk
                rx = random.randint(0, CHUNK_SIZE - 1)
                ry = random.randint(0, CHUNK_SIZE - 1)
                for x in range(CHUNK_SIZE):
                    for y in range(CHUNK_SIZE):
                        dist = math.sqrt((x - rx)**2 + (y - ry)**2)
                        if dist < 12:
                            chunk.radiation[x, y] = max(0, 100.0 - dist * 8.0)
                            
        elif self.preset == PRESET_NO_SUN:
            # Set default light level to pitch black
            chunk.light.fill(5.0)

    def get_tile(self, tx, ty):
        """Gets tile ID at specific tile coordinates."""
        cx = tx // CHUNK_SIZE
        cy = ty // CHUNK_SIZE
        lx = tx % CHUNK_SIZE
        ly = ty % CHUNK_SIZE
        
        chunk = self.get_chunk(cx, cy)
        return chunk.tiles[lx, ly]

    def set_tile(self, tx, ty, tile_type):
        """Sets tile ID at specific tile coordinates."""
        cx = tx // CHUNK_SIZE
        cy = ty // CHUNK_SIZE
        lx = tx % CHUNK_SIZE
        ly = ty % CHUNK_SIZE
        
        chunk = self.get_chunk(cx, cy)
        chunk.tiles[lx, ly] = tile_type
        self.dirty_chunks.add((cx, cy))

    def get_radiation_at(self, tx, ty):
        """Gets radiation level at tile coordinates."""
        cx = tx // CHUNK_SIZE
        cy = ty // CHUNK_SIZE
        lx = tx % CHUNK_SIZE
        ly = ty % CHUNK_SIZE
        
        chunk = self.get_chunk(cx, cy)
        return chunk.radiation[lx, ly]

    def get_light_at(self, tx, ty):
        """Gets light level at tile coordinates."""
        cx = tx // CHUNK_SIZE
        cy = ty // CHUNK_SIZE
        lx = tx % CHUNK_SIZE
        ly = ty % CHUNK_SIZE
        
        chunk = self.get_chunk(cx, cy)
        return chunk.light[lx, ly]

    def set_light_at(self, tx, ty, val):
        """Sets light level at tile coordinates."""
        cx = tx // CHUNK_SIZE
        cy = ty // CHUNK_SIZE
        lx = tx % CHUNK_SIZE
        ly = ty % CHUNK_SIZE
        
        chunk = self.get_chunk(cx, cy)
        chunk.light[lx, ly] = val

    def get_entities_at(self, tx, ty):
        """Gets entities on a specific tile coordinate using spatial hash."""
        cx = tx // CHUNK_SIZE
        cy = ty // CHUNK_SIZE
        entities = []
        # Check neighboring chunks as well to ensure overlapping hits are covered
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                ccx = cx + dx
                ccy = cy + dy
                key = (ccx, ccy)
                if key in self.entity_chunks:
                    for ent in self.entity_chunks[key]:
                        if int(ent.x) == tx and int(ent.y) == ty:
                            entities.append(ent)
        return entities

    def update_entity_chunks(self, entities):
        """Re-hashes all active entities into chunk coordinates."""
        self.entity_chunks = {}
        for ent in entities:
            cx = int(ent.x) // CHUNK_SIZE
            cy = int(ent.y) // CHUNK_SIZE
            key = (cx, cy)
            if key not in self.entity_chunks:
                self.entity_chunks[key] = []
            self.entity_chunks[key].append(ent)

    def update_environment(self, active_chunks):
        """Updates day cycle, entity light grids, grass growth and decay.
        
        active_chunks: set of (cx, cy) tuples visible to player
        """
        # Progress day/night cycle
        self.time_of_day = (self.time_of_day + self.day_speed) % 24.0
        
        # Calculate ambient light based on hour
        if self.preset == PRESET_NO_SUN:
            self.global_light = 5.0
        else:
            # Ambient daylight formula
            hour_rad = (self.time_of_day / 24.0) * 2 * math.pi
            self.global_light = 55.0 + 45.0 * math.sin(hour_rad - math.pi/2)
            
        # Reset and fill light levels for active chunks
        for cx, cy in active_chunks:
            chunk = self.get_chunk(cx, cy)
            chunk.light.fill(self.global_light)
            
        # Project dynamic light sources around active entities in "Without Sun" mode
        if self.preset == PRESET_NO_SUN:
            for chunk_list in self.entity_chunks.values():
                for ent in chunk_list:
                    if ent.is_dead:
                        continue
                    # Suppress human/android light if flashlight battery is empty
                    if ent.type in ["human", "android"] and getattr(ent, "flashlight_battery", 100.0) <= 0.0:
                        continue
                    # Light radius in grid tiles
                    r_tiles = 6 if ent.type == "android" else (3 if ent.type == "human" else (2 if ent.type == "charger" else (4 if ent.type == "beacon" else 0)))
                    if r_tiles == 0:
                        continue
                    
                    tx, ty = int(ent.x), int(ent.y)
                    for dx in range(-r_tiles, r_tiles + 1):
                        for dy in range(-r_tiles, r_tiles + 1):
                            dist = math.hypot(dx, dy)
                            if dist <= r_tiles:
                                ltx = tx + dx
                                lty = ty + dy
                                if 0 <= ltx < self.width and 0 <= lty < self.height:
                                    intensity = max(5.0, 100.0 * (1.0 - (dist / r_tiles)))
                                    # Update light grid of target tile
                                    tcx = ltx // CHUNK_SIZE
                                    tcy = lty // CHUNK_SIZE
                                    tlx = ltx % CHUNK_SIZE
                                    tly = lty % CHUNK_SIZE
                                    t_chunk = self.get_chunk(tcx, tcy)
                                    t_chunk.light[tlx, tly] = max(t_chunk.light[tlx, tly], intensity)

        # Update environment dynamics of active chunks
        for cx, cy in active_chunks:
            chunk = self.get_chunk(cx, cy)
            
            # Grass regrowth (Dirt -> Grass)
            dirt_mask = (chunk.tiles == TILE_DIRT)
            if np.any(dirt_mask):
                rand_arr = np.random.rand(CHUNK_SIZE, CHUNK_SIZE)
                regrow_mask = dirt_mask & (rand_arr < GRASS_REGROW_CHANCE)
                if np.any(regrow_mask):
                    chunk.tiles[regrow_mask] = TILE_GRASS
                    self.dirty_chunks.add((cx, cy))
                    
            # Vegetation decay in deep darkness
            if self.preset == PRESET_NO_SUN:
                grass_mask = (chunk.tiles == TILE_GRASS)
                dark_mask = (chunk.light < 15.0)
                decay_rand = np.random.rand(CHUNK_SIZE, CHUNK_SIZE)
                decay_mask = grass_mask & dark_mask & (decay_rand < 0.005) # 0.5% chance
                if np.any(decay_mask):
                    chunk.tiles[decay_mask] = TILE_DIRT
                    self.dirty_chunks.add((cx, cy))
            
            # If nuclear, diffuse/decay radiation slightly
            if self.preset == PRESET_NUCLEAR:
                # Add random radiation spikes
                if random.random() < 0.01:
                    rx = random.randint(0, CHUNK_SIZE - 1)
                    ry = random.randint(0, CHUNK_SIZE - 1)
                    chunk.radiation[rx, ry] = min(100.0, chunk.radiation[rx, ry] + 50)
                # Slow dispersion/decay
                chunk.radiation *= 0.999

    def get_active_chunks_in_viewport(self, camera_x, camera_y, view_w, view_h):
        """Finds all chunk coordinate tuples that cover the screen's viewport."""
        from src.config import TILE_SIZE
        
        start_wx = int(camera_x / (TILE_SIZE * CHUNK_SIZE))
        start_wy = int(camera_y / (TILE_SIZE * CHUNK_SIZE))
        end_wx = int((camera_x + view_w) / (TILE_SIZE * CHUNK_SIZE)) + 1
        end_wy = int((camera_y + view_h) / (TILE_SIZE * CHUNK_SIZE)) + 1
        
        active = set()
        for cx in range(start_wx, end_wx + 1):
            for cy in range(start_wy, end_wy + 1):
                # Ensure wrapping within map sizes
                ccx = cx % (self.width // CHUNK_SIZE)
                ccy = cy % (self.height // CHUNK_SIZE)
                active.add((ccx, ccy))
        return active
