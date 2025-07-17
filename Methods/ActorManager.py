from typing import Any

from .Humanoid import Humanoid
from .NameGenerator import NameGenerator
from .Crewman import Crewman
import random

class ActorManager:
    def __init__(self):
        self.actors = []


    def add(self, actor: Humanoid):
        self.actors.append(actor)

    def populate(self, population: int):
        for i in range(population):
            NPC: Crewman = Crewman(name=f'{NameGenerator().generate_name()}', age=random.randint(0,110), net_worth=random.uniform(0, 1e9))
            self.actors.append(NPC)

    def get_random_actor(self) -> Humanoid:
        if not self.actors:
            raise Exception("You must populate the actor manager before getting an actor.")
        return random.choice(self.actors)

    def act_randomnly(self, action_history) -> Any:
        if not self.actors:
            raise Exception("You must populate the actor manager before making an action.")
        action = random.choice(self.actors).act(self.actors, action_history)
        return action
