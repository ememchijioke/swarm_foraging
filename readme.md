# Swarm Foraging Under Heat and Energy Constraint

This is a Mesa-based swarm model where agents search for food under heat and energy constraints.

## Key Ideas

* Local perception (radius = 1)
* Pheromone-based coordination (stigmergy)
* States: RESTING, EXPLORING, RETURNING

## Model Architecture & Logic
![Architecture](doc/Swarm-architecture.png)

### 1. Agent State
- **RESTING** : Agent stays at the nest to retain body temperature($T_i$). It then transitions to **EXPLORING** when temperature reaches minimum safe level $T_{min}$
- **EXPLORING** : The agenet searches for food using directional movement (One direction for 4-10 steps) to avoid the inneficiency in random wandering. 
- **RETURNING** : Triggered when food is found or the agent hits the return temperature threshold($T_{return} = 46°C$). 
### 2. Decentralized Coordination (Stigmergy)
 **Pheromone Deposition**  
  When an agent consumes food, the agent estimates local food richness of the area.
- **Weighted Trails**  
  Stronger pheromones are produced for richer food clusters. Strength = Base + (Richness * Factor)
- **Trail Following**  
  Nearby exploring agents follow stronger pheromone signals to exploit the known food areas.
### 3. Survival Constraints
- Temperature increases outside the nest
- Temperature decreases inside the nest
- Energy decreases every step
- Additional energy is lost during movement

An agent dies if:
- Energy ≤ 0
- Temperature ≥ critical threshold (Body temperature > 50c)

## Constraint Table
| Parameter | Value | Description |
|-----------|-------|-------------|
| Energy (Emax) | 100 | Initial metabolic reserve |
| Metabolic Decay | -1 / step | Constant energy loss |
| Movement Cost | -1 / step | Penalty for active displacement |
| Heat Gain | +0.5 / step | Thermal increase outside the nest |
| Critical Temp (Tcritical) | 50 | Death threshold |

## Stigmergy Working
![Simulation Result](doc/stigmergy.png)

## Experiment Result
Detailed screenshots of multiple runs are available in `/docs/results`.
| Swarm Size | Baseline (Thermal-Only Return) | Improved (Energy-Aware Return) | Net Gain |
|------------|--------------------------------|--------------------------------|----------|
| 40 Agents  | 84 steps                       | 84 steps                       | 0%       |
| 50 Agents  | 81 steps                       | 84 steps                       | +3%      |
| 60 Agents  | 80 steps                       | 85 steps                       | +5%      |


## Setup and running
``` bash
## Requirements
- Python 3.10+
- Mesa 3.5.1
- Solara(For visualization)
### Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
###  Install dependencies
pip install -r requirements.txt
### run  
solara run create.py
```

