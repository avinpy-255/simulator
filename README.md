# Nexus: Neural Survival Sandbox

Welcome to **Nexus: Neural Survival Sandbox**, a high-performance, top-down tactical ecosystem simulation built in Pygame on a massive **3200x3200 grid**. 

The simulation supports real-time survival presets, complex species interactions, dynamic lighting projections, and integrates **Customizable Neural Androids** powered by a Policy Gradient neural network that learns in real-time from user feedback (RLHF).

![Nexus Gameplay Screenshot](Screenshot%202026-05-23%20135237.png)

---

## 🎮 Core Features & Mechanics

### 1. Customizable Neural Androids (RLHF)
Androids make decisions using a Policy Gradient neural network (REINFORCE algorithm) mapping a 37-dimensional state vector to 5 possible actions (Move Up, Down, Left, Right, Idle).
- **Interactive Activations View**: Renders real-time node outputs and synaptic weights (Blue = positive, Red = negative).
- **Manual RLHF Training**: Apply `REWARD (+1)` or `PUNISH (-1)` buttons to shape their behavior in real-time.
- **Auto-Train Checklist**: Automatically guides androids to navigate to the closest **Target Beacon** via distance-based rewards (`+0.2`) and punishments (`-0.1`).

### 2. Environment Presets & Survival Scenarios
- **Default Preset**: A peaceful, lush grassland filled with grazing animals, survivors, and charging stations.
- **Nuclear Preset**: An irradiated wasteland where nuclear soil decays living entities. Androids can equip a **Rad-Shield** module to ignore radiation damage.
- **Zombie Preset**: Spawn infected mutants that hunt humans and animals. Survivors can spend wood resources to place **Wall barricades** to block zombies. Zombies will stay in place and smash blocking walls until they break.
- **No Sun Preset**: Plunges the grid into pitch darkness. Flashlights drain battery over time. Androids recharge at charging pads, while humans consume food. Crops/grass slowly decay into dirt in deep unlit areas.

### 3. Predator-Prey Ecology (`Wolf` Species)
Wolves hunt wild animals for energy. If a zombie approaches, they flee. Fed wolves with no breed cooldown reproduce organically when nearby.

### 4. Interactive Paintbrush Toolbar
Use hotkeys `1` through `7` or click directly on the toolbar to paint walls, grass, water, dirt, rad soil, concrete floor, or spawn target beacons on the grid in real-time.

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- Pygame-ce & NumPy

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Simulation
```bash
python main.py
```

### Run Tests
Verification tests check the neural network forward pass, RLHF backpropagation, and target beacon coordinate calculations:
```bash
python -m unittest tests/test_brain.py
```

---

## ⌨️ Controls Cheat Sheet
- **Scroll Viewport**: `W`, `A`, `S`, `D` or Arrow Keys
- **Reposition Entities**: Hold `D` + Left-Click and drag any entity
- **Select Entity**: Left-Click on any entity to view status and detailed telemetry diagnostics
- **Brush Selection**: Keys `1` - `7` (or click toolbar slots)
  - `1`: Wall
  - `2`: Grass
  - `3`: Water
  - `4`: Dirt
  - `5`: Rad Soil
  - `6`: Concrete Floor
  - `7`: Target Beacon
