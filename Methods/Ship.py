from typing import List, Dict

from .Humanoid import Humanoid
from .Inventory import Inventory
from .WeaponSystem import WeaponSystem


class Ship:
    def __init__(self, crew: List, name: str, accuracy):
        self.crew: List[Humanoid] = crew
        self.cargo: Inventory = Inventory()
        self.damage_log: List[str] = []
        self.integrity: float = 100.0
        self.systems = {
            "life_support": {"status": "online", "health": 100.0},
            "navigation": {"status": "online", "health": 100.0},
            "propulsion": {"status": "online", "health": 100.0},
            "power_core": {"status": "online", "health": 100.0},
            "sensors": {"status": "online", "health": 100.0},
        }
        self.name = name
        self.weapon_system: WeaponSystem = WeaponSystem(name="Phaser", accuracy=accuracy)
        self.relations = Dict[Ship, float] # From 0 to 100

    def name_weapon_system(self, name):
        self.weapon_system.name_weapon_system(name)

    def set_weapon_system(self, weapon_system: WeaponSystem):
        self.weapon_system = weapon_system

    def apply_damage_to_system(self, system_name: str, amount: float, source: str = "unknown"):
        system = self.systems.get(system_name)
        if not system:
            raise ValueError(f"System '{system_name}' not found.")
        system["health"] = max(system["health"] - amount, 0.0)
        if system["health"] == 0.0:
            system["status"] = "offline"
        elif system["health"] < 100.0:
            system["status"] = "damaged"
        self.damage_log.append(f"{system_name} was damaged by {source} and lost {amount} integrity")

    def repair_system(self, system_name: str, amount: float):
        system = self.systems.get(system_name)
        if not system:
            raise ValueError(f"System '{system_name}' not found.")
        system["health"] = min(system["health"] + amount, 100.0)
        system["status"] = "online" if system["health"] == 100.0 else "damaged"

    def status_report(self):
        return {
            "integrity": self.integrity,
            "systems": {
                k: {"status": v["status"], "health": v["health"]}
                for k, v in self.systems.items()
            },
            "cargo_count": self.cargo.get_occupied_slots(),
        }

    def get_systems(self):
        return self.systems

