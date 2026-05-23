# UI Framework and Components for Nexus
import pygame
import math
from src.config import COLORS, SIDEBAR_WIDTH, BOTTOM_PANEL_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT, GRID_WIDTH, GRID_HEIGHT
from src.utils import draw_rounded_rect, draw_text

class Button:
    def __init__(self, x, y, width, height, text, bg_color=None, text_color=None, border_color=None, border_radius=0, font_size=16):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.bg_color = bg_color if bg_color else COLORS["ui_button"]
        self.text_color = text_color if text_color else COLORS["ui_text"]
        self.border_color = border_color if border_color else COLORS["ui_border"]
        self.border_radius = border_radius
        self.font_size = font_size
        self.is_hovered = False

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def draw(self, surface):
        # Draw button box
        color = COLORS["ui_button_hover"] if self.is_hovered else self.bg_color
        
        # Transparent background draw
        draw_rounded_rect(surface, self.rect, color, radius=self.border_radius, border_color=self.border_color)
        
        # Draw label
        draw_text(surface, self.text, self.rect.centerx, self.rect.centery - (self.font_size // 2) + 1, 
                  size=self.font_size, color=self.text_color, align="center")

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, start_val, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.curr_val = start_val
        self.label = label
        
        self.knob_radius = 8
        self.knob_x = x + int((start_val - min_val) / (max_val - min_val) * width)
        self.is_dragging = False

    def draw(self, surface):
        # Draw label & value
        draw_text(surface, f"{self.label}: {self.curr_val:.2f}", self.rect.x, self.rect.y - 20, size=14, color=COLORS["ui_text"])
        
        # Draw bar
        bar_rect = pygame.Rect(self.rect.x, self.rect.centery - 2, self.rect.width, 4)
        draw_rounded_rect(surface, bar_rect, (80, 80, 90), radius=0)
        
        # Draw active bar portion
        active_rect = pygame.Rect(self.rect.x, self.rect.centery - 2, self.knob_x - self.rect.x, 4)
        draw_rounded_rect(surface, active_rect, COLORS["ui_accent"], radius=0)
        
        # Draw knob
        pygame.draw.circle(surface, (255, 255, 255), (self.knob_x, self.rect.centery), self.knob_radius)
        pygame.draw.circle(surface, COLORS["ui_accent"], (self.knob_x, self.rect.centery), self.knob_radius - 2)

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            dist = math.hypot(mouse_pos[0] - self.knob_x, mouse_pos[1] - self.rect.centery)
            if dist <= self.knob_radius + 4 or self.rect.collidepoint(mouse_pos):
                self.is_dragging = True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            self.is_dragging = False
            
        if self.is_dragging and event.type in [pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN]:
            mx = max(self.rect.x, min(mouse_pos[0], self.rect.x + self.rect.width))
            self.knob_x = mx
            t = (mx - self.rect.x) / self.rect.width
            self.curr_val = self.min_val + t * (self.max_val - self.min_val)
            return self.curr_val
        return None

class UI:
    def __init__(self, main_game):
        self.game = main_game
        
        # Dimensions
        self.sidebar_rect = pygame.Rect(WINDOW_WIDTH - SIDEBAR_WIDTH, 0, SIDEBAR_WIDTH, WINDOW_HEIGHT)
        self.bottom_rect = pygame.Rect(0, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT, WINDOW_WIDTH - SIDEBAR_WIDTH, BOTTOM_PANEL_HEIGHT)
        
        self.buttons = {}
        self.sliders = {}
        self.init_ui_elements()
        
        # Customizer fields
        self.custom_name = "Android Omega"
        self.custom_role = "Gatherer"
        self.custom_temp = "Curious"
        self.custom_solar = False
        self.custom_shield = False
        self.auto_reward = False
        
        self.editing_field = None  # Track if typing name or role

    def init_ui_elements(self):
        # Preset buttons (Bottom panel)
        bx, by = 20, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 45
        preset_names = ["Default", "Nuclear", "Zombie", "No Sun", "No Human", "No Animal"]
        for name in preset_names:
            key = f"preset_{name.lower().replace(' ', '_')}"
            self.buttons[key] = Button(bx, by, 100, 32, name, font_size=13)
            bx += 110
            
        # Spawn entity buttons (Bottom panel)
        self.buttons["spawn_human"] = Button(700, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 45, 90, 32, "+ Human", font_size=13)
        self.buttons["spawn_zombie"] = Button(800, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 45, 90, 32, "+ Zombie", font_size=13)
        self.buttons["spawn_android"] = Button(700, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 85, 90, 32, "+ Android", font_size=13)
        self.buttons["spawn_charger"] = Button(800, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 85, 90, 32, "+ Charger", font_size=13)
        
        # Simulation playback buttons
        self.buttons["play_pause"] = Button(20, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 95, 100, 32, "Pause", font_size=13)
        self.buttons["clear_world"] = Button(130, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 95, 100, 32, "Clear Grid", font_size=13)
        
        # Speed slider (Bottom panel)
        self.sliders["game_speed"] = Slider(300, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 115, 200, 20, 0.5, 4.0, 1.0, "Simulation Speed")
        
        # RLHF Buttons (Sidebar, initialized when an Android is selected)
        sx, sy = WINDOW_WIDTH - SIDEBAR_WIDTH + 20, 260
        self.buttons["rlhf_reward"] = Button(sx, sy, 140, 40, "REWARD (+1)", bg_color=(39, 174, 96, 200), border_color=(46, 204, 113), font_size=14)
        self.buttons["rlhf_punish"] = Button(sx + 160, sy, 140, 40, "PUNISH (-1)", bg_color=(192, 57, 43, 200), border_color=(231, 76, 60), font_size=14)
        
        # Customizer buttons
        self.buttons["customizer_create"] = Button(WINDOW_WIDTH - SIDEBAR_WIDTH + 20, 190, 300, 34, "Create Android with custom ID", bg_color=(60, 40, 75, 200), font_size=13)
        
        # Deselect button (classic dark red border)
        self.buttons["deselect_entity"] = Button(WINDOW_WIDTH - SIDEBAR_WIDTH + 20, 500, 300, 34, "CLOSE INSPECTOR", bg_color=(35, 15, 15), border_color=(255, 50, 50))

    def draw(self, surface):
        # Draw glassmorphism backgrounds for Sidebar and Bottom panel
        draw_rounded_rect(surface, self.sidebar_rect, COLORS["ui_bg"], radius=0, border_color=COLORS["ui_border"])
        draw_rounded_rect(surface, self.bottom_rect, COLORS["ui_bg"], radius=0, border_color=COLORS["ui_border"])
        
        # --- Bottom Panel Headers & Statistics ---
        draw_text(surface, "WORLD ENVIRONMENT PRESETS", 20, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 15, size=16, color=COLORS["ui_accent"])
        draw_text(surface, "SPAWN TOOLS", 700, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 15, size=16, color=COLORS["ui_accent"])
        
        # Statistics Box
        stats_x = 520
        draw_text(surface, "SIMULATION STATS", stats_x, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 15, size=15, color=COLORS["ui_text_dim"])
        draw_text(surface, f"World Size: {self.game.world.width}x{self.game.world.height}", stats_x, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 40, size=13)
        draw_text(surface, f"FPS: {int(self.game.clock.get_fps())}", stats_x, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 60, size=13)
        draw_text(surface, f"Humans: {self.game.get_entity_count('human')}", stats_x, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 80, size=13)
        draw_text(surface, f"Zombies: {self.game.get_entity_count('zombie')}", stats_x, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 100, size=13)
        draw_text(surface, f"Androids: {self.game.get_entity_count('android')}", stats_x, WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT + 120, size=13)

        # Draw default bottom controls
        for btn in self.buttons.values():
            # Skip drawing RLHF controls if no android is selected
            if (btn.text.startswith("REWARD") or btn.text.startswith("PUNISH")) and not self.game.selected_android:
                continue
            # Skip drawing Close Inspector button if no entity is selected
            if btn.text == "CLOSE INSPECTOR" and not self.game.selected_entity:
                continue
            btn.draw(surface)
            
        for slider in self.sliders.values():
            slider.draw(surface)
            
        # --- Viewport Overlays ---
        self.draw_viewport_legend(surface)
        self.draw_tile_toolbar(surface)
            
        # --- Right Sidebar Layout ---
        self.draw_sidebar(surface)

    def draw_sidebar(self, surface):
        x = WINDOW_WIDTH - SIDEBAR_WIDTH + 20
        draw_text(surface, "NEXUS INTERACTION HUB", x, 15, size=18, color=COLORS["ui_accent"])
        
        # Divider line
        pygame.draw.line(surface, COLORS["ui_border"], (WINDOW_WIDTH - SIDEBAR_WIDTH + 15, 45), (WINDOW_WIDTH - 15, 45), 1)
        
        if self.game.selected_android:
            # Android Inspector Panel
            self.draw_android_inspector(surface, x)
        elif self.game.selected_entity:
            # General Entity Inspector
            self.draw_general_inspector(surface, x)
        else:
            # Android Creator Customizer Panel
            self.draw_android_customizer(surface, x)
            
        # Draw Mini-Map at the bottom right corner of the sidebar
        self.draw_minimap(surface)

    def draw_android_customizer(self, surface, x):
        draw_text(surface, "ANDROID CREATOR & CUSTOMIZER", x, 55, size=15, color=COLORS["ui_text"])
        
        # Draw input boxes for name and role
        y_offset = 85
        box_width = 300
        
        # Name Input Box
        draw_text(surface, "Name (Click to edit):", x, y_offset, size=13, color=COLORS["ui_text_dim"])
        name_rect = pygame.Rect(x, y_offset + 18, box_width, 24)
        name_border = COLORS["ui_accent"] if self.editing_field == "name" else COLORS["ui_border"]
        draw_rounded_rect(surface, name_rect, (30, 30, 40), radius=0, border_color=name_border)
        draw_text(surface, self.custom_name, name_rect.x + 8, name_rect.y + 4, size=13)
        
        # Role Input Box
        y_offset += 50
        draw_text(surface, "Role:", x, y_offset, size=13, color=COLORS["ui_text_dim"])
        role_rect = pygame.Rect(x, y_offset + 18, box_width, 24)
        role_border = COLORS["ui_accent"] if self.editing_field == "role" else COLORS["ui_border"]
        draw_rounded_rect(surface, role_rect, (30, 30, 40), radius=0, border_color=role_border)
        draw_text(surface, self.custom_role, role_rect.x + 8, role_rect.y + 4, size=13)
        
        # Checkboxes for upgrades
        y_offset = 230
        draw_text(surface, "Modular Hardwares:", x, y_offset, size=13, color=COLORS["ui_text_dim"])
        
        # Solar Panel Checkbox
        y_offset += 20
        solar_rect = pygame.Rect(x, y_offset, 14, 14)
        draw_rounded_rect(surface, solar_rect, (30, 30, 40), radius=0, border_color=COLORS["ui_border"])
        if self.custom_solar:
            pygame.draw.line(surface, COLORS["ui_accent"], (x + 3, y_offset + 3), (x + 11, y_offset + 11), 2)
            pygame.draw.line(surface, COLORS["ui_accent"], (x + 11, y_offset + 3), (x + 3, y_offset + 11), 2)
        draw_text(surface, "Solar pad (+0.06/f in light)", x + 24, y_offset - 2, size=11)
        
        # Rad Shield Checkbox
        y_offset += 20
        shield_rect = pygame.Rect(x, y_offset, 14, 14)
        draw_rounded_rect(surface, shield_rect, (30, 30, 40), radius=0, border_color=COLORS["ui_border"])
        if self.custom_shield:
            pygame.draw.line(surface, COLORS["ui_accent"], (x + 3, y_offset + 3), (x + 11, y_offset + 11), 2)
            pygame.draw.line(surface, COLORS["ui_accent"], (x + 11, y_offset + 3), (x + 3, y_offset + 11), 2)
        draw_text(surface, "Radiation deflector shield", x + 24, y_offset - 2, size=11)
        
        # Info details
        y_offset += 35
        draw_text(surface, "Select an android on map to train them.", x, y_offset, size=13, color=COLORS["ui_text_dim"])
        draw_text(surface, "Provide feedback using RLHF buttons", x, y_offset + 20, size=13, color=COLORS["ui_text_dim"])
        draw_text(surface, "to shape their behaviors in real-time.", x, y_offset + 40, size=13, color=COLORS["ui_text_dim"])

    def draw_android_inspector(self, surface, x):
        android = self.game.selected_android
        draw_text(surface, f"INSPECTOR: {android.name}", x, 55, size=16, color=(255, 255, 255))
        
        # Stats display
        y_offset = 85
        draw_text(surface, f"Role: {android.role}  |  Temp: {android.temperament}", x, y_offset, size=13, color=COLORS["ui_text_dim"])
        
        # Health bar
        y_offset += 20
        draw_text(surface, f"Health: {int(android.health)}%", x, y_offset, size=12)
        h_bar_rect = pygame.Rect(x + 100, y_offset + 3, 180, 10)
        draw_rounded_rect(surface, h_bar_rect, (40, 40, 50), radius=0)
        h_active = pygame.Rect(x + 100, y_offset + 3, int(android.health / 100.0 * 180), 10)
        draw_rounded_rect(surface, h_active, (46, 204, 113), radius=0)

        # Battery bar
        y_offset += 16
        draw_text(surface, f"Battery: {int(android.battery)}%", x, y_offset, size=12)
        b_bar_rect = pygame.Rect(x + 100, y_offset + 3, 180, 10)
        draw_rounded_rect(surface, b_bar_rect, (40, 40, 50), radius=0)
        b_active = pygame.Rect(x + 100, y_offset + 3, int(android.battery / 100.0 * 180), 10)
        draw_rounded_rect(surface, b_active, COLORS["charger"], radius=0)
        
        # Flashlight bar
        y_offset += 16
        draw_text(surface, f"Lightpad: {int(android.flashlight_battery)}%", x, y_offset, size=12)
        f_bar_rect = pygame.Rect(x + 100, y_offset + 3, 180, 10)
        draw_rounded_rect(surface, f_bar_rect, (40, 40, 50), radius=0)
        f_active = pygame.Rect(x + 100, y_offset + 3, int(android.flashlight_battery / 100.0 * 180), 10)
        draw_rounded_rect(surface, f_active, COLORS["beacon"], radius=0)

        # Show equipped modules
        y_offset += 16
        modules_text = []
        if android.has_solar_panel:
            modules_text.append("SOLAR")
        if android.has_rad_shield:
            modules_text.append("RAD-SHIELD")
        mod_str = " | ".join(modules_text) if modules_text else "NONE"
        draw_text(surface, f"Hardware: {mod_str}", x, y_offset, size=11, color=COLORS["ui_text_dim"])

        y_offset += 16
        draw_text(surface, f"Rewards Applied: {android.rewards_count}", x, y_offset, size=12, color=COLORS["reward_green"])
        draw_text(surface, f"Punish Applied: {android.punishments_count}", x + 160, y_offset, size=12, color=COLORS["punish_red"])
        
        # Auto-Reward Checkbox
        y_offset += 18
        ar_rect = pygame.Rect(x, y_offset, 14, 14)
        draw_rounded_rect(surface, ar_rect, (30, 30, 40), radius=0, border_color=COLORS["ui_border"])
        if self.auto_reward:
            pygame.draw.line(surface, COLORS["ui_accent"], (x + 3, y_offset + 3), (x + 11, y_offset + 11), 2)
            pygame.draw.line(surface, COLORS["ui_accent"], (x + 11, y_offset + 3), (x + 3, y_offset + 11), 2)
        draw_text(surface, "Auto-Train to closest Beacon", x + 24, y_offset - 2, size=11, color=COLORS["ui_text"])
        
        # Neural Network Graph Visualizer in Sidebar
        self.draw_neural_net_visualizer(surface, WINDOW_WIDTH - SIDEBAR_WIDTH + 20, 310)

    def draw_neural_net_visualizer(self, surface, x, y):
        android = self.game.selected_android
        if not android or android.current_state_vector is None:
            return
            
        draw_text(surface, "NEURAL ACTIVATIONS (REALTIME)", x, y, size=13, color=COLORS["ui_accent"])
        
        # Width/height of visualization area
        w, h = 300, 200
        vis_rect = pygame.Rect(x, y + 20, w, h)
        draw_rounded_rect(surface, vis_rect, (25, 25, 30, 255), radius=0, border_color=COLORS["ui_border"])
        
        # Inputs, Hidden, Output node visualization coordinates
        # Since 35 inputs is too crowded to draw as text labels, we will group inputs:
        # We will summarize 35 inputs into key sensors:
        # Obstacles, Food, Charger, Zombie (8 directions each -> 4 categories) + Internal
        # Let's map coordinates for 3 groups of layers:
        # Layer 1: Inputs (Let's draw 6 main grouped categories)
        # Layer 2: Hidden units (Let's draw 6 representative hidden neurons)
        # Layer 3: Outputs (5 actions)
        
        inputs_summarized = [
            ("Obstacles", max(android.current_state_vector[0:32:4])),
            ("Food", max(android.current_state_vector[1:32:4])),
            ("Charger", max(android.current_state_vector[2:32:4])),
            ("Zombies", max(android.current_state_vector[3:32:4])),
            ("Battery", android.current_state_vector[32]),
            ("Rad Level", android.current_state_vector[34])
        ]
        
        outputs_labels = ["UP", "DOWN", "LEFT", "RIGHT", "INTERACT"]
        
        # Node positions
        input_nodes = []
        hidden_nodes = []
        output_nodes = []
        
        # Calculate Y offsets
        for i, (label, val) in enumerate(inputs_summarized):
            ny = vis_rect.y + 20 + i * 28
            input_nodes.append((vis_rect.x + 25, ny, val, label))
            
        for i in range(6):
            ny = vis_rect.y + 20 + i * 28
            h_val = android.brain.last_hidden[i] if len(android.brain.last_hidden) > i else 0.0
            hidden_nodes.append((vis_rect.x + 150, ny, h_val))
            
        for i, label in enumerate(outputs_labels):
            ny = vis_rect.y + 20 + i * 32
            out_val = android.brain.last_outputs[i] if len(android.brain.last_outputs) > i else 0.0
            output_nodes.append((vis_rect.x + 270, ny, out_val, label))
            
        # Draw Synapses (connecting lines) with weights
        # We will draw connections using actual weights from the Android's brain
        # Since we compressed inputs, we will just draw representative synapse paths
        for idx_in, (ix, iy, val_in, _) in enumerate(input_nodes):
            for idx_hid, (hx, hy, val_hid) in enumerate(hidden_nodes):
                weight = android.brain.W1[idx_in, idx_hid] if idx_in < android.brain.W1.shape[0] else 0.0
                intensity = int(min(255, abs(weight) * 120))
                # Color code: green/blue for positive, red for negative
                w_color = (0, 180, 255, intensity) if weight > 0 else (255, 90, 90, intensity)
                
                # Active links glow
                line_w = 1
                if val_in > 0.1:
                    line_w = 2
                
                pygame.draw.line(surface, w_color, (ix, iy), (hx, hy), line_w)
                
        for idx_hid, (hx, hy, val_hid) in enumerate(hidden_nodes):
            for idx_out, (ox, oy, val_out, _) in enumerate(output_nodes):
                weight = android.brain.W2[idx_hid, idx_out] if idx_hid < android.brain.W2.shape[0] else 0.0
                intensity = int(min(255, abs(weight) * 150))
                w_color = (0, 180, 255, intensity) if weight > 0 else (255, 90, 90, intensity)
                
                line_w = 1
                if abs(val_hid) > 0.4:
                    line_w = 2
                pygame.draw.line(surface, w_color, (hx, hy), (ox, oy), line_w)
                
        # Draw Nodes
        # Input nodes
        for ix, iy, val, label in input_nodes:
            glow = int(val * 150)
            pygame.draw.circle(surface, (30 + glow, 30 + glow, 50 + glow), (ix, iy), 8)
            pygame.draw.circle(surface, COLORS["ui_accent"] if val > 0.2 else (100, 100, 100), (ix, iy), 8, width=1)
            # Short label
            draw_text(surface, label[:4], ix - 22, iy - 6, size=10, color=(180, 180, 190))
            
        # Hidden nodes
        for hx, hy, val in hidden_nodes:
            glow = int(abs(val) * 150)
            pygame.draw.circle(surface, (30, 30 + glow, 30 + glow), (hx, hy), 6)
            pygame.draw.circle(surface, (120, 120, 120), (hx, hy), 6, width=1)
            
        # Output nodes
        for ox, oy, val, label in output_nodes:
            glow = int(val * 180)
            pygame.draw.circle(surface, (30 + glow, 30 + glow, 30), (ox, oy), 8)
            pygame.draw.circle(surface, (255, 215, 0) if val > 0.4 else (120, 120, 120), (ox, oy), 8, width=1)
            # Label
            draw_text(surface, label, ox + 12, oy - 6, size=10, color=(220, 220, 220))
            # Draw percentage
            draw_text(surface, f"{int(val*100)}%", ox - 32, oy - 6, size=10, color=(160, 160, 160))

        # Draw explanation of synapse weights
        draw_text(surface, "Blue links: Positive / Excitatory (+)", x, y + 225, size=10, color=(0, 180, 255))
        draw_text(surface, "Red links: Negative / Inhibitory (-)", x, y + 240, size=10, color=(255, 90, 90))

    def draw_minimap(self, surface):
        """Draws a mini map of the 3200x3200 world in the bottom of the sidebar."""
        mx = WINDOW_WIDTH - SIDEBAR_WIDTH + 50
        my = 540
        mw, mh = 240, 160
        
        map_rect = pygame.Rect(mx, my, mw, mh)
        # Background
        draw_rounded_rect(surface, map_rect, (10, 10, 12), radius=0, border_color=COLORS["ui_border"])
        
        # Display viewport location as a green outline box
        # Scale factor (3200 tiles -> 240 pixels width = 13.3 tiles per pixel)
        scale_x = GRID_WIDTH / mw
        scale_y = GRID_HEIGHT / mh
        
        # Draw camera rectangle on minimap
        cam_x = self.game.camera_x / 24 # in tiles
        cam_y = self.game.camera_y / 24
        cam_w = (WINDOW_WIDTH - SIDEBAR_WIDTH) / 24
        cam_h = (WINDOW_HEIGHT - BOTTOM_PANEL_HEIGHT) / 24
        
        mcx = int(mx + cam_x / scale_x)
        mcy = int(my + cam_y / scale_y)
        mcw = max(4, int(cam_w / scale_x))
        mch = max(4, int(cam_h / scale_y))
        
        pygame.draw.rect(surface, (46, 204, 113), (mcx, mcy, mcw, mch), width=1)
        
        # Draw entities as tiny dots on minimap
        for ent in self.game.entities:
            px = int(mx + ent.x / scale_x)
            py = int(my + ent.y / scale_y)
            if map_rect.collidepoint(px, py):
                pygame.draw.rect(surface, ent.color, (px, py, 2, 2))
                
        draw_text(surface, "MINI-MAP (3200x3200)", mx, my - 18, size=12, color=COLORS["ui_text_dim"])

    def handle_click(self, mouse_pos):
        # Click on paintbrush toolbar slots
        tb_x, tb_y = 20, 20
        slot_size = 38
        gap = 10
        from src.config import TILE_WALL, TILE_GRASS, TILE_WATER, TILE_DIRT, TILE_WASTELAND, TILE_FLOOR
        slots_types = [TILE_WALL, TILE_GRASS, TILE_WATER, TILE_DIRT, TILE_WASTELAND, TILE_FLOOR, "beacon"]
        for i in range(7):
            curr_x = tb_x + 10 + i * (slot_size + gap)
            slot_rect = pygame.Rect(curr_x, tb_y + 10, slot_size, slot_size)
            if slot_rect.collidepoint(mouse_pos):
                self.game.active_brush_tile = slots_types[i]
                return True

        # Click on text inputs in customizer
        x = WINDOW_WIDTH - SIDEBAR_WIDTH + 20
        name_rect = pygame.Rect(x, 103, 300, 24)
        role_rect = pygame.Rect(x, 153, 300, 24)
        
        # Checkbox regions in customizer
        solar_rect = pygame.Rect(x, 250, 240, 16)
        shield_rect = pygame.Rect(x, 270, 240, 16)
        
        if not self.game.selected_android:
            if name_rect.collidepoint(mouse_pos):
                self.editing_field = "name"
                return True
            elif role_rect.collidepoint(mouse_pos):
                self.editing_field = "role"
                return True
            elif solar_rect.collidepoint(mouse_pos):
                self.custom_solar = not self.custom_solar
                return True
            elif shield_rect.collidepoint(mouse_pos):
                self.custom_shield = not self.custom_shield
                return True
            else:
                self.editing_field = None
                
        # Auto-reward checkbox click
        if self.game.selected_android:
            ar_rect_click = pygame.Rect(x, 187, 240, 16) # y offset calculation matching visualizer
            if ar_rect_click.collidepoint(mouse_pos):
                self.auto_reward = not self.auto_reward
                return True
                
        # Handle regular buttons
        for key, btn in self.buttons.items():
            # Skip inactive RLHF buttons
            if (key.startswith("rlhf")) and not self.game.selected_android:
                continue
                
            if btn.rect.collidepoint(mouse_pos):
                self.trigger_button_callback(key)
                return True
                
        return False

    def handle_keyboard(self, event):
        if not self.editing_field:
            return False
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                self.editing_field = None
            elif event.key == pygame.K_BACKSPACE:
                if self.editing_field == "name":
                    self.custom_name = self.custom_name[:-1]
                elif self.editing_field == "role":
                    self.custom_role = self.custom_role[:-1]
            else:
                if len(event.unicode) > 0:
                    if self.editing_field == "name" and len(self.custom_name) < 18:
                        self.custom_name += event.unicode
                    elif self.editing_field == "role" and len(self.custom_role) < 18:
                        self.custom_role += event.unicode
            return True
        return False

    def trigger_button_callback(self, key):
        from src.config import (
            PRESET_DEFAULT, PRESET_NUCLEAR, PRESET_ZOMBIE, PRESET_NO_SUN, PRESET_NO_HUMANS, PRESET_NO_ANIMALS
        )
        
        if key.startswith("preset_"):
            preset_name = key.replace("preset_", "")
            mapping = {
                "default": PRESET_DEFAULT,
                "nuclear": PRESET_NUCLEAR,
                "zombie": PRESET_ZOMBIE,
                "no_sun": PRESET_NO_SUN,
                "no_human": PRESET_NO_HUMANS,
                "no_animal": PRESET_NO_ANIMALS
            }
            target_preset = mapping.get(preset_name, PRESET_DEFAULT)
            self.game.change_preset(target_preset)
            
        elif key == "play_pause":
            self.game.paused = not self.game.paused
            self.buttons["play_pause"].text = "Play" if self.game.paused else "Pause"
            
        elif key == "clear_world":
            self.game.clear_world()
            
        elif key == "spawn_human":
            self.game.spawn_entity_in_center("human")
        elif key == "spawn_zombie":
            self.game.spawn_entity_in_center("zombie")
        elif key == "spawn_android":
            self.game.spawn_entity_in_center("android")
        elif key == "spawn_charger":
            self.game.spawn_entity_in_center("charger")
            
        elif key == "rlhf_reward":
            if self.game.selected_android:
                self.game.selected_android.brain.apply_rlhf_feedback(1.0)
                self.game.selected_android.rewards_count += 1
                
        elif key == "rlhf_punish":
            if self.game.selected_android:
                self.game.selected_android.brain.apply_rlhf_feedback(-1.0)
                self.game.selected_android.punishments_count += 1
                
        elif key == "customizer_create":
            # Spawn a customized android
            self.game.spawn_customized_android(self.custom_name, self.custom_role, "Custom")
            if self.game.selected_android:
                self.game.selected_android.has_solar_panel = self.custom_solar
                self.game.selected_android.has_rad_shield = self.custom_shield
            
        elif key == "deselect_entity":
            self.game.selected_entity = None
            self.game.selected_android = None

    def draw_viewport_legend(self, surface):
        """Draws a beautiful floating panel showing the color codes of all entities."""
        w, h = 180, 175
        x = self.game.view_w - w - 20
        y = 20
        
        rect = pygame.Rect(x, y, w, h)
        # Translucent dark glass background with border
        draw_rounded_rect(surface, rect, COLORS["ui_bg"], radius=0, border_color=COLORS["ui_border"], border_width=1)
        
        # Title
        draw_text(surface, "ENTITY LEGEND", x + w // 2, y + 10, size=12, color=COLORS["ui_accent"], align="center")
        pygame.draw.line(surface, COLORS["ui_border"], (x + 15, y + 26), (x + w - 15, y + 26), 1)
        
        # Legend items
        legend_items = [
            ("human", "Human (Survivor)"),
            ("zombie", "Zombie (Infected)"),
            ("animal", "Animal (Prey)"),
            ("android", "Neural Android"),
            ("charger", "Battery Charger"),
            ("food", "Food Supply")
        ]
        
        start_y = y + 34
        for key, name in legend_items:
            color = COLORS[key]
            # Draw circle
            pygame.draw.circle(surface, color, (x + 22, start_y + 8), 6)
            pygame.draw.circle(surface, (255, 255, 255, 100), (x + 22, start_y + 8), 6, width=1)
            # Draw text
            draw_text(surface, name, x + 38, start_y, size=11, color=COLORS["ui_text"])
            start_y += 22

    def draw_tile_toolbar(self, surface):
        """Draws a floating toolbar at the top-left showing the available paintbrush slots."""
        from src.config import TILE_WALL, TILE_GRASS, TILE_WATER, TILE_DIRT, TILE_WASTELAND, TILE_FLOOR
        
        # Toolbar slots configurations (Includes Beacon Slot 7)
        slots = [
            (TILE_WALL, "Wall", "1"),
            (TILE_GRASS, "Grass", "2"),
            (TILE_WATER, "Water", "3"),
            (TILE_DIRT, "Dirt", "4"),
            (TILE_WASTELAND, "Rad Soil", "5"),
            (TILE_FLOOR, "Floor", "6"),
            ("beacon_brush", "Beacon", "7")
        ]
        
        slot_size = 38
        gap = 10
        total_w = len(slots) * (slot_size + gap) + 10
        h = 68
        
        x = 20
        y = 20
        
        # Draw background panel
        bg_rect = pygame.Rect(x, y, total_w, h)
        draw_rounded_rect(surface, bg_rect, COLORS["ui_bg"], radius=0, border_color=COLORS["ui_border"])
        
        # Draw slots
        curr_x = x + 10
        for tile_id, name, hotkey in slots:
            slot_rect = pygame.Rect(curr_x, y + 10, slot_size, slot_size)
            
            # Highlight selected slot
            is_selected = (self.game.active_brush_tile == tile_id or (tile_id == "beacon_brush" and self.game.active_brush_tile == "beacon"))
            
            # Outer slot frame
            border_col = COLORS["ui_accent"] if is_selected else COLORS["ui_border"]
            border_w = 2 if is_selected else 1
            draw_rounded_rect(surface, slot_rect, (30, 30, 35), radius=0, border_color=border_col, border_width=border_w)
            
            # Inner tile preview block
            preview_rect = pygame.Rect(curr_x + 6, y + 16, slot_size - 12, slot_size - 12)
            color = COLORS["beacon"] if tile_id == "beacon_brush" else COLORS[tile_id]
            pygame.draw.rect(surface, color, preview_rect)
            
            # Hotkey label (top right corner of slot)
            draw_text(surface, hotkey, curr_x + slot_size - 5, y + 12, size=9, color=COLORS["ui_accent"], align="right")
            
            # Draw slot tile name as a paintbrush legend under the slot
            draw_text(surface, name, curr_x + slot_size // 2, y + 52, size=9, color=COLORS["ui_text_dim"], align="center")
            
            curr_x += slot_size + gap
            
        # Draw label next to toolbar
        draw_text(surface, "Paintbrush Toolbar (Keys 1-7)", x + 10, y + h + 4, size=11, color=COLORS["ui_text_dim"])

    def draw_general_inspector(self, surface, x):
        ent = self.game.selected_entity
        if not ent or ent.is_dead:
            self.game.selected_entity = None
            return
            
        # Title based on entity type
        titles = {
            "human": "SURVIVOR: HUMAN",
            "zombie": "MUTANT: ZOMBIE",
            "animal": "FAUNA: WILD ANIMAL",
            "food": "RESOURCE: FOOD SCRAPS",
            "charger": "INFRASTRUCTURE: CHARGER",
            "wolf": "PREDATOR: WOLF",
            "beacon": "TACTICAL: TARGET BEACON"
        }
        title_text = titles.get(ent.type, "ENTITY STATUS")
        draw_text(surface, title_text, x, 55, size=15, color=COLORS["ui_accent"])
        
        # Divider line
        pygame.draw.line(surface, COLORS["ui_border"], (WINDOW_WIDTH - SIDEBAR_WIDTH + 15, 80), (WINDOW_WIDTH - 15, 80), 1)
        
        y_offset = 95
        
        # Position
        draw_text(surface, f"Location: X:{int(ent.x)}, Y:{int(ent.y)}", x, y_offset, size=13, color=COLORS["ui_text_dim"])
        y_offset += 25
        
        # Health bar (if applicable)
        if hasattr(ent, "health"):
            draw_text(surface, f"Health: {int(ent.health)}%", x, y_offset, size=12)
            h_bar_rect = pygame.Rect(x + 90, y_offset + 3, 190, 10)
            draw_rounded_rect(surface, h_bar_rect, (40, 40, 50), radius=0)
            h_active = pygame.Rect(x + 90, y_offset + 3, int(max(0, ent.health) / 100.0 * 190), 10)
            draw_rounded_rect(surface, h_active, (50, 255, 50), radius=0)
            y_offset += 25
            
        # Hunger bar (if applicable)
        if hasattr(ent, "hunger"):
            label_h = "Hunger:" if ent.type == "wolf" else "Energy:"
            draw_text(surface, f"{label_h} {int(ent.hunger)}%", x, y_offset, size=12)
            b_bar_rect = pygame.Rect(x + 90, y_offset + 3, 190, 10)
            draw_rounded_rect(surface, b_bar_rect, (40, 40, 50), radius=0)
            b_active = pygame.Rect(x + 90, y_offset + 3, int(max(0, ent.hunger) / 100.0 * 190), 10)
            draw_rounded_rect(surface, b_active, COLORS["ui_accent"], radius=0)
            y_offset += 25
            
        # Behavior State
        state_text = getattr(ent, "state", "Static")
        draw_text(surface, f"Activity: {state_text.upper()}", x, y_offset, size=13, color=COLORS["ui_text"])
        y_offset += 25
        
        # Specific Extra Status
        if ent.type == "human":
            # Check infection status
            if ent.infection_timer >= 0:
                sec_left = ent.infection_timer // 60
                inf_text = f"INFECTED (Turns in {sec_left}s)"
                inf_col = (255, 50, 50)
            else:
                inf_text = "HEALTHY"
                inf_col = (50, 255, 50)
            draw_text(surface, f"Condition: {inf_text}", x, y_offset, size=13, color=inf_col)
            y_offset += 25
            
        elif ent.type == "zombie":
            draw_text(surface, "Radiation: IMMUNE / ABSORB", x, y_offset, size=13, color=(50, 255, 50))
            y_offset += 25
            if ent.target:
                draw_text(surface, f"Targeting: {ent.target.type.upper()}", x, y_offset, size=13, color=COLORS["ui_accent"])
                y_offset += 25
                
        elif ent.type == "wolf":
            if ent.breed_cooldown > 0:
                breed_txt = f"Mating Cooldown: {ent.breed_cooldown//60}s"
            else:
                breed_txt = "Ready to Breed"
            draw_text(surface, f"Mating: {breed_txt}", x, y_offset, size=13, color=COLORS["ui_accent"])
            y_offset += 25
                
        elif ent.type == "charger":
            draw_text(surface, "Output: 100W Constant", x, y_offset, size=13, color=COLORS["ui_text_dim"])
            y_offset += 25
            
        elif ent.type == "food":
            draw_text(surface, "Caloric Value: +40% Energy", x, y_offset, size=13, color=COLORS["ui_text_dim"])
            y_offset += 25
            
        # Separator / Diagnostics Box
        y_offset += 15
        rect_readout = pygame.Rect(x, y_offset, 300, 100)
        draw_rounded_rect(surface, rect_readout, (15, 25, 15), radius=0, border_color=COLORS["ui_border"])
        
        draw_text(surface, "SYSTEM DIAGNOSTICS READOUT:", x + 10, y_offset + 8, size=11, color=COLORS["ui_accent"])
        draw_text(surface, f"UUID: {id(ent) % 1000000:06d}", x + 10, y_offset + 28, size=11, color=COLORS["ui_text_dim"])
        
        if hasattr(ent, "speed"):
            draw_text(surface, f"Velocity max: {ent.speed:.3f} px/f", x + 10, y_offset + 48, size=11, color=COLORS["ui_text_dim"])
            
        telemetry = "Telemetry: STABLE"
        if hasattr(ent, "health") and ent.health < 40:
            telemetry = "Telemetry: CRITICAL LEVEL"
        elif ent.type == "zombie":
            telemetry = "Telemetry: ANOMALOUS"
        draw_text(surface, telemetry, x + 10, y_offset + 68, size=11, color=(255, 50, 50) if "CRITICAL" in telemetry or "ANOMALOUS" in telemetry else COLORS["ui_text"])
