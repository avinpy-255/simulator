# Entities for Nexus: Neural Survival Sandbox
import random
import math
import pygame
from src.config import (
    COLORS, TILE_WALL, TILE_GRASS, TILE_DIRT, TILE_WASTELAND, TILE_FLOOR,
    GRID_WIDTH, GRID_HEIGHT, TILE_SIZE, FLASHLIGHT_DECAY_RATE
)
from src.brain import NeuralBrain
from src.utils import distance

class BaseEntity:
    def __init__(self, x, y, ent_type):
        self.x = float(x)
        self.y = float(y)
        self.type = ent_type
        self.health = 100.0
        self.speed = 0.08
        self.color = COLORS.get(ent_type, (255, 255, 255))
        self.is_dead = False
        
        # Bounding box width/height in grid tiles (almost 1 tile)
        self.radius = 0.4

    def update(self, world, entities):
        pass

    def draw(self, surface, camera_x, camera_y):
        """Draws the entity as a beautiful anti-aliased circle on the surface."""
        from src.utils import world_to_screen
        sx, sy = world_to_screen(self.x + 0.5, self.y + 0.5, camera_x, camera_y)
        
        # Only draw if visible on screen (approximate check)
        rect = surface.get_rect()
        if 0 <= sx <= rect.width and 0 <= sy <= rect.height:
            # Drop shadow
            pygame.draw.circle(surface, (10, 10, 15, 100), (sx + 2, sy + 2), int(self.radius * TILE_SIZE))
            # Entity circle
            pygame.draw.circle(surface, self.color, (sx, sy), int(self.radius * TILE_SIZE))
            # Soft inner border
            pygame.draw.circle(surface, (255, 255, 255, 120), (sx, sy), int(self.radius * TILE_SIZE), width=1)

    def move_with_collision(self, dx, dy, world):
        """Moves the entity, preventing pass-through of solid TILE_WALL or boundary limits."""
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Grid boundaries
        new_x = max(0.1, min(GRID_WIDTH - 1.1, new_x))
        new_y = max(0.1, min(GRID_HEIGHT - 1.1, new_y))
        
        # A simple bounding box check on the surrounding 4 tiles of the player
        # Check X movement
        tile_x1 = int(new_x)
        tile_x2 = int(new_x + 0.99)
        tile_y1 = int(self.y)
        tile_y2 = int(self.y + 0.99)
        
        collision_x = False
        for tx in [tile_x1, tile_x2]:
            for ty in [tile_y1, tile_y2]:
                if world.get_tile(tx, ty) == TILE_WALL:
                    collision_x = True
                    break
        if not collision_x:
            self.x = new_x
            
        # Check Y movement
        tile_x1 = int(self.x)
        tile_x2 = int(self.x + 0.99)
        tile_y1 = int(new_y)
        tile_y2 = int(new_y + 0.99)
        
        collision_y = False
        for tx in [tile_x1, tile_x2]:
            for ty in [tile_y1, tile_y2]:
                if world.get_tile(tx, ty) == TILE_WALL:
                    collision_y = True
                    break
        if not collision_y:
            self.y = new_y

class Food(BaseEntity):
    def __init__(self, x, y):
        super().__init__(x, y, "food")
        self.radius = 0.25
        self.color = COLORS["food"]

class Charger(BaseEntity):
    def __init__(self, x, y):
        super().__init__(x, y, "charger")
        self.radius = 0.3
        self.color = COLORS["charger"]
        
    def draw(self, surface, camera_x, camera_y):
        """Override to draw a glowing charging station."""
        from src.utils import world_to_screen
        sx, sy = world_to_screen(self.x + 0.5, self.y + 0.5, camera_x, camera_y)
        
        # Pulsing circle
        time_ms = pygame.time.get_ticks()
        pulse = int(math.sin(time_ms * 0.006) * 3 + 7)
        
        # Outer glow
        glow_surf = pygame.Surface((pulse * 4, pulse * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 215, 0, 80), (pulse * 2, pulse * 2), pulse * 2)
        surface.blit(glow_surf, (sx - pulse * 2, sy - pulse * 2))
        
        # Center core
        pygame.draw.circle(surface, self.color, (sx, sy), int(self.radius * TILE_SIZE))
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), int(self.radius * TILE_SIZE * 0.5))

