# Swarm Foraging Under Heat and Energy Constraint

This is a Mesa-based swarm model where agents search for food under heat and energy constraints.

## Key Ideas

* Local perception (radius = 1)
* Pheromone-based coordination (stigmergy)
* States: RESTING, EXPLORING, RETURNING

## Result
![Simulation Result](Initial_run_result.png)

## Setup and running
``` bash
## Requirements
- Python 3.10+
### Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
###  Install dependencies
pip install -r requirements.txt
### run  
solara run create.py
```

## Authors 
- Fahad Ali Jalil
- Chijioke Emem