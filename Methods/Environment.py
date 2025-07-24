from typing import List

from .Ship import Ship


class Environment:

    def __init__(self, main_ship: Ship, ships_sector=None):
        if ships_sector is None:
            ships_sector = []
        self.main_ship: Ship = main_ship
        self.mood = "Regular"
        self.planet = None
        self.ships_sector: List[Ship] = ships_sector
        pass


    def set_mood(self, mood: str):
        self.mood = mood