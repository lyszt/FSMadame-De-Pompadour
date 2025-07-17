import random


class NameGenerator():
    def __init__(self):
        self.names = []

    def generate_name(self) -> str:
        with open("Methods/Datasets/male_names.txt", "r") as f:
            name_list = [line.strip() for line in f if line.strip()]
        return random.choice(name_list)