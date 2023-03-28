import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from point2d import Point2D
import matplotlib
from matplotlib import animation
from datetime import datetime
from enum import Enum
from abc import ABC


class Status(Enum):
    SUSCEPTIBLE = 1
    INFECTED = 2
    RECOVERED = 3


class Agent(ABC):
    def __init__(self, id, position: Point2D, target_position: Point2D, velocity):
        self.id = id
        self.position = position
        self.target_position = target_position
        self.velocity = velocity
        self.step = self.calculate_step()

    def calculate_step(self):
        if self.target_position.x == self.position.x and \
           self.target_position.y == self.position.y:
            return Point2D(0, 0)
        else:
            direction = self.target_position - self.position
            return direction * (self.velocity/direction.r)

    def get_position(self):
        return self.position
    
    def get_distance(self, other):
        return (self.position - other.position).r
    

    def update_position(self, grid_size = 100): 
        if self.get_distance_to_target() <= self.velocity:
            self.position = self.target_position
            self.set_random_target_position(grid_size)
            self.step = self.calculate_step()
        else:
            self.position = Point2D(
                min(max(0, (self.position + self.step).x), grid_size), 
                min(max(0, (self.position + self.step).y), grid_size)
            )  

    def get_distance_to_target(self):
        return np.sqrt(
            (self.position.x - self.target_position.x)**2 + \
            (self.position.y - self.target_position.y)**2
        )
    
    def set_random_target_position(self, grid_size):
        self.target_position = Point2D(
            min(max(0, self.position.x + np.random.random() * 40 - 20), grid_size),
            min(max(0, self.position.y + np.random.random() * 40 - 20), grid_size)
        )
    
    def get_color(self):
        return self.color


class SusceptibleAgent(Agent):
    def __init__(self, id, position: Point2D, target_position: Point2D, velocity = 5):
        super().__init__(id, position, target_position, velocity)
        self.status = Status.SUSCEPTIBLE
        self.color = "#c9cfd3"

    def infect(self, recovery_probability): 
        return InfectedAgent(
            self.id, 
            self.position, 
            self.target_position, 
            self.velocity,
            recovery_probability
        )


class InfectedAgent(Agent):
    def __init__(
            self, 
            id, 
            position: Point2D, 
            target_position: Point2D, 
            velocity = 5, 
            recovery_probability = 1/20
        ):
        super().__init__(id, position, target_position, velocity)
        self.status = Status.INFECTED
        self.recovery_probability = recovery_probability
        self.color = "#f6dc68"

    def recover(self):
        return RecoveredAgent(
            self.id, 
            self.position, 
            self.target_position, 
            self.velocity
        )

    def try_to_recover(self):
        if np.random.random() < self.recovery_probability:
            return self.recover()
        else:
            return self
        

class RecoveredAgent(Agent):
    def __init__(
            self, 
            id, 
            position: Point2D, 
            target_position = Point2D(0, 0), 
            velocity = 0
        ):
        super().__init__(id, position, target_position, velocity)
        self.status = Status.RECOVERED
        self.color = "#03313d"