class Animal(BaseEntity):
    def __init__(self, x, y):
        super().__init__(x, y, "animal")
        self.hunger = 100.0
        self.state = "wander"  # wander, flee, graze
        self.wander_timer = 0
        self.wander_dir = (0, 0)
        self.speed = 0.06

    def update(self, world, entities):
        # Hunger depletion
        self.hunger -= 0.02
        if self.hunger <= 0:
            self.health -= 0.1
            self.hunger = 0
            
        if self.health <= 0:
            self.is_dead = True
            return
            
        # Radiation damage
        rad = world.get_radiation_at(int(self.x), int(self.y))
        if rad > 10.0:
            self.health -= rad * 0.01

        # Check for nearby predators (zombies, humans)
        predator = None
        min_dist = 5.0
        for ent in entities:
            if ent.type in ["zombie", "human"] and not ent.is_dead:
                d = distance(self.x, self.y, ent.x, ent.y)
                if d < min_dist:
                    min_dist = d
                    predator = ent
                    
        if predator:
            self.state = "flee"
            # Move away from predator
            dx = self.x - predator.x
            dy = self.y - predator.y
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                self.move_with_collision((dx/length) * self.speed * 1.5, (dy/length) * self.speed * 1.5, world)
            return

        # Grazing behavior
        tx, ty = int(self.x), int(self.y)
        if world.get_tile(tx, ty) == TILE_GRASS and self.hunger < 80.0:
            self.state = "graze"
            world.set_tile(tx, ty, TILE_DIRT)
            self.hunger = min(100.0, self.hunger + 30.0)
            return

        # Wandering behavior
        self.state = "wander"
        self.wander_timer -= 1
        if self.wander_timer <= 0:
            angle = random.uniform(0, 2 * math.pi)
            self.wander_dir = (math.cos(angle), math.sin(angle))
            self.wander_timer = random.randint(60, 180)
            
        self.move_with_collision(self.wander_dir[0] * self.speed, self.wander_dir[1] * self.speed, world)

