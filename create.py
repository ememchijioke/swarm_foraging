# ==========================================
# model parameters & requirements (mini-project 1) 
# Fahad Ali Jalil Student Number: 12502261
# Chijioke Chukuemeka Emem Student Number: 12348404
# ==========================================
# environment:
# - grid size: adjustable, defaults to 60x60.
# - nest: one single nest right in the middle of the grid.
# - food: finite and doesn't respawn. covers 10% to 15% of the map.
# - food clusters: split into 10 to 12 groups.
#
# swarm (the creatures):
# - swarm size: anywhere from 40 to 60 (we default to 50).
# - starting stats: full energy and safe temp.
# - perception: strictly local. they can only see their own stats, the nest, and food within 1 block.
# - actions: they can move, stay still, eat, or drop pheromones (stigmergy).
# - environment effects: they heat up outside, cool down inside the nest, and constantly lose energy.
# - death: they die if energy hits 0 or if they get too hot.
# - simulation end: it only stops when every single creature is dead.
# ==========================================

import mesa
from mesa.visualization import SolaraViz, make_space_component, make_plot_component
import random
import solara

# constants
E_MAX = 100
T_SAFE = 37
T_CRIT = 50
T_MIN = 30

### Params
T_RETURN = 46
BASE_ENERGY_DECAY = 1
MOVE_ENERGY_COST = 1
HEAT_GAIN_OUTSIDE = 0.5
COOL_RATE_IN_NEST = 2.0
FOOD_ENERGY_GAIN = 50
PHEROMONE_BASE_STRENGTH = 40
PHEROMONE_RICHNESS_FACTOR = 8
PHEROMONE_DECAY = 5
DIRECTION_TIMER_MIN = 4
DIRECTION_TIMER_MAX = 10

# 1. agents

class Food(mesa.Agent):

    """agent representing finite, non renewable food."""

    def __init__(self, model):
        super().__init__(model)


class Pheromone(mesa.Agent):
    """agent representing a trace left by the ants"""
### Removed hardcoded strength and replaced with a parameter than can be adjusted above with the param list.(Pheromone base strength and decay) 
    def __init__(self, model,strength=PHEROMONE_BASE_STRENGTH):
        super().__init__(model)
        self.strength = strength

    def step(self):
        self.strength -= PHEROMONE_DECAY
        if self.strength <= 0:
            self.model.grid.remove_agent(self)
            self.model.agents.remove(self)


class CreatureAgent(mesa.Agent):
    """smarter agent using state machines, stigmergy, and momentum"""

    def __init__(self, model):
        super().__init__(model)
        self.energy = E_MAX
        self.temperature = T_SAFE
        self.is_alive = True

        # State Machine
        self.state = "RESTING"

###Changed the exploration to make it more directional so they don't just bounce around but they can be more directional        # Momentum variables
        #self.explore_target = None
        # self.explore_timer = 0
        self.direction =  None
        self.direction_timer = 0
###  Added this line for the agents to remember how rich/dense the last food discovered area was. 
        self.last_food_richness = 0
    
    
    def step(self):
        if not self.is_alive:
            return

        at_nest = (self.pos == self.model.nest_pos)

        # state transition
        if self.state == "RESTING":
            if self.temperature <= T_MIN:
                self.state = "EXPLORING"

        elif self.state == "EXPLORING":
            if self.temperature > T_RETURN or self.energy < 25: ### I changed this to remove hardcoding to enable flexibility in adjusting the return temperation
                ### Added new return logic for a more dynamic return trigger based ion low energy levels. 
                self.state = "RETURNING"

        elif self.state == "RETURNING":
            if at_nest:
                self.state = "RESTING"

