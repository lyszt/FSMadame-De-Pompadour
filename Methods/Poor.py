import random

from .Humanoid import Humanoid
from .Inventory import Inventory

class Poor(Humanoid):
    def __init__(self, name, net_worth, age):
        super().__init__(name, age, net_worth)


    def eat_possessions(self) -> None:
        self.inventory.empty()
        print(f"{self.name} comeu suas possessões! Que delicia!")

    def receive_alms(self, item):
        print(f"{self.name} recebeu um {item} como esmola. 'Muito obrigado!' - Disse {self.name}")
        self.inventory.add(item)

    def remove_possession(self, item):
        self.inventory.remove(item)

    def get_inventory(self) -> Inventory:
        return self.inventory

    def idle_action(self):
        with open("Methods/Datasets/poor_actions.txt", "r") as f:
            name_list = [line.strip() for line in f if line.strip()]
        return random.choice(name_list)

    def against_another_neutral(self):
        with open("Methods/Datasets/poor_target_actions_neutral.txt", "r") as f:
            name_list = [line.strip() for line in f if line.strip()]
        return random.choice(name_list)

    def act(self, actors_around: list):
        options = ["to_oneself", "against_another"]
        choice = random.choice(options)
        match choice:
            case "to_oneself":
                return f"{self.name} {self.idle_action()}."
            case "against_another":
                return f"{self.name} {self.against_another_neutral()} {random.choice(actors_around)}."