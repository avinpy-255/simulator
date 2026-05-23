# Neural Network Brain with Policy Gradient RLHF Training
import numpy as np
import math

class NeuralBrain:
    def __init__(self, input_size=37, hidden_size=16, output_size=5, learning_rate=0.01):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.lr = learning_rate
        
        # Initialize weights and biases using Xavier initialization
        self.W1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, output_size) * np.sqrt(2.0 / hidden_size)
        self.b2 = np.zeros((1, output_size))
        
        # Action history buffer for RLHF
        # Stores tuples: (state_vector, chosen_action, action_probabilities_vector)
        self.history = []
        self.max_history_len = 300  # Save last 5 seconds of actions at 60 FPS (if ticked every frame)
        self.gamma = 0.98  # Discount factor for credit assignment
        
        # Store last activations for visualization
        self.last_inputs = np.zeros(input_size)
        self.last_hidden = np.zeros(hidden_size)
        self.last_outputs = np.zeros(output_size)

    def softmax(self, x):
        """Stable softmax calculation."""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

    def forward(self, state):
        """Forward propagation through the network.
        
        state: 1D array of shape (input_size,)
        """
        # Save input
        self.last_inputs = state.copy()
        
        # Reshape to 2D row vector
        x = state.reshape(1, -1)
        
        # Hidden layer (Tanh activation)
        h_input = np.dot(x, self.W1) + self.b1
        h = np.tanh(h_input)
        self.last_hidden = h[0].copy()
        
        # Output layer (Softmax probabilities)
        out_input = np.dot(h, self.W2) + self.b2
        probs = self.softmax(out_input)[0]
        self.last_outputs = probs.copy()
        
        return probs

    def select_action(self, state, explore=True):
        """Runs forward pass and selects action based on output probabilities."""
        probs = self.forward(state)
        
        # Ensure no negative/nan probabilities due to float inaccuracies
        probs = np.nan_to_num(probs)
        if np.sum(probs) > 0:
            probs = probs / np.sum(probs)
        else:
            probs = np.ones(self.output_size) / self.output_size
            
        if explore:
            # Sample action based on probabilities
            action = np.random.choice(self.output_size, p=probs)
        else:
            action = np.argmax(probs)
            
        # Store in history buffer
        self.history.append((state.copy(), action, probs.copy()))
        if len(self.history) > self.max_history_len:
            self.history.pop(0)
            
        return action

    def apply_rlhf_feedback(self, reward):
        """Applies Policy Gradient reinforcement learning update based on human feedback.
        
        reward: float (+1.0 for Reward / -1.0 for Punish)
        Uses temporal credit assignment where actions closer to the feedback event 
        receive a larger portion of the reward/punishment.
        """
        if not self.history:
            return

        # Initialize gradients
        dW1 = np.zeros_like(self.W1)
        db1 = np.zeros_like(self.b1)
        dW2 = np.zeros_like(self.W2)
        db2 = np.zeros_like(self.b2)
        
        # Backpropagate through history backwards (most recent action gets highest reward weight)
        num_steps = len(self.history)
        for t in range(num_steps):
            state, action, probs = self.history[t]
            
            # Distance from feedback event (most recent gets weight 1.0, decaying backwards)
            time_decay = self.gamma ** (num_steps - 1 - t)
            step_reward = reward * time_decay
            
            # Reshape vectors
            x = state.reshape(1, -1)
            h = np.tanh(np.dot(x, self.W1) + self.b1)
            
            # Gradient of Log-Likelihood of chosen action w.r.t. output logits:
            # d(log P(a))/d(logits) = e_a - P
            # Since we want to perform Gradient ASCENT on expected reward:
            # We scale this gradient by step_reward
            d_logits = np.zeros((1, self.output_size))
            d_logits[0, :] = -probs  # decrease probability for all actions
            d_logits[0, action] += 1.0  # increase probability for chosen action
            
            # Scale by reward value
            d_logits *= step_reward
            
            # Gradients of Output Layer
            dW2 += np.dot(h.T, d_logits)
            db2 += d_logits
            
            # Gradients backpropagated to hidden layer
            dh = np.dot(d_logits, self.W2.T)
            
            # Gradient w.r.t. hidden logits (derivative of Tanh is 1 - tanh^2)
            d_hidden_logits = dh * (1.0 - h * h)
            
            # Gradients of Input/Hidden Layer
            dW1 += np.dot(x.T, d_hidden_logits)
            db1 += d_hidden_logits

        # Apply gradient updates with learning rate (Gradient Ascent)
        self.W1 += self.lr * dW1
        self.b1 += self.lr * db1
        self.W2 += self.lr * dW2
        self.b2 += self.lr * db2

        # Clear history to avoid applying the same reward twice
        self.history.clear()

    def get_sensors_from_world(self, entity, world):
        """Constructs the 35-dimensional state representation for the android:
        
        - 8 directions (Up, Up-Right, Right, Down-Right, Down, Down-Left, Left, Up-Left)
        - For each direction, sense:
          1. Obstacle proximity (Wall, border)
          2. Food proximity (Food entity)
          3. Battery charger proximity (Charger entity)
          4. Zombie proximity (Zombie entity)
        - 3 Internal state metrics:
          1. Battery charge (0.0 to 1.0)
          2. Health (0.0 to 1.0)
          3. Radiation Level (0.0 to 1.0)
        """
        state = np.zeros(self.input_size)
        
        # Directions mapping (dx, dy)
        directions = [
            (0, -1),  # N
            (1, -1),  # NE
            (1, 0),   # E
            (1, 1),   # SE
            (0, 1),   # S
            (-1, 1),  # SW
            (-1, 0),  # W
            (-1, -1)  # NW
        ]
        
        max_dist = 8  # How far the android can "see" in tiles
        
        idx = 0
        for dx, dy in directions:
            # Initialize sensor readings (higher = closer, 0.0 = not found/far)
            obs_val = 0.0
            food_val = 0.0
            charge_val = 0.0
            zombie_val = 0.0
            
            # Cast ray up to max_dist tiles
            for step in range(1, max_dist + 1):
                tx = int(entity.x + dx * step)
                ty = int(entity.y + dy * step)
                
                # Check grid bounds
                if tx < 0 or tx >= world.width or ty < 0 or ty >= world.height:
                    if obs_val == 0.0:
                        obs_val = 1.0 / step
                    break
                    
                # Check walls
                from src.config import TILE_WALL
                if world.get_tile(tx, ty) == TILE_WALL:
                    if obs_val == 0.0:
                        obs_val = 1.0 / step
                
                # Check items and entities on this tile
                # Search active entities in world at (tx, ty)
                for other in world.get_entities_at(tx, ty):
                    if other.type == "food" and food_val == 0.0:
                        food_val = 1.0 / step
                    elif other.type == "charger" and charge_val == 0.0:
                        charge_val = 1.0 / step
                    elif other.type == "zombie" and zombie_val == 0.0:
                        zombie_val = 1.0 / step
                        
            # Populate array
            state[idx] = obs_val
            state[idx + 1] = food_val
            state[idx + 2] = charge_val
            state[idx + 3] = zombie_val
            idx += 4
            
        # Internal states
        state[32] = entity.battery / 100.0
        state[33] = entity.health / 100.0
        # Get radiation level at current position
        state[34] = world.get_radiation_at(int(entity.x), int(entity.y)) / 100.0
        
        # Relative TargetBeacon offsets (Inputs 35 and 36)
        beacon_dx = 0.0
        beacon_dy = 0.0
        nearest_beacon = None
        min_beacon_dist = 99999.0
        
        for chunk_list in world.entity_chunks.values():
            for other in chunk_list:
                if other.type == "beacon" and not other.is_dead:
                    d = math.hypot(other.x - entity.x, other.y - entity.y)
                    if d < min_beacon_dist:
                        min_beacon_dist = d
                        nearest_beacon = other
                        
        if nearest_beacon:
            # Normalized relative offset (max distance is 16.0 tiles for high-res pathing)
            beacon_dx = max(-1.0, min(1.0, (nearest_beacon.x - entity.x) / 16.0))
            beacon_dy = max(-1.0, min(1.0, (nearest_beacon.y - entity.y) / 16.0))
            
        state[35] = beacon_dx
        state[36] = beacon_dy
        
        return state
