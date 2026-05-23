# Main Game Controller for Nexus: Neural Survival Sandbox
import pygame
import sys
import random
import math
from src.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE, CHUNK_SIZE, COLORS,
    SIDEBAR_WIDTH, BOTTOM_PANEL_HEIGHT, GRID_WIDTH, GRID_HEIGHT,
    TILE_GRASS, TILE_DIRT, TILE_WATER, TILE_WALL, TILE_WASTELAND, TILE_FLOOR, TILE_ROAD,
    STARTING_HUMANS, STARTING_ANIMALS, STARTING_ZOMBIES, STARTING_ANDROIDS, STARTING_CHARGERS, STARTING_FOOD,
    STARTING_WOLVES,
    PRESET_DEFAULT, PRESET_NUCLEAR, PRESET_ZOMBIE, PRESET_NO_SUN, PRESET_NO_HUMANS, PRESET_NO_ANIMALS
)
from src.world import World
from src.entities import Human, Zombie, Animal, NeuralAndroid, Food, Charger, Wolf, TargetBeacon
from src.ui import UI, Button
from src.utils import draw_text, screen_to_world

class GameController:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Nexus: Neural Survival Sandbox")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Viewport Dimensions (Left of sidebar, top of bottom panel)
        self.view_w = WINDOW_WIDTH - SIDEBAR_WIDTH
        self.view_h = WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT
        
        # Camera Offset (in pixels)
        # Center of 3200x3200 world
        self.camera_x = (1600 * TILE_SIZE) - (self.view_w // 2)
        self.camera_y = (1600 * TILE_SIZE) - (self.view_h // 2)
        self.camera_speed = 8
        
        # Game State
        self.paused = False
        self.simulation_speed = 1.0  # Speed multiplier for updates
        self.active_brush_tile = TILE_WALL
        
        # World & UI Setup
        self.world = World(preset=PRESET_DEFAULT)
        self.ui = UI(self)
        
        # Entities list
        self.entities = []
        self.selected_android = None
        self.selected_entity = None
        self.suppress_painting = False
        self.dragged_entity = None
        
        # Cached chunk surfaces to prevent redraw overhead
        self.chunk_surfaces = {}
        
        # Title screen state
        self.in_title_screen = True
        
        # Title Screen Buttons
        cx = WINDOW_WIDTH // 2
        self.title_buttons = {
            "start": Button(cx - 150, 200, 300, 40, "ENTER SANDBOX", bg_color=(15, 35, 15), border_color=(0, 255, 0), font_size=14),
            "preset_zombie": Button(cx - 150, 255, 300, 40, "ZOMBIE OUTBREAK PRESET", bg_color=(15, 35, 15), border_color=(255, 165, 0), font_size=14),
            "preset_nuclear": Button(cx - 150, 310, 300, 40, "NUCLEAR WINTER PRESET", bg_color=(15, 35, 15), border_color=(255, 165, 0), font_size=14),
            "preset_no_sun": Button(cx - 150, 365, 300, 40, "SUNLESS DARKNESS PRESET", bg_color=(15, 35, 15), border_color=(255, 165, 0), font_size=14),
            "exit": Button(cx - 150, 420, 300, 40, "SHUTDOWN TERMINAL", bg_color=(35, 15, 15), border_color=(255, 50, 50), font_size=14)
        }
        
        # Spawn initial entities
        self.setup_preset_world(self.world.preset)

    def change_preset(self, preset):
        """Clears world, changes preset rules, and spawns corresponding elements."""
        self.selected_android = None
        self.selected_entity = None
        self.dragged_entity = None
        self.ui.editing_field = None
        self.world = World(preset=preset)
        self.chunk_surfaces.clear()
        self.entities.clear()
        
        self.setup_preset_world(preset)

    def clear_world(self):
        """Removes all entities and walls, resetting the active chunk textures."""
        self.entities.clear()
        self.selected_android = None
        self.selected_entity = None
        self.dragged_entity = None
        for key, chunk in self.world.chunks.items():
            chunk.tiles.fill(TILE_GRASS)
            chunk.radiation.fill(0.0)
        self.chunk_surfaces.clear()

    def get_entity_count(self, ent_type):
        """Returns the number of alive entities of a specific type."""
        return sum(1 for e in self.entities if e.type == ent_type and not e.is_dead)

    def setup_preset_world(self, preset):
        """Generates initial starting entities based on preset configurations."""
        # 1. Place Android
        if preset != PRESET_NO_HUMANS:
            # Android
            self.spawn_random_entities(NeuralAndroid, STARTING_ANDROIDS)
            # Humans
            self.spawn_random_entities(Human, STARTING_HUMANS)
            
        if preset != PRESET_NO_ANIMALS:
            # Animals
            self.spawn_random_entities(Animal, STARTING_ANIMALS)
            # Wolves
            self.spawn_random_entities(Wolf, STARTING_WOLVES)
            
        # Zombies
        if preset == PRESET_ZOMBIE:
            self.spawn_random_entities(Zombie, STARTING_ZOMBIES * 3)
        elif preset != PRESET_NO_ANIMALS or preset != PRESET_NO_HUMANS:
            self.spawn_random_entities(Zombie, STARTING_ZOMBIES)
            
        # Food & Charger stations
        self.spawn_random_entities(Charger, STARTING_CHARGERS)
        self.spawn_random_entities(Food, STARTING_FOOD)
        
        # Focus camera on first android if available
        androids = [e for e in self.entities if isinstance(e, NeuralAndroid)]
        if androids:
            self.camera_x = (androids[0].x * TILE_SIZE) - (self.view_w // 2)
            self.camera_y = (androids[0].y * TILE_SIZE) - (self.view_h // 2)
            self.selected_android = androids[0]

    def spawn_random_entities(self, class_type, count):
        """Helper to spawn entities in a safe radius near camera/center."""
        center_x = 1600
        center_y = 1600
        for _ in range(count):
            rx = center_x + random.randint(-40, 40)
            ry = center_y + random.randint(-40, 40)
            
            # Avoid placing inside solid wall
            if self.world.get_tile(rx, ry) != TILE_WALL:
                if class_type == NeuralAndroid:
                    # Give randomized names to Androids
                    names = ["Delta-9", "Echo-7", "Nexus-X", "Sentry-3", "Rover-0"]
                    roles = ["Explorer", "Worker", "Guard", "Farmer"]
                    self.entities.append(NeuralAndroid(rx, ry, name=random.choice(names), role=random.choice(roles)))
                else:
                    self.entities.append(class_type(rx, ry))

    def spawn_entity_in_center(self, ent_type):
        """Spawns an entity right in the middle of the camera's viewport."""
        world_cx, world_cy = screen_to_world(self.view_w // 2, self.view_h // 2, self.camera_x, self.camera_y)
        if ent_type == "human":
            self.entities.append(Human(world_cx, world_cy))
        elif ent_type == "zombie":
            self.entities.append(Zombie(world_cx, world_cy))
        elif ent_type == "android":
            self.entities.append(NeuralAndroid(world_cx, world_cy))
        elif ent_type == "charger":
            self.entities.append(Charger(world_cx, world_cy))
            # Invalidate chunk surface cache
            cx, cy = world_cx // CHUNK_SIZE, world_cy // CHUNK_SIZE
            if (cx, cy) in self.chunk_surfaces:
                del self.chunk_surfaces[(cx, cy)]

    def spawn_customized_android(self, name, role, temperament):
        """Spawns an android with customized identity traits from the customizer."""
        world_cx, world_cy = screen_to_world(self.view_w // 2, self.view_h // 2, self.camera_x, self.camera_y)
        new_android = NeuralAndroid(world_cx, world_cy, name=name, role=role, temperament=temperament)
        self.entities.append(new_android)
        self.selected_android = new_android

    def handle_keyboard_camera(self):
        """Moves camera based on continuous keyboard state updates."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.camera_x -= self.camera_speed
            
        # Suppress camera scrolling with D if held down to drag entities
        suppress_d = keys[pygame.K_d] and pygame.mouse.get_pressed()[0]
        if (keys[pygame.K_d] and not suppress_d) or keys[pygame.K_RIGHT]:
            self.camera_x += self.camera_speed
            
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.camera_y -= self.camera_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.camera_y += self.camera_speed
            
        # Constrain camera to grid size (3200 * 24px)
        max_cam_x = GRID_WIDTH * TILE_SIZE - self.view_w
        max_cam_y = GRID_HEIGHT * TILE_SIZE - self.view_h
        self.camera_x = max(0, min(max_cam_x, self.camera_x))
        self.camera_y = max(0, min(max_cam_y, self.camera_y))

    def update(self):
        """Updates physics ticks, state updates, and simulation entities."""
        if self.in_title_screen:
            return
            
        # Auto-follow selected android with camera if it moves near viewport margins
        keys = pygame.key.get_pressed()
        manual_keys = [pygame.K_a, pygame.K_d, pygame.K_w, pygame.K_s, pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]
        is_manual_scrolling = any(keys[k] for k in manual_keys)
        
        if not is_manual_scrolling and self.selected_android and not self.selected_android.is_dead:
            pixel_x = self.selected_android.x * TILE_SIZE
            pixel_y = self.selected_android.y * TILE_SIZE
            
            # Follow if within 120 pixels of boundaries
            margin = 120
            if (pixel_x < self.camera_x + margin or 
                pixel_x > self.camera_x + self.view_w - margin or 
                pixel_y < self.camera_y + margin or 
                pixel_y > self.camera_y + self.view_h - margin):
                
                target_x = (self.selected_android.x * TILE_SIZE) - (self.view_w // 2)
                target_y = (self.selected_android.y * TILE_SIZE) - (self.view_h // 2)
                
                # Constrain target
                max_cam_x = GRID_WIDTH * TILE_SIZE - self.view_w
                max_cam_y = GRID_HEIGHT * TILE_SIZE - self.view_h
                target_x = max(0, min(max_cam_x, target_x))
                target_y = max(0, min(max_cam_y, target_y))
                
                # Smooth lerp
                self.camera_x += (target_x - self.camera_x) * 0.08
                self.camera_y += (target_y - self.camera_y) * 0.08

        # Update simulation speed from slider
        speed_val = self.ui.sliders["game_speed"].curr_val
        self.simulation_speed = speed_val
        
        if self.paused:
            # Even when paused, re-hash spatial entities so clicks still select correctly
            self.world.update_entity_chunks(self.entities)
            return

        # Multiple updates per frame based on speed setting
        ticks = int(self.simulation_speed)
        fraction = self.simulation_speed - ticks
        
        # Run whole updates
        for _ in range(ticks):
            self.tick_simulation()
            
        # Run fractional update with chance
        if random.random() < fraction:
            self.tick_simulation()

    def tick_simulation(self):
        # Update visible environment
        active_chunks = self.world.get_active_chunks_in_viewport(self.camera_x, self.camera_y, self.view_w, self.view_h)
        self.world.update_environment(active_chunks)
        
        # Spatial hashing updates
        self.world.update_entity_chunks(self.entities)
        
        # Update entities
        dead_entities = []
        for ent in self.entities:
            ent.update(self.world, self.entities)
            if ent.is_dead:
                dead_entities.append(ent)
                
        # Auto-Reward Navigation training loop
        if self.ui.auto_reward and self.selected_android and not self.selected_android.is_dead:
            nearest_beacon = None
            min_beacon_dist = 99999.0
            for ent in self.entities:
                if ent.type == "beacon" and not ent.is_dead:
                    d = math.hypot(ent.x - self.selected_android.x, ent.y - self.selected_android.y)
                    if d < min_beacon_dist:
                        min_beacon_dist = d
                        nearest_beacon = ent
            if nearest_beacon:
                if hasattr(self.selected_android, "last_beacon_dist") and self.selected_android.last_beacon_dist is not None:
                    prev_d = self.selected_android.last_beacon_dist
                    if min_beacon_dist < prev_d:
                        self.selected_android.brain.apply_rlhf_feedback(0.2)
                        self.selected_android.rewards_count += 1
                    elif min_beacon_dist > prev_d:
                        self.selected_android.brain.apply_rlhf_feedback(-0.1)
                        self.selected_android.punishments_count += 1
                self.selected_android.last_beacon_dist = min_beacon_dist
            else:
                self.selected_android.last_beacon_dist = None
        elif self.selected_android:
            self.selected_android.last_beacon_dist = None
                
        # Handle zombified humans
        for ent in dead_entities:
            self.entities.remove(ent)
            if ent == self.selected_android:
                self.selected_android = None
                
            # If a human died of zombie infection, spawn a zombie!
            if isinstance(ent, Human) and ent.infection_timer >= 0 and ent.health <= 0:
                self.entities.append(Zombie(ent.x, ent.y))
            # Spawn food in place of dead animals (scraps)
            elif isinstance(ent, Animal):
                self.entities.append(Food(ent.x, ent.y))
                
        # Spawning environment entities periodically
        if len(self.entities) < 200:
            if random.random() < 0.01:
                # Randomly spawn food or charger near viewport
                wx, wy = screen_to_world(random.randint(0, self.view_w), random.randint(0, self.view_h), self.camera_x, self.camera_y)
                if self.world.get_tile(wx, wy) != TILE_WALL:
                    if random.random() < 0.8:
                        self.entities.append(Food(wx, wy))
                    else:
                        self.entities.append(Charger(wx, wy))
                        cx, cy = wx // CHUNK_SIZE, wy // CHUNK_SIZE
                        if (cx, cy) in self.chunk_surfaces:
                            del self.chunk_surfaces[(cx, cy)]

    def draw(self):
        if self.in_title_screen:
            self.draw_title_screen()
            return
            
        self.screen.fill((10, 10, 12))
        
        # 1. Render visible grid chunks
        active_chunks = self.world.get_active_chunks_in_viewport(self.camera_x, self.camera_y, self.view_w, self.view_h)
        self.render_map_chunks(active_chunks)
        
        # 2. Render Entities
        # Filter entities to those near/within viewport to keep rendering fast
        view_rect = pygame.Rect(self.camera_x - 100, self.camera_y - 100, self.view_w + 200, self.view_h + 200)
        for ent in self.entities:
            pixel_x = ent.x * TILE_SIZE
            pixel_y = ent.y * TILE_SIZE
            if view_rect.collidepoint(pixel_x, pixel_y):
                ent.draw(self.screen, self.camera_x, self.camera_y)
                
        # 3. Apply Darkness/Light mask for Without Sun mode
        if self.world.preset == PRESET_NO_SUN:
            self.draw_flashlight_mask(view_rect)
            
        # 4. Draw HUD highlights (targeting ring around selected entity)
        if self.selected_entity and not self.selected_entity.is_dead:
            from src.utils import world_to_screen
            sx, sy = world_to_screen(self.selected_entity.x + 0.5, self.selected_entity.y + 0.5, self.camera_x, self.camera_y)
            ring_col = COLORS["ui_accent"] if isinstance(self.selected_entity, NeuralAndroid) else COLORS["ui_text"]
            pygame.draw.circle(self.screen, ring_col, (sx, sy), int(self.selected_entity.radius * TILE_SIZE + 6), width=2)
            # Outer reticle lines for classic look
            r_sz = int(self.selected_entity.radius * TILE_SIZE + 6)
            pygame.draw.line(self.screen, ring_col, (sx - r_sz - 4, sy), (sx - r_sz + 2, sy), 1)
            pygame.draw.line(self.screen, ring_col, (sx + r_sz - 2, sy), (sx + r_sz + 4, sy), 1)
            pygame.draw.line(self.screen, ring_col, (sx, sy - r_sz - 4), (sx, sy - r_sz + 2), 1)
            pygame.draw.line(self.screen, ring_col, (sx, sy + r_sz - 2), (sx, sy + r_sz + 4), 1)
            
        # Viewport overlays are drawn by the UI component

        
        # 5. Draw UI panels
        self.ui.draw(self.screen)
        
        pygame.display.flip()

    def draw_title_screen(self):
        # Fill screen with dark base
        self.screen.fill((5, 10, 5))
        
        # Draw a beautiful retro scrolling matrix-like grid in title screen
        time_ms = pygame.time.get_ticks()
        grid_offset = int(time_ms * 0.05) % 24
        for x in range(0, WINDOW_WIDTH, 24):
            pygame.draw.line(self.screen, (0, 20, 0), (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(grid_offset, WINDOW_HEIGHT, 24):
            pygame.draw.line(self.screen, (0, 20, 0), (0, y), (WINDOW_WIDTH, y), 1)
            
        # Draw central terminal box
        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2
        terminal_rect = pygame.Rect(cx - 280, cy - 250, 560, 500)
        
        # Transparent dark green back panel
        back_surf = pygame.Surface((560, 500), pygame.SRCALPHA)
        back_surf.fill((5, 15, 5, 230))
        self.screen.blit(back_surf, (cx - 280, cy - 250))
        
        # Border
        pygame.draw.rect(self.screen, COLORS["ui_border"], terminal_rect, width=2)
        
        # Draw titles
        draw_text(self.screen, "N E X U S", cx, cy - 220, size=54, color=COLORS["ui_text"], align="center")
        draw_text(self.screen, "NEURAL SURVIVAL SANDBOX v2.0", cx, cy - 165, size=15, color=COLORS["ui_accent"], align="center")
        
        # Draw small separator line
        pygame.draw.line(self.screen, COLORS["ui_border"], (cx - 220, cy - 145), (cx + 220, cy - 145), 1)
        
        # Draw decorative system status text
        draw_text(self.screen, "SYSTEM DIAGNOSTICS: ONLINE", cx - 220, cy - 130, size=12, color=COLORS["ui_text_dim"])
        draw_text(self.screen, "NEURAL INTERFACE: READY", cx + 220, cy - 130, size=12, color=COLORS["ui_text_dim"], align="right")
        
        # Draw Title Buttons
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.title_buttons.values():
            btn.check_hover(mouse_pos)
            btn.draw(self.screen)
            
        # Draw scanlines overlay
        for y in range(0, WINDOW_HEIGHT, 4):
            pygame.draw.line(self.screen, (0, 5, 0), (0, y), (WINDOW_WIDTH, y), 1)
            
        # Draw retro blinking terminal prompt
        prompt_text = "SECURE TERMINAL ACCESS > PRE-BOOT COMPLETE."
        if int(time_ms / 400) % 2 == 0:
            prompt_text += " _"
        draw_text(self.screen, prompt_text, cx, cy + 220, size=12, color=COLORS["ui_accent"], align="center")
        
        pygame.display.flip()

    def render_map_chunks(self, active_chunks):
        """Draws chunk cached surfaces to screen using camera coordinates."""
        for cx, cy in active_chunks:
            chunk = self.world.get_chunk(cx, cy)
            
            # If chunk texture surface doesn't exist, render it to memory cache
            if (cx, cy) not in self.chunk_surfaces:
                self.cache_chunk_surface(cx, cy, chunk)
                
            chunk_surf = self.chunk_surfaces[(cx, cy)]
            
            # Compute screen coordinates
            screen_x = cx * CHUNK_SIZE * TILE_SIZE - self.camera_x
            screen_y = cy * CHUNK_SIZE * TILE_SIZE - self.camera_y
            
            # Blit standard chunk surface
            self.screen.blit(chunk_surf, (screen_x, screen_y))
            
            # If Nuclear Preset, blit radiation hazard indicator glow
            if self.world.preset == PRESET_NUCLEAR:
                rad_strength = chunk.radiation.max()
                if rad_strength > 5.0:
                    glow_surf = pygame.Surface((CHUNK_SIZE * TILE_SIZE, CHUNK_SIZE * TILE_SIZE), pygame.SRCALPHA)
                    alpha = int(min(60, rad_strength * 0.6))
                    glow_surf.fill((100, 255, 50, alpha))
                    self.screen.blit(glow_surf, (screen_x, screen_y))

    def cache_chunk_surface(self, cx, cy, chunk):
        """Creates a static cached Surface of a 32x32 chunk to speed up rendering loops."""
        surf = pygame.Surface((CHUNK_SIZE * TILE_SIZE, CHUNK_SIZE * TILE_SIZE))
        for x in range(CHUNK_SIZE):
            for y in range(CHUNK_SIZE):
                tile = chunk.tiles[x, y]
                color = COLORS.get(tile, (50, 50, 50))
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                
                # Render base tile
                pygame.draw.rect(surf, color, rect)
                
                # Draw visual outlines for walls/floors to look clean and structured
                if tile == TILE_WALL:
                    pygame.draw.rect(surf, (30, 32, 35), rect, width=1)
                elif tile == TILE_FLOOR:
                    pygame.draw.rect(surf, (40, 42, 45), rect, width=1)
                else:
                    # Subtle organic border
                    pygame.draw.rect(surf, (0, 0, 0, 15), rect, width=1)
                    
        self.chunk_surfaces[(cx, cy)] = surf

    def draw_flashlight_mask(self, view_rect):
        """Draws dynamic radial shadows and cone light around agents to simulate pitch black."""
        # Create light mask surface
        mask = pygame.Surface((self.view_w, self.view_h), pygame.SRCALPHA)
        # Fill with ambient dark (translucent black-blue)
        mask.fill((5, 5, 8, 248))
        
        # Gather all emitters
        emitters = []
        for ent in self.entities:
            pixel_x = ent.x * TILE_SIZE
            pixel_y = ent.y * TILE_SIZE
            if view_rect.collidepoint(pixel_x, pixel_y):
                # Suppress light if entity flashlight battery is dead
                if ent.type in ["human", "android"] and getattr(ent, "flashlight_battery", 100.0) <= 0.0:
                    continue
                # Light Radius based on entity type
                if ent == self.selected_android:
                    radius = 160  # Selected Android light beam is stronger
                elif ent.type == "android":
                    radius = 100
                elif ent.type == "human":
                    radius = 70
                elif ent.type == "zombie":
                    radius = 35   # Zombies glow slightly red
                elif ent.type == "charger":
                    radius = 50
                elif ent.type == "beacon":
                    radius = 90   # Beacon glows neon cyan
                else:
                    continue
                emitters.append((ent, pixel_x, pixel_y, radius))
                
        # Draw transparent holes in mask
        for ent, px, py, radius in emitters:
            sx = int(px + (ent.radius * TILE_SIZE) - self.camera_x)
            sy = int(py + (ent.radius * TILE_SIZE) - self.camera_y)
            
            # Simple radial gradient cutout
            if ent.type == "zombie":
                glow_color = (255, 50, 50, 100)
            elif ent.type == "charger":
                glow_color = (255, 220, 100, 120)
            else:
                glow_color = (255, 255, 255, 180)
                
            # Create local light circle
            light_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            for r in range(radius, 0, -6):
                alpha = int(248 * (1.0 - (r / radius)))
                col = (glow_color[0], glow_color[1], glow_color[2], alpha)
                pygame.draw.circle(light_surf, col, (radius, radius), r)
                
            # Blit subtraction onto mask
            mask.blit(light_surf, (sx - radius, sy - radius), special_flags=pygame.BLEND_RGBA_SUB)
            
        self.screen.blit(mask, (0, 0))

    def handle_map_click(self, mouse_pos):
        """Checks click targets on the world viewport: selects agents or paints tiles."""
        mx, my = mouse_pos
        if mx >= self.view_w or my >= self.view_h:
            return  # Clicked inside UI frames
            
        # Convert screen coords to world map index
        wx, wy = screen_to_world(mx, my, self.camera_x, self.camera_y)
        
        # 1. Search for clicked entities (priority to Androids)
        clicked_entities = []
        for ent in self.entities:
            dist = math.hypot(ent.x - wx, ent.y - wy)
            if dist <= 1.2:
                clicked_entities.append(ent)
                
        if clicked_entities:
            # Sort clicked entities to prioritize Androids, then Humans, then Zombies, then others
            clicked_entities.sort(key=lambda e: 0 if isinstance(e, NeuralAndroid) else (1 if isinstance(e, Human) else (2 if isinstance(e, Zombie) else 3)))
            self.selected_entity = clicked_entities[0]
            if isinstance(self.selected_entity, NeuralAndroid):
                self.selected_android = self.selected_entity
            else:
                self.selected_android = None
            return True
            
        # 2. Paint world tiles if clicked empty space
        if self.active_brush_tile == "beacon":
            # Spawn a TargetBeacon if there isn't one close by on this tile coordinate
            tx, ty = int(wx), int(wy)
            already_has_beacon = False
            for ent in self.entities:
                if ent.type == "beacon" and int(ent.x) == tx and int(ent.y) == ty and not ent.is_dead:
                    already_has_beacon = True
                    break
            if not already_has_beacon:
                self.entities.append(TargetBeacon(tx, ty))
            return False

        # Edit tile type in world grid
        self.world.set_tile(wx, wy, self.active_brush_tile)
        
        # If Nuclear, add radiation source
        if self.active_brush_tile == TILE_WASTELAND:
            cx = wx // CHUNK_SIZE
            cy = wy // CHUNK_SIZE
            lx = wx % CHUNK_SIZE
            ly = wy % CHUNK_SIZE
            self.world.get_chunk(cx, cy).radiation[lx, ly] = 100.0
            
        # Invalidate chunk surface cache to trigger redraw
        cx = wx // CHUNK_SIZE
        cy = wy // CHUNK_SIZE
        if (cx, cy) in self.chunk_surfaces:
            del self.chunk_surfaces[(cx, cy)]
            
        return False

    def handle_map_drag(self, mouse_pos):
        """Allows painting/drawing continuously by dragging mouse left button."""
        mx, my = mouse_pos
        if mx >= self.view_w or my >= self.view_h:
            return
            
        wx, wy = screen_to_world(mx, my, self.camera_x, self.camera_y)
        if self.active_brush_tile == "beacon":
            tx, ty = int(wx), int(wy)
            already_has_beacon = False
            for ent in self.entities:
                if ent.type == "beacon" and int(ent.x) == tx and int(ent.y) == ty and not ent.is_dead:
                    already_has_beacon = True
                    break
            if not already_has_beacon:
                self.entities.append(TargetBeacon(tx, ty))
            return

        if self.world.get_tile(wx, wy) != self.active_brush_tile:
            self.world.set_tile(wx, wy, self.active_brush_tile)
            
            cx = wx // CHUNK_SIZE
            cy = wy // CHUNK_SIZE
            if (cx, cy) in self.chunk_surfaces:
                del self.chunk_surfaces[(cx, cy)]

    def run(self):
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            
            # 1. Event Loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                # Title screen event interception
                if self.in_title_screen:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.title_buttons["start"].rect.collidepoint(mouse_pos):
                            self.in_title_screen = False
                            self.paused = False
                        elif self.title_buttons["preset_zombie"].rect.collidepoint(mouse_pos):
                            self.change_preset(PRESET_ZOMBIE)
                            self.in_title_screen = False
                            self.paused = False
                        elif self.title_buttons["preset_nuclear"].rect.collidepoint(mouse_pos):
                            self.change_preset(PRESET_NUCLEAR)
                            self.in_title_screen = False
                            self.paused = False
                        elif self.title_buttons["preset_no_sun"].rect.collidepoint(mouse_pos):
                            self.change_preset(PRESET_NO_SUN)
                            self.in_title_screen = False
                            self.paused = False
                        elif self.title_buttons["exit"].rect.collidepoint(mouse_pos):
                            running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                            self.in_title_screen = False
                            self.paused = False
                    continue
                    
                # UI Inputs typing handler
                if self.ui.editing_field:
                    self.ui.handle_keyboard(event)
                    continue
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left click
                        keys = pygame.key.get_pressed()
                        # If holding 'D' to drag/move entities
                        if keys[pygame.K_d]:
                            mx, my = mouse_pos
                            if mx < self.view_w and my < self.view_h:
                                wx, wy = screen_to_world(mx, my, self.camera_x, self.camera_y)
                                for ent in self.entities:
                                    if math.hypot(ent.x - wx, ent.y - wy) <= 1.2:
                                        self.dragged_entity = ent
                                        self.suppress_painting = True
                                        break
                                        
                        # Click on UI panels takes priority if not dragging
                        if not self.dragged_entity:
                            if self.ui.handle_click(mouse_pos):
                                self.suppress_painting = True
                            else:
                                # If map click selected an entity, suppress paint dragging
                                if self.handle_map_click(mouse_pos):
                                    self.suppress_painting = True
                                else:
                                    self.suppress_painting = False
                                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragged_entity = None
                        self.suppress_painting = False
                            
                elif event.type == pygame.KEYDOWN:
                    # Switch tile brush types with numeric keys
                    if event.key == pygame.K_1:
                        self.active_brush_tile = TILE_WALL
                    elif event.key == pygame.K_2:
                        self.active_brush_tile = TILE_GRASS
                    elif event.key == pygame.K_3:
                        self.active_brush_tile = TILE_WATER
                    elif event.key == pygame.K_4:
                        self.active_brush_tile = TILE_DIRT
                    elif event.key == pygame.K_5:
                        self.active_brush_tile = TILE_WASTELAND
                    elif event.key == pygame.K_6:
                        self.active_brush_tile = TILE_FLOOR
                    elif event.key == pygame.K_7:
                        self.active_brush_tile = "beacon"
                        
                # Sliders handling
                self.ui.sliders["game_speed"].handle_event(event, mouse_pos)
                
            # Dragging entity update
            if self.dragged_entity:
                if pygame.mouse.get_pressed()[0]:
                    mx, my = mouse_pos
                    if mx < self.view_w and my < self.view_h:
                        wx, wy = screen_to_world(mx, my, self.camera_x, self.camera_y)
                        self.dragged_entity.x = max(0.1, min(GRID_WIDTH - 1.1, wx - 0.5))
                        self.dragged_entity.y = max(0.1, min(GRID_HEIGHT - 1.1, wy - 0.5))
                else:
                    self.dragged_entity = None
                    self.suppress_painting = False
                    
            # Handle continuous map paint dragging
            if pygame.mouse.get_pressed()[0] and not self.suppress_painting:
                self.handle_map_drag(mouse_pos)
                
            # 2. Camera Controls
            self.handle_keyboard_camera()
            
            # 3. Physics / Update Loop
            self.update()
            
            # 4. Render
            self.draw()
            
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = GameController()
    game.run()
