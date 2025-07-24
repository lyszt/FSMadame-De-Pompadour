import collections
from typing import Optional, List, Any


class Inventory:
    def __init__(self, inventory_size: Optional[int] = 0):
        self.inventory: List[Optional[Any]] = [None for _ in range(inventory_size)]

    def __str__(self):
        return str(list(self.inventory)).replace("[", " ").replace("]", " ")

    def __getitem__(self, index):
        return self.inventory[index]

    def add(self, *args):
        for arg in args:
            self.inventory.append(arg)

    def empty(self):
        self.inventory = []

    def remove(self, item):
        self.inventory.remove(item)

    def __setitem__(self, index, value):
        if index >= len(self.inventory):
            raise IndexError
        self.inventory[index] = value

    def get_available_slots(self):
        return sum(1 for item in self.inventory if item is not None)

    def get_occupied_slots(self) -> int:
        return sum(1 for item in self.inventory if item is not None)

    def is_full(self) -> bool:
        return self.get_available_slots() == 0