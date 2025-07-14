from .Inventory import Inventory

class Humanoid:
    def __init__(self, name: str, age: int, net_worth: float):
        self.name: str = name
        self.age: int = age
        self.net_worth: float = net_worth
        self.alive: bool = True
        self.inventory: Inventory = Inventory()


    def act(self) -> str:
        return f"{self.name} is meowing."