class SIRSimulation:
    def __init__(
            self, 
            agents_number = 500, 
            initial_infection_rate = 0.01, 
            infection_radius = 5,
            infection_probability = 0.2, 
            recovery_probability = 0.015, 
            grid_size = 200,
            save_figure = False
        ):
        self.animation = None
        self.AGENTS_NUMBER = agents_number
        self.INITIAL_INFECTION_RATE = initial_infection_rate
        self.INFECTION_RADIUS = infection_radius
        self.INFECTION_PROBABILITY = infection_probability
        self.RECOVERY_PROBABILITY = recovery_probability
        self.GRID_SIZE = grid_size
        self.save_figure = save_figure
        self.agents = []
        self.infected_numbers = [self.INITIAL_INFECTION_RATE * self.AGENTS_NUMBER]
        self.susceptible_numbers = [self.AGENTS_NUMBER - self.infected_numbers[-1]]
        self.recovered_numbers = [0]
        self.list_time = [0]
        self.init_agents()
        self.init_figure()


    def init_agents(self):
        infected_indices = np.random.choice(
            self.AGENTS_NUMBER, 
            int(self.AGENTS_NUMBER * self.INITIAL_INFECTION_RATE), 
            replace = False
            )
        
        self.agents = [
            self.init_agent(i, infected_indices) for i in range(self.AGENTS_NUMBER)
        ]


    def init_agent(self, i, infected_indices):
        if i in infected_indices:
            return InfectedAgent(
                i, 
                Point2D(np.random.random() * self.GRID_SIZE, np.random.random() * self.GRID_SIZE),
                Point2D(np.random.random() * self.GRID_SIZE, np.random.random() * self.GRID_SIZE),
                np.random.random() + 1,
                self.RECOVERY_PROBABILITY
            ) 
        else:
            return SusceptibleAgent(
                i, 
                Point2D(np.random.random() * self.GRID_SIZE, np.random.random() * self.GRID_SIZE),
                Point2D(np.random.random() * self.GRID_SIZE, np.random.random() * self.GRID_SIZE),
                np.random.random() + 1
            ) 


    def init_figure(self):
        self.fig = plt.figure(figsize = (20, 10))
        self.gridspec = self.fig.add_gridspec(ncols = 2, nrows = 1)
        self.init_kpis_plot()
        self.init_population_scatter()


    def init_kpis_plot(self):
        self.kpis_plot = self.fig.add_subplot(self.gridspec[0, 0])
        self.kpis_plot.set_ylim(0, self.AGENTS_NUMBER)
        self.update_kpis_plot(0)
        self.kpis_plot.set_xlabel("Time")
        self.kpis_plot.set_ylabel("Agents")


    def init_population_scatter(self):
        self.population_scatter = self.fig.add_subplot(self.gridspec[0, 1])
        self.population_scatter.axis([-1, self.GRID_SIZE + 1, -1, self.GRID_SIZE + 1])
        self.population_scatter = self.population_scatter.scatter(
            [agent.position.x for agent in self.agents],
            [agent.position.y for agent in self.agents],
            s = 16
        )
        self.population_scatter.set_color([agent.get_color() for agent in self.agents])


    def update(self, frame):
        self.try_to_pause_simulation()
        self.update_agents()
        self.update_agents_numbers()
        self.list_time.append(frame)
        self.update_kpis_plot(frame)
        self.update_population_scatter()

        return self.population_scatter, self.kpis_plot


    def try_to_pause_simulation(self):
        if self.infected_numbers[-1] == 0:
            self.pause_simualtion()


    def pause_simualtion(self):
        self.animation.event_source.stop()


    def update_agents(self):
        for agent in self.agents:
            agent.update_position(self.GRID_SIZE)
            if agent.status == Status.INFECTED:
                for other_agent in self.agents:
                    if other_agent.id != agent.id \
                        and other_agent.status == Status.SUSCEPTIBLE:
                        if agent.get_distance(other_agent) < self.INFECTION_RADIUS:
                            if np.random.random() < self.INFECTION_PROBABILITY:
                                self.agents[other_agent.id] = other_agent.infect(self.RECOVERY_PROBABILITY)
                self.agents[agent.id] = agent.try_to_recover()


    def update_agents_numbers(self):
        agent_numbers = {"S": 0, "I": 0, "R": 0}
        for agent in self.agents:
            if agent.status == Status.SUSCEPTIBLE:
                agent_numbers["S"] += 1
            elif agent.status == Status.INFECTED:
                agent_numbers["I"] += 1
            elif agent.status == Status.RECOVERED:
                agent_numbers["R"] += 1
            else:
                raise ValueError()
        self.susceptible_numbers.append(agent_numbers["S"])
        self.infected_numbers.append(agent_numbers["I"])
        self.recovered_numbers.append(agent_numbers["R"])


    def update_kpis_plot(self, frame):
        self.kpis_plot.set_xlim(left = 0, right = max(1, frame))
        self.kpis_plot.stackplot(
            self.list_time, 
            self.infected_numbers, 
            self.susceptible_numbers, 
            self.recovered_numbers,
            colors = ["#f6dc68", "#c9cfd3", "#03313d"]
        )


    def update_population_scatter(self):
        offsets = np.array(
            [
                [agent.position.x for agent in self.agents], 
                [agent.position.y for agent in self.agents]
            ]
        )
        self.population_scatter.set_offsets(np.ndarray.transpose(offsets))
        self.population_scatter.set_color([agent.get_color() for agent in self.agents])
      

    def run(self):
        self.animation = animation.FuncAnimation(
            self.fig, 
            self.update, 
            interval = 20,
            blit = False,
            repeat = True,
            save_count = 800
        )
        if self.save_figure:
            self.save_fig()
        else:
            plt.show()

    
    def save_fig(self):
        matplotlib.rcParams["animation.ffmpeg_path"] = \
        "C:\\Users\\klaud\Desktop\\ffmpeg-6.0-essentials_build\\ffmpeg-6.0-essentials_build\\bin\\ffmpeg.exe"
        writer = animation.FFMpegWriter(fps = 15)
        figname = "{}_agents_number_{}_prct_infected_{}_infection_radius_{}" \
                  "_infection_prob_{}_recovery_prob_{}.mp4".format(
            datetime.now().strftime("%Y%m%d"), 
            self.AGENTS_NUMBER,
            self.INITIAL_INFECTION_RATE,
            self.INFECTION_RADIUS,
            self.INFECTION_PROBABILITY,
            self.RECOVERY_PROBABILITY
        )
        full_figname = os.path.join(os.path.join(os.getcwd(), 'figs'), figname)
        self.animation.save(full_figname, writer = writer)


if __name__ == "__main__":
    # sim = SIRSimulation(infection_probability = 0.1, recovery_probability = 0.025, save_figure = True)
    # sim.run()
    sim = SIRSimulation(infection_probability = 0.25, recovery_probability = 0.01, save_figure = True)
    sim.run()


