from typing import Any, Dict
from uuid import UUID

from flask import jsonify
from googletrans import Translator

from .Captain import Captain
from .Environment import Environment
from .Humanoid import Humanoid
from .Lieutenant import Lieutenant
from .NameGenerator import NameGenerator
from .Crewman import Crewman
from .Doctor import Doctor
import random

from .Ship import Ship


class ActorManager:
    def __init__(self):
        self.actors: Dict[UUID, Humanoid] = {}
        self.ship = Ship(crew=list(self.actors.values()),name="La Madame de Pompadour", accuracy=.5)
        self.environment: Environment = Environment(main_ship=self.ship, ships_sector=None)
        self.captain = Captain(name=f'{NameGenerator().generate_name()}', age=random.randint(0,110), net_worth=random.uniform(0, 1e9), ship_command=self.ship, environment=self.environment)


    def add(self, actor: Humanoid):
        self.actors[actor.id] = actor

    def populate(self, population: int):
        for i in range(population):
            NPC: Crewman = Crewman(name=f'{NameGenerator().generate_name()}', age=random.randint(0,110), net_worth=random.uniform(0, 1e9), ship=self.ship, environment=self.environment)
            self.actors[NPC.id] = (NPC)
        self.actors[self.captain.id] = self.captain
        # Essential archetypes
        doc: Doctor = Doctor(name=NameGenerator().generate_name(), age=random.randint(0,110), net_worth=random.uniform(0, 1e9), environment=self.environment)
        self.actors[doc.id] = doc
        lieutenant: Lieutenant = Lieutenant(name=NameGenerator().generate_name(), age=random.randint(0,110), net_worth=random.uniform(0, 1e9), environment=self.environment, ship_command=self.ship)
        self.actors[lieutenant.id] = lieutenant

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

        if len(action_history) > 2 and "Captain" in action_history[-1] and all("ENVIRONMENT" not in action for action in action_history[-5:]):
            return self.environment.act(action_history)
        if not self.actors:
            raise Exception("You must populate the actor manager before making an action.")
        if len(action_history) == 0:
            return self.environment.introduce()
        if len(action_history) == 1:
            return self.captain.set_initial_mission(list(self.actors.values()), action_history)
        else:
            if all(self.captain.name not in action for action in action_history[-5:]):
                return self.captain.act(list(self.actors.values()), action_history)
        action = random.choice(list(self.actors.values())).act(list(self.actors.values()), action_history)

        self.actors = {key: actor for key, actor in self.actors.items() if actor.alive}

        return action