class Human(BaseEntity):
    def __init__(self, x, y):
        super().__init__(x, y, "human")
        self.hunger = 100.0
        self.state = "wander"  # wander, search_food, flee, sleep
        self.target = None
        self.wander_timer = 0
        self.wander_dir = (0, 0)
        self.speed = 0.07
        self.infection_timer = -1  # Negative means healthy, positive counts down to turning zombie
        self.wood = 0
        self.flashlight_battery = 100.0

    def update(self, world, entities):
        # Human status decays
        self.hunger -= 0.025
        if self.hunger <= 0:
            self.health -= 0.15
            self.hunger = 0
            
        if self.health <= 0:
            self.is_dead = True
            return
            
        # Zombification timer
        if self.infection_timer > 0:
            self.infection_timer -= 1
            if self.infection_timer <= 0:
                self.is_dead = True
                return
                
        # Radiation damage
        rad = world.get_radiation_at(int(self.x), int(self.y))
        if rad > 10.0:
            self.health -= rad * 0.015

        # Flashlight battery drain
        if world.preset == "no_sun":
            self.flashlight_battery = max(0.0, self.flashlight_battery - FLASHLIGHT_DECAY_RATE)

        # Gather wood/scrap from terrain
        tx, ty = int(self.x), int(self.y)
        current_tile = world.get_tile(tx, ty)
        if current_tile == TILE_GRASS and self.wood < 8:
            if random.random() < 0.04:  # 4% chance per frame
                self.wood += 1
                world.set_tile(tx, ty, TILE_DIRT)
        elif current_tile in [TILE_WALL, TILE_FLOOR] and self.wood < 8:
            if random.random() < 0.02:  # Scavenge scrap
                self.wood += 1

        # Check for zombies
        zombie = None
        min_dist = 6.0
        for ent in entities:
            if ent.type == "zombie" and not ent.is_dead:
                d = distance(self.x, self.y, ent.x, ent.y)
                if d < min_dist:
                    min_dist = d
                    zombie = ent
                    
        if zombie:
            self.state = "flee"
            self.target = None
            
            # Place defensive barricades (costs 2 wood)
            if self.wood >= 2:
                dx = self.x - zombie.x
                dy = self.y - zombie.y
                length = math.hypot(dx, dy)
                if length > 0:
                    bx = int(self.x - (dx / length))
                    by = int(self.y - (dy / length))
                    if 0 <= bx < world.width and 0 <= by < world.height:
                        if world.get_tile(bx, by) in [TILE_GRASS, TILE_DIRT]:
                            world.set_tile(bx, by, TILE_WALL)
                            self.wood -= 2
            
            # Flee movement
            dx = self.x - zombie.x
            dy = self.y - zombie.y
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                self.move_with_collision((dx/length) * self.speed * 1.4, (dy/length) * self.speed * 1.4, world)
            return

        # Sleep at night
        if world.global_light < 15.0:
            self.state = "sleep"
            return

        # Search for food
        if self.hunger < 70.0:
            self.state = "search_food"
            # Find closest food
            closest_food = None
            closest_dist = 12.0
            for ent in entities:
                if ent.type == "food" and not ent.is_dead:
                    d = distance(self.x, self.y, ent.x, ent.y)
                    if d < closest_dist:
                        closest_dist = d
                        closest_food = ent
            
            if closest_food:
                self.target = closest_food
                # Move towards food
                dx = closest_food.x - self.x
                dy = closest_food.y - self.y
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    self.move_with_collision((dx/length) * self.speed, (dy/length) * self.speed, world)
                # Consume food if close
                if closest_dist < 0.8:
                    closest_food.is_dead = True
                    self.hunger = min(100.0, self.hunger + 40.0)
                    self.health = min(100.0, self.health + 10.0)
                    self.flashlight_battery = 100.0  # Recharge flashlight
                return

        # Wander
        self.state = "wander"
        self.wander_timer -= 1
        if self.wander_timer <= 0:
            angle = random.uniform(0, 2 * math.pi)
            self.wander_dir = (math.cos(angle), math.sin(angle))
            self.wander_timer = random.randint(40, 150)
            
        self.move_with_collision(self.wander_dir[0] * self.speed, self.wander_dir[1] * self.speed, world)

class Zombie(BaseEntity):
    def __init__(self, x, y):
        super().__init__(x, y, "zombie")
        self.state = "wander"  # wander, hunt
        self.target = None
        self.speed = 0.05
        self.wander_timer = 0
        self.wander_dir = (0, 0)

    def update(self, world, entities):
        # 1. Smash nearby walls if they block their path
        tx, ty = int(self.x), int(self.y)
        for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
            wx, wy = tx + dx, ty + dy
            if 0 <= wx < world.width and 0 <= wy < world.height:
                if world.get_tile(wx, wy) == TILE_WALL:
                    # Smash wall
                    if random.random() < 0.005:  # Smash in ~3.5 seconds
                        world.set_tile(wx, wy, TILE_DIRT)
                    self.state = "smashing"
                    return  # Stop and bash
                    
        # Search for humans or animals to hunt
        self.target = None
        closest_dist = 10.0
        for ent in entities:
            if ent.type in ["human", "animal"] and not ent.is_dead:
                d = distance(self.x, self.y, ent.x, ent.y)
                if d < closest_dist:
                    closest_dist = d
                    self.target = ent
                    
        if self.target:
            self.state = "hunt"
            # Move towards target
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            length = math.sqrt(dx*dx + dy*dy)
            if length > 0:
                self.move_with_collision((dx/length) * self.speed, (dy/length) * self.speed, world)
                
            # Attack if close
            if closest_dist < 0.7:
                self.target.health -= 0.6
                if self.target.type == "human" and random.random() < 0.05:
                    # Infect human
                    if self.target.infection_timer < 0:
                        self.target.infection_timer = random.randint(180, 500) # turns soon
            return

        # Wander
        self.state = "wander"
        self.wander_timer -= 1
        if self.wander_timer <= 0:
            angle = random.uniform(0, 2 * math.pi)
            self.wander_dir = (math.cos(angle), math.sin(angle))
            self.wander_timer = random.randint(60, 200)
            
        self.move_with_collision(self.wander_dir[0] * self.speed, self.wander_dir[1] * self.speed, world)

