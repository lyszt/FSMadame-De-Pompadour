import random
import uuid
from abc import abstractmethod

from .Inventory import Inventory

class Humanoid:
    def __init__(self, name: str, age: int, net_worth: float):
        self.id: uuid = uuid.uuid4()
        self.name: str = name
        self.age: int = age
        self.net_worth: float = net_worth
        self.alive: bool = True
        self.inventory: Inventory = Inventory()
        with open("Methods/Datasets/personality_traits.txt", "r") as f:
            personality_list = [line.strip() for line in f if line.strip()]
        self.personality = []
        while len(self.personality) != 3:
            random_trait = random.choice(personality_list)
            if random_trait not in self.personality:
                self.personality.append(random.choice(personality_list))



def meow(self) -> str:
        return f"{self.name} is meowing."

    @abstractmethod
    def idle_action(self):
        pass
    @abstractmethod
    def against_another_neutral(self):
        pass
    @abstractmethod
    def act(self, actors_around: list, action_history: list):
        pass
