import random
import uuid
from abc import abstractmethod
from typing import Callable

from .Inventory import Inventory

def command(func: Callable) -> Callable:
    """Decorator to register a method as an AI-callable command."""
    func.is_command = True
    return func


class Humanoid:
    def __init__(self, name: str, age: int, net_worth: float, actor_manager):
        self.id: uuid = uuid.uuid4()
        self.name: str = name
        self.age: int = age
        self.net_worth: float = net_worth
        self.alive: bool = True
        self.health: float = 100.0
        self.inventory: Inventory = Inventory()
        self.tasks = []
        self.actor_manager = actor_manager
        self.captain_task = f"Your superiors have given you a task: {self.tasks}" if len(self.tasks) > 0 else ""
        self.global_prompt = """
        
        """
        with open("Methods/Datasets/personality_traits.txt", "r") as f:
            personality_list = [line.strip() for line in f if line.strip()]
        self.personality = []
        while len(self.personality) != 3:
            random_trait = random.choice(personality_list)
            if random_trait not in self.personality:
                self.personality.append(random_trait)
        self.memory_depth: int = 15
        if "Forgettable" in self.personality or "addict" in self.personality:
            self.memory_depth -= 5



    def meow(self) -> str:
            return f"{self.name} is meowing."

    @abstractmethod
    def idle_action(self):
        pass
    @abstractmethod
    def against_another_neutral(self):
        pass
    @abstractmethod
    def act(self, actors_around: list, action_history: list):
        pass

    def lose_hp(self, amount: float):
        self.health -= amount
        if self.health <= 0:
            self.alive = False

    def add_task(self, task):
        self.tasks.append(task)
        self.captain_task = f"Your superiors have given you tasks: {self.tasks}" if len(self.tasks) > 0 else ""
        self.global_prompt = f"""
            {self.captain_task}
        """

    def remove_task(self, choice):
       if choice in self.tasks:
           self.tasks.remove(choice)
       self.captain_task = f"Your superiors have given you tasks: {self.tasks}" if len(self.tasks) > 0 else ""
       self.global_prompt = f"""
            {self.captain_task}
        """

    @command
    def punch(self, target_name: str) -> str:
        """Starts a physical altercation with another character by name."""
        if not target_name:
            return f"{self.name} swings at the air, looking foolish."

        target = next((actor for actor in self.actor_manager.actors.values() if target_name.lower() in actor.name.lower()), None)

        if not target:
            return f"{self.name} looks around for '{target_name}' but can't find them."
        if not target.alive:
            return f"{self.name} looks at {target.name}'s body but does nothing."

        target.lose_hp(random.uniform(1, 10))
        places_to_punch = ["jaw", "nose", "stomach", "ribs", "shoulder"]
        return f"{self.name} punches {target.name} right in the {random.choice(places_to_punch)}."

    @command
    def shoot(self, target_name: str) -> str:
        """Uses a personal weapon against another character by name."""
        if not target_name:
            return f"{self.name} nervously draws a weapon but has no one to aim at."

        target = next((actor for actor in self.actor_manager.actors.values() if target_name.lower() in actor.name.lower()), None)

        if not target:
            return f"{self.name} aims their weapon, but can't find '{target_name}'."
        if not target.alive:
            return f"{self.name} aims their weapon at {target.name}'s body but doesn't fire."

        damage = random.uniform(15, 50)
        target.lose_hp(damage)

        if not target.alive:
            return f"{self.name} pulls out a concealed weapon and kills {target.name} in a shocking act of violence."
        else:
            return f"{self.name} shoots and wounds {target.name}."


    @command
    def acquire_item(self, item: str) -> str:
        """Acquires a new item for their medical kit."""
        if not item:
            return f"{self.name} considers acquiring something, but decides against it."
        self.inventory.add(item)
        return f"{self.name} acquires a '{item}' and carefully places it in their medical kit."

    @command
    def get_inventory(self) -> str:
        """Checks their own medical kit."""
        items = self.inventory.inventory
        if len(items) < 1:
            return f"{self.name} checks their medical bag and finds it empty."
        return f"{self.name} takes stock of their medical supplies: {', '.join(items)}."



    @command
    def use_item(self, item: str) -> str:
        """Uses an item from inventory in a contextual, narrative way."""
        if not item:
            return f"{self.name} considers using a tool but doesn't pick one."
        if item not in self.inventory.inventory:
            return f"{self.name} can't use '{item}'—it's not in the kit."
        return f"{self.name} uses the '{item}' as needed for the situation."


    def accept_order(self, order: str) -> str:
        """Accepts an order from a superior and stores it for execution."""
        if not order:
            return f"{self.name} acknowledges but receives no specific order."
        self.add_task(order)
        return f"{self.name} acknowledges the order: '{order}'."

    @command
    def task_is_completed(self, arg: str) -> str:
        """Reports that one of their assigned tasks is now completed. The argument must be the exact task string."""
        task = arg
        if not self.tasks:
            return f"{self.name} has no orders to execute."
        if task not in self.tasks:
            return f"{self.name} reports on a task, but '{task}' was not in their orders."
        self.remove_task(task)
        return f"{self.name} reports they have finished the task: '{task}."