class NeuralAndroid(BaseEntity):
    def __init__(self, x, y, name="Android Alpha", role="Explorer", temperament="Balanced"):
        super().__init__(x, y, "android")
        self.name = name
        self.role = role
        self.temperament = temperament
        
        # Stats
        self.battery = 100.0  # Android energy
        self.health = 100.0
        self.speed = 0.09
        self.is_dormant = False
        
        # Modular upgrades
        self.has_solar_panel = False
        self.has_rad_shield = False
        self.flashlight_battery = 100.0
        
        # Neural Network Brain
        self.brain = NeuralBrain(learning_rate=0.01)
        
        # Training record count (stats for UI)
        self.rewards_count = 0
        self.punishments_count = 0
        
        # Sensor inputs cache for visualization
        self.current_state_vector = None

    def update(self, world, entities):
        if self.health <= 0:
            self.is_dead = True
            return
            
        # Radiation damage (Rad shield ignores this)
        rad = world.get_radiation_at(int(self.x), int(self.y))
        if rad > 10.0 and not self.has_rad_shield:
            self.health -= rad * 0.005

        # Battery drainage
        if not self.is_dormant:
            self.battery -= 0.05
            if self.battery <= 0:
                self.battery = 0
                self.is_dormant = True
                
            # Solar panel battery recharge in daylight
            if self.has_solar_panel:
                tile_l = world.get_light_at(int(self.x), int(self.y))
                if tile_l > 60.0:
                    self.battery = min(100.0, self.battery + 0.06)
                    
            # Flashlight drain in sunless preset
            if world.preset == "no_sun":
                self.flashlight_battery = max(0.0, self.flashlight_battery - FLASHLIGHT_DECAY_RATE)
        else:
            # In dormant state, check if placed or moved onto a charger to boot back up
            self.health -= 0.05
            self.speed = 0.0
            
        # Recharge if standing on charger
        for ent in entities:
            if ent.type == "charger" and not ent.is_dead:
                if distance(self.x, self.y, ent.x, ent.y) < 0.8:
                    self.battery = 100.0
                    self.flashlight_battery = 100.0  # Recharge flashlight
                    self.health = min(100.0, self.health + 0.2)
                    self.is_dormant = False
                    self.speed = 0.09
                    
        # Consume food if standing on food
        for ent in entities:
            if ent.type == "food" and not ent.is_dead:
                if distance(self.x, self.y, ent.x, ent.y) < 0.8:
                    ent.is_dead = True
                    self.health = min(100.0, self.health + 30)

        if self.is_dormant:
            return

        # Gather sensors inputs
        self.current_state_vector = self.brain.get_sensors_from_world(self, world)
        
        # Select action using Neural Network
        action = self.brain.select_action(self.current_state_vector)
        
        # Map actions:
        # 0: Move Up
        # 1: Move Down
        # 2: Move Left
        # 3: Move Right
        # 4: Idle / Stand Still
        dx, dy = 0.0, 0.0
        if action == 0:
            dy = -self.speed
        elif action == 1:
            dy = self.speed
        elif action == 2:
            dx = -self.speed
        elif action == 3:
            dx = self.speed
            
        if dx != 0.0 or dy != 0.0:
            self.move_with_collision(dx, dy, world)

    def draw(self, surface, camera_x, camera_y):
        """Draws the custom android."""
        super().draw(surface, camera_x, camera_y)
        
        # Draw a little sensor antenna indicator
        if not self.is_dormant:
            from src.utils import world_to_screen
            sx, sy = world_to_screen(self.x + 0.5, self.y + 0.5, camera_x, camera_y)
            # Pulse the antenna light
            time_ms = pygame.time.get_ticks()
            if int(time_ms / 300) % 2 == 0:
                pygame.draw.circle(surface, (255, 255, 255), (sx, sy - 6), 2)

