import random
import csv


class NameGenerator():
    def __init__(self):
        self.names = []

    def generate_name(self) -> str:
        with open("Methods/Datasets/prenom.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            family_names = [row[0].strip() for row in reader]
            next(reader, None)
        return random.choice(family_names)


    def generate_planet(self) -> str:
        with open("Methods/Datasets/planets.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)

            next(reader, None)

            planet_names = [row[1].strip() for row in reader]

        planet_name = random.choice(planet_names)
        with open("Methods/Datasets/planet_types.txt", "r") as f:
            planet_types = [line.strip() for line in f if line.strip()]
            type = random.choice(planet_types)

        return f"{planet_name}, {type}."
