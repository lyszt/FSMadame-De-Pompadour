import random
from typing import List, Optional

from .Ship import Ship


class Environment:

    def __init__(self, main_ship: Ship, ships_sector=None):
        if ships_sector is None:
            ships_sector = []
        self.main_ship: Ship = main_ship
        self.mood = "Regular"
        self.planet = None
        self.anomalies: List[str] = []
        self.ships_sector: List[Ship] = ships_sector
        pass


    def set_mood(self, mood: str):
        self.mood = mood

    def discover_anomaly(self) -> Optional[str]:
        if not self.anomalies:
            return None
        return random.choice(self.anomalies)

    def get_visible_ships(self) -> List[Ship]:
        return [s for s in self.ships_sector if s != self.main_ship]

    def introduce(self):
        return ("Space: the final frontier. These are the voyages of the starship La Madame de Pompadour. Her ongoing mission: to "
                "explore strange new worlds, to seek out new life-forms and new civilizations; to boldly go where no "
                "one has gone before.")