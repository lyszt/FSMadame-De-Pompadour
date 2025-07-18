from typing import Any, Dict
from uuid import UUID

from flask import jsonify

from .Captain import Captain
from .Humanoid import Humanoid
from .NameGenerator import NameGenerator
from .Crewman import Crewman
import random

class ActorManager:
    def __init__(self):
        self.captain: Humanoid
        self.actors: Dict[UUID, Humanoid] = {}


    def add(self, actor: Humanoid):
        self.actors[actor.id] = actor

    def populate(self, population: int):
        self.captain = Captain(name=f'{NameGenerator().generate_name()}', age=random.randint(0,110), net_worth=random.uniform(0, 1e9))
        for i in range(population):
            NPC: Crewman = Crewman(name=f'{NameGenerator().generate_name()}', age=random.randint(0,110), net_worth=random.uniform(0, 1e9))
            self.actors[NPC.id] = (NPC)
        self.actors[self.captain.id] = self.captain

    def get_actor_by_id(self, id: UUID):
        return self.actors[id]

    def get_actor_list(self):
        serialized = {str(uuid): actor.name for uuid, actor in self.actors.items()}
        return jsonify({
            "body": serialized,
            "status": 200
        })

    def get_random_actor(self) -> Humanoid:
        if not self.actors:
            raise Exception("You must populate the actor manager before getting an actor.")
        return random.choice(list(self.actors.values()))

    def act_randomnly(self, action_history) -> Any:
        if not self.actors:
            raise Exception("You must populate the actor manager before making an action.")
        if len(action_history) == 0 or self.captain.name not in action_history[-5:]:
            return self.captain.act(list(self.actors.values()), action_history)
        action = random.choice(list(self.actors.values())).act(list(self.actors.values()), action_history)
        return action