class TargetBeacon(BaseEntity):
    def __init__(self, x, y):
        super().__init__(x, y, "beacon")
        self.radius = 0.3
        self.color = COLORS["beacon"]
        
    def draw(self, surface, camera_x, camera_y):
        from src.utils import world_to_screen
        sx, sy = world_to_screen(self.x + 0.5, self.y + 0.5, camera_x, camera_y)
        
        time_ms = pygame.time.get_ticks()
        pulse = int(math.sin(time_ms * 0.01) * 4 + 8)
        
        # Pulsing rings
        pygame.draw.circle(surface, (0, 255, 255, 60), (sx, sy), pulse * 2, width=1)
        pygame.draw.circle(surface, self.color, (sx, sy), int(self.radius * TILE_SIZE))
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 3)

class Wolf(BaseEntity):
    def __init__(self, x, y):
        super().__init__(x, y, "wolf")
        self.hunger = 100.0
        self.state = "wander"  # wander, hunt, breed
        self.target = None
        self.speed = 0.075
        self.wander_timer = 0
        self.wander_dir = (0, 0)
        self.breed_cooldown = 300

    def update(self, world, entities):
        self.hunger -= 0.03
        if self.hunger <= 0:
            self.health -= 0.2
            self.hunger = 0
        if self.health <= 0:
            self.is_dead = True
            return
            
        if self.breed_cooldown > 0:
            self.breed_cooldown -= 1
            
        rad = world.get_radiation_at(int(self.x), int(self.y))
        if rad > 10.0:
            self.health -= rad * 0.01

        # 1. Flee from zombies
        zombie = None
        min_z_dist = 6.0
        for ent in entities:
            if ent.type == "zombie" and not ent.is_dead:
                d = distance(self.x, self.y, ent.x, ent.y)
                if d < min_z_dist:
                    min_z_dist = d
                    zombie = ent
        if zombie:
            self.state = "flee"
            dx, dy = self.x - zombie.x, self.y - zombie.y
            length = math.hypot(dx, dy)
            if length > 0:
                self.move_with_collision((dx/length)*self.speed*1.4, (dy/length)*self.speed*1.4, world)
            return

        # 2. Reproduction check (breed if fed and no cooldown)
        if self.hunger > 80.0 and self.breed_cooldown <= 0:
            partner = None
            min_p_dist = 4.0
            for ent in entities:
                if isinstance(ent, Wolf) and ent != self and not ent.is_dead and ent.hunger > 80.0 and ent.breed_cooldown <= 0:
                    d = distance(self.x, self.y, ent.x, ent.y)
                    if d < min_p_dist:
                        min_p_dist = d
                        partner = ent
            if partner:
                self.state = "breed"
                dx, dy = partner.x - self.x, partner.y - self.y
                length = math.hypot(dx, dy)
                if length > 0:
                    self.move_with_collision((dx/length)*self.speed, (dy/length)*self.speed, world)
                if min_p_dist < 0.8:
                    # Spawn pup!
                    entities.append(Wolf(self.x + random.uniform(-0.5, 0.5), self.y + random.uniform(-0.5, 0.5)))
                    self.breed_cooldown = 600
                    partner.breed_cooldown = 600
                    self.hunger -= 40.0
                    partner.hunger -= 40.0
                return

        # 3. Hunt prey (Animal)
        if self.hunger < 75.0:
            self.state = "hunt"
            closest_prey = None
            min_prey_dist = 10.0
            for ent in entities:
                if ent.type == "animal" and not ent.is_dead:
                    d = distance(self.x, self.y, ent.x, ent.y)
                    if d < min_prey_dist:
                        min_prey_dist = d
                        closest_prey = ent
            if closest_prey:
                dx, dy = closest_prey.x - self.x, closest_prey.y - self.y
                length = math.hypot(dx, dy)
                if length > 0:
                    self.move_with_collision((dx/length)*self.speed*1.2, (dy/length)*self.speed*1.2, world)
                if min_prey_dist < 0.8:
                    closest_prey.is_dead = True
                    self.hunger = min(100.0, self.hunger + 55.0)
                    self.health = min(100.0, self.health + 20.0)
                return

        # 4. Wander
        self.state = "wander"
        self.wander_timer -= 1
        if self.wander_timer <= 0:
            angle = random.uniform(0, 2 * math.pi)
            self.wander_dir = (math.cos(angle), math.sin(angle))
            self.wander_timer = random.randint(60, 180)
        self.move_with_collision(self.wander_dir[0]*self.speed, self.wander_dir[1]*self.speed, world)
