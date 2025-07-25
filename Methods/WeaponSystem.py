import random


class WeaponSystem:
    def __init__(self, name, accuracy):
        self.name = name
        self.accuracy: float = accuracy


    def shoot(self, ship, source) -> bool:
        if not ship:
            raise ValueError(f"Ship '{ship}' not found.")
        if random.uniform(0,1) < self.accuracy:
            ship.apply_damage_to_system(system_name=random.choice(list(ship.get_systems())), source=source.name, amount = random.uniform(0,100))
            return True
        else:
            return False

    def name_weapon_system(self,name):
        self.name = name