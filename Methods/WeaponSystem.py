import random

from .Ship import Ship


class WeaponSystem:
    def __init__(self, name, ship, accuracy):
        self.name = name
        self.ship: Ship = ship
        self.accuracy: float = accuracy


    def shoot(self, ship: Ship) -> bool:
        if not ship:
            raise ValueError(f"Ship '{ship}' not found.")
        if random.random() < self.accuracy:
            ship.apply_damage_to_system(system_name=random.choice(list(ship.get_systems())), source=self.ship.name, amount = random.uniform(0,100))
            return True
        else:
            return False

    def name_weapon_system(self,name):
        self.name = name