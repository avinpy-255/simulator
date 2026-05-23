# Unit tests for NeuralBrain and RLHF updates
import unittest
import numpy as np
from src.brain import NeuralBrain

class TestNeuralBrain(unittest.TestCase):
    def setUp(self):
        # Create a brain with a small structure for testing speed
        self.brain = NeuralBrain(input_size=10, hidden_size=5, output_size=3, learning_rate=0.1)

    def test_forward_pass(self):
        # Generate random state
        state = np.random.rand(10)
        probs = self.brain.forward(state)
        
        # Output probabilities must sum to 1.0
        self.assertAlmostEqual(np.sum(probs), 1.0, places=5)
        self.assertEqual(len(probs), 3)
        self.assertTrue(np.all(probs >= 0.0))

    def test_select_action(self):
        state = np.random.rand(10)
        action = self.brain.select_action(state, explore=True)
        
        # Verify action fits range
        self.assertTrue(0 <= action < 3)
        # Check that action was added to history
        self.assertEqual(len(self.brain.history), 1)

    def test_rlhf_reward_learning(self):
        """Verifies that positive reward increases action probability."""
        state = np.ones(10) * 0.5
        
        # First pass
        probs_before = self.brain.forward(state).copy()
        
        # Select action manually to force it
        # We append to history manually: (state, action, probabilities)
        action = 1
        self.brain.history.append((state.copy(), action, probs_before.copy()))
        
        # Apply positive reward
        self.brain.apply_rlhf_feedback(1.0)
        
        # Second pass (same state)
        probs_after = self.brain.forward(state)
        
        # Probability of action 1 should be HIGHER
        self.assertGreater(probs_after[action], probs_before[action])

    def test_rlhf_punish_learning(self):
        """Verifies that negative punishment decreases action probability."""
        state = np.ones(10) * 0.5
        
        # First pass
        probs_before = self.brain.forward(state).copy()
        
        # Select action manually
        action = 2
        self.brain.history.append((state.copy(), action, probs_before.copy()))
        
        # Apply negative reward (punishment)
        self.brain.apply_rlhf_feedback(-1.0)
        
        # Second pass
        probs_after = self.brain.forward(state)
        
        # Probability of action 2 should be LOWER
        self.assertLess(probs_after[action], probs_before[action])

    def test_default_dimensions_and_beacons(self):
        """Test default 37-dimensional state extraction and target beacon relative coordinates."""
        # Initialize default brain
        default_brain = NeuralBrain()
        self.assertEqual(default_brain.input_size, 37)
        self.assertEqual(default_brain.output_size, 5)
        
        # Mock world and entity
        from src.world import World
        from src.entities import NeuralAndroid, TargetBeacon
        world = World()
        
        android = NeuralAndroid(10, 10)
        # Place a target beacon at (15, 6)
        beacon = TargetBeacon(15, 6)
        world.update_entity_chunks([android, beacon])
        
        # Get sensor state
        state = default_brain.get_sensors_from_world(android, world)
        
        # Verify shape
        self.assertEqual(state.shape, (37,))
        
        # Inputs 35 and 36 must be relative normalized coordinates
        # nearest beacon is (15, 6), android is (10, 10)
        # dx = (15 - 10) / 16.0 = 5 / 16.0 = 0.3125
        # dy = (6 - 10) / 16.0 = -4 / 16.0 = -0.25
        self.assertAlmostEqual(state[35], 0.3125, places=5)
        self.assertAlmostEqual(state[36], -0.25, places=5)

if __name__ == "__main__":
    unittest.main()