### Removed all the hardcoding present here as well. The agents will now heat up, cool down, and lose energy based on the parameters defined above.  
        # Other enviornment drain
        if at_nest:
            self.temperature = max(T_MIN, self.temperature - COOL_RATE_IN_NEST)
        else:
            self.temperature += HEAT_GAIN_OUTSIDE

        self.energy -= BASE_ENERGY_DECAY

        # death parameters
        if self.energy <= 0 or self.temperature >= T_CRIT:
            self.is_alive = False
            self.model.grid.remove_agent(self)
            self.model.agents.remove(self)
            return

        # action based on state
        if self.state == "RESTING":
            pass

        elif self.state == "RETURNING":
            possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
            if possible_steps:
                best_step = min(
                    possible_steps,
                    key=lambda p: abs(p[0] - self.model.nest_pos[0]) + abs(p[1] - self.model.nest_pos[1])
                )

                ### ADDED: drop pheromone while returning
                trail_strength = PHEROMONE_BASE_STRENGTH + PHEROMONE_RICHNESS_FACTOR * self.last_food_richness
                self.model.drop_pheromone(self.pos, strength=trail_strength)

                self.model.grid.move_agent(self, best_step)
                self.energy -= MOVE_ENERGY_COST
            
        elif self.state == "EXPLORING":
            neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=True, radius=1)

            food_here = [obj for obj in neighbors if isinstance(obj, Food) and obj.pos == self.pos]
            food_near = [obj for obj in neighbors if isinstance(obj, Food) and obj.pos != self.pos]
            pheromones_near = [obj for obj in neighbors if isinstance(obj, Pheromone) and obj.pos != self.pos]

            if len(food_here) > 0:
                food_item = food_here[0]
                
                ### ADDED estimate local food richness
                local_richness = self.model.count_food_around(self.pos, radius=1)
                self.last_food_richness = local_richness
                
                self.energy = min(E_MAX, self.energy + FOOD_ENERGY_GAIN)
                
               ### self.model.grid.remove_agent(food_item) ### Changed this to use the helper function for safe removal that I added to the model. 
                self.model.remove_world_agent(food_item)
                
               ### self.last_food_richness = food_item.richness ### Remeber how rich the food is. 
                ### self.model.agents.remove(food_item)
                ### self.model.drop_pheromone(self.pos)
            
                ### Added this line to make the agents drop stronger pheromones if the food they found was richer. 
                strength = PHEROMONE_BASE_STRENGTH + PHEROMONE_RICHNESS_FACTOR * local_richness
                self.model.drop_pheromone(self.pos, strength=strength)
                self.state = "RETURNING"

            elif len(food_near) > 0:
                    ### ADDED: prefer food cell that seems locally richer
                best_food = max(
                    food_near,
                    key=lambda f: self.model.count_food_around(f.pos, radius=1)
                )
                self.model.grid.move_agent(self, best_food.pos)
                self.energy -= MOVE_ENERGY_COST

            elif len(pheromones_near) > 0:
                best_pheromone = max(pheromones_near, key=lambda p: p.strength)
                self.model.grid.move_agent(self, best_pheromone.pos)
                self.energy -= MOVE_ENERGY_COST

            else:
                possible_steps = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
                if possible_steps:
                    ### CHANGED: direction-based movement instead of explore_target momentum
                    if self.direction is None or self.direction_timer <= 0:
                        self.direction = self.random.choice([
                            (-1, -1), (-1, 0), (-1, 1),
                            (0, -1),           (0, 1),
                            (1, -1),  (1, 0),  (1, 1)
                        ])
                        self.direction_timer = self.random.randint(DIRECTION_TIMER_MIN, DIRECTION_TIMER_MAX)

                    next_x = self.pos[0] + self.direction[0]
                    next_y = self.pos[1] + self.direction[1]

                    next_x = min(max(next_x, 0), self.model.grid.width - 1)
                    next_y = min(max(next_y, 0), self.model.grid.height - 1)
                    next_pos = (next_x, next_y)

                    if next_pos != self.pos:
                        self.model.grid.move_agent(self, next_pos)
                        self.energy -= MOVE_ENERGY_COST  # >>> CHANGED

                    self.direction_timer -= 1


# 2. Model overview

