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
