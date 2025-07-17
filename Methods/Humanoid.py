import random
from abc import abstractmethod

from .Inventory import Inventory

class Humanoid:
    def __init__(self, name: str, age: int, net_worth: float):
        self.name: str = name
        self.age: int = age
        self.net_worth: float = net_worth
        self.alive: bool = True
        self.inventory: Inventory = Inventory()


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