class SwarmModel(mesa.Model):
    def __init__(self, num_agents=50, width=60, height=60, seed=None):
        super().__init__(seed=seed)
        self.num_agents = num_agents

        self.grid = mesa.space.MultiGrid(width, height, torus=False)
        self.nest_pos = (width // 2, height // 2)

        for _ in range(self.num_agents):
            a = CreatureAgent(self)
            self.grid.place_agent(a, self.nest_pos)

        self.generate_food_clusters(width, height)

        # Data collection
        # This tells Mesa to count up these statistics every single frame
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Alive": lambda m: sum(1 for a in m.agents if isinstance(a, CreatureAgent)),
                "Dead": lambda m: m.num_agents - sum(1 for a in m.agents if isinstance(a, CreatureAgent)),
                "Pheromones": lambda m: sum(1 for a in m.agents if isinstance(a, Pheromone)),
                ### ADDED: better analysis metrics
                "Food Remaining": lambda m: sum(1 for a in m.agents if isinstance(a, Food)),
                "Average Energy": lambda m: (
                    sum(a.energy for a in m.agents if isinstance(a, CreatureAgent)) /
                    max(1, sum(1 for a in m.agents if isinstance(a, CreatureAgent)))
                ),
                "Average Temperature": lambda m: (
                    sum(a.temperature for a in m.agents if isinstance(a, CreatureAgent)) /
                    max(1, sum(1 for a in m.agents if isinstance(a, CreatureAgent)))
                ),
                "Resting": lambda m: sum(1 for a in m.agents if isinstance(a, CreatureAgent) and a.state == "RESTING"),
                "Exploring": lambda m: sum(1 for a in m.agents if isinstance(a, CreatureAgent) and a.state == "EXPLORING"),
                "Returning": lambda m: sum(1 for a in m.agents if isinstance(a, CreatureAgent) and a.state == "RETURNING"),
            }
        )
        # Collect the initial state at step 0
        self.datacollector.collect(self)

 #Added a helper for safe removal everywhere
    def remove_world_agent(self, agent):
        self.grid.remove_agent(agent)
        self.agents.remove(agent)
        
    def drop_pheromone(self, pos, strength=PHEROMONE_BASE_STRENGTH):
        p = Pheromone(self, strength=strength)
        self.grid.place_agent(p, pos)

    #Added supports for richness estimation
    def count_food_around(self, pos, radius=1):
        neighbors = self.grid.get_neighbors(pos, moore=True, include_center=True, radius=radius)
        return sum(1 for obj in neighbors if isinstance(obj, Food))

    def generate_food_clusters(self, width, height):
        target_food_cells = self.random.randint(360, 540)
        num_clusters = self.random.randint(10, 12)
        cells_per_cluster = target_food_cells // num_clusters

        for _ in range(num_clusters):
            cx, cy = random.randrange(width), random.randrange(height)
            for _ in range(cells_per_cluster):
                cx = min(max(cx + random.randint(-1, 1), 0), width - 1)
                cy = min(max(cy + random.randint(-1, 1), 0), height - 1)

                cell_contents = self.grid.get_cell_list_contents((cx, cy))
                if not any(isinstance(obj, Food) for obj in cell_contents):
                    f = Food(self)
                    self.grid.place_agent(f, (cx, cy))

    def step(self):
        self.agents.shuffle_do("step")

        # Save the data for this frame to draw the graphs
        self.datacollector.collect(self)

        creatures_alive = sum(1 for a in self.agents if isinstance(a, CreatureAgent))
        if creatures_alive == 0:
            self.running = False


# 3. (UI & GRAPHS)

def agent_portrayal(agent):
    # Dynamic Colors based on State Machine
    if isinstance(agent, CreatureAgent):
        if agent.state == "RESTING":
            return {"color": "blue", "marker": "o", "size": 50}
        elif agent.state == "EXPLORING":
            return {"color": "orange", "marker": "o", "size": 50}
        elif agent.state == "RETURNING":
            return {"color": "red", "marker": "o", "size": 50}

    elif isinstance(agent, Food):
        return {"color": "green", "marker": "s", "size": 40}

    elif isinstance(agent, Pheromone):
        size = max(10, (agent.strength / 100) * 40)
        return {"color": "purple", "marker": "s", "size": size}

    return {}


# legends
def legend_component(model):
    """Uses Solara Markdown to draw a legend above the grid."""
    return solara.Markdown('''
    ### Swarm Legend
    * **Blue Circle:** Resting in Nest (Cooling down)
    * **Orange Circle:** Exploring for Food
    * **Red Circle:** Returning to Nest (Heating up)
    * **Green Square:** Food Cluster
    * **Purple Square:** Pheromone Trail
    ''')


# CHANGED but kept same place in code, but upgraded to sliders for easier experimentation
model_params = {
    "num_agents": {
        "type": "SliderInt",
        "value": 50,
        "label": "Number of Creatures",
        "min": 40,
        "max": 60,
        "step": 1,
    },
    "width": {
        "type": "SliderInt",
        "value": 60,
        "label": "Grid Width",
        "min": 30,
        "max": 100,
        "step": 5,
    },
    "height": {
        "type": "SliderInt",
        "value": 60,
        "label": "Grid Height",
        "min": 30,
        "max": 100,
        "step": 5,
    }
}

# This add the Legend and the two Plots into the Solara UI
page = SolaraViz(
    SwarmModel(num_agents=50, width=60, height=60),
    components=[
        legend_component,
        make_space_component(agent_portrayal),
        make_plot_component({"Alive": "blue", "Dead": "red"}),  # Graph 1: Population
        
        ### Expanded this
make_plot_component({"Pheromones": "purple", "Food Remaining": "green"}),
        make_plot_component({"Resting": "blue", "Exploring": "orange", "Returning": "red"}),
        make_plot_component({"Average Energy": "black", "Average Temperature": "brown"})    ],
    model_params=model_params,
    name="Swarm Survival Simulation"
)