import os
import random
import re
import traceback
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional
from gpt4all import gpt4all, GPT4All

from .Inventory import Inventory

def command(func: Callable) -> Callable:
    """Decorator to register a method as an AI-callable command."""
    func.is_command = True
    return func


class Humanoid(ABC):
    def __init__(self, name: str, age: int, net_worth: float, actor_manager: 'ActorManager'):
        self.id = uuid.uuid4()
        self.name: str = name
        self.age: int = age
        self.net_worth: float = net_worth
        self.alive: bool = True
        self.health: float = 100.0
        self.inventory: Inventory = Inventory()
        self.tasks = []
        self.actor_manager = actor_manager
        # micro llm
        # API doesn't work, btw
        try:
            home_directory = Path.home()
            model_folder = home_directory / 'llm_models'
            self.model = GPT4All(
                model_name='mistral-7b-instruct-v0.1.Q3_K_M.gguf',
                model_path=str(model_folder)
            )
        except Exception:
            traceback.print_exc()
            print("Download mistral-7b-instruct-v0.1.Q3_K_M.gguf to your 'home/llm_models' folder in your home directory for this to run.")

        self.wants = []
        self.fears = []
        self.backstory = ""

        with open("Methods/Datasets/personality_traits.txt", "r") as f:
            personality_list = [line.strip() for line in f if line.strip()]
            self.personality = random.sample(personality_list, k=3)

        # memory depth adjustments
        self.memory_depth: int = 15
        if "Forgettable" in self.personality or "addict" in self.personality:
            self.memory_depth -= 5

        print(f"Using small model to generate {self.name}'s personality")
        self.set_backstory()
        self.define_fears_and_wants()
        self.captain_task = f"Your superiors have given you a task: {self.tasks}" if len(self.tasks) > 0 else ""
        self.global_information = [
            self.wants,
            self.fears,
            self.backstory,
            self.tasks
        ]
        self.global_prompt = self._compose_global_prompt()

    def _compose_global_prompt(self) -> str:
        wants_s = ", ".join(self.wants) if self.wants else "none"
        fears_s = ", ".join(self.fears) if self.fears else "none"
        tasks_s = ", ".join(self.tasks) if self.tasks else "none"
        return f"Wants: {wants_s}\nFears: {fears_s}\nBackstory: {self.backstory}\nTasks: {tasks_s}"

    @abstractmethod
    def act(self, actors_around: list, action_history: list):
        pass


    def set_backstory(self):
        context = f"""
             You are a character in a text-based simulation aboard the French military starship, FS Madame de Pompadour.
             You are surrounded by many in your crew. They are: {self.actor_manager.actors}
             Your name is {self.name}, and you are known for being: {self.personality}
             Make a small, brief backstory telling how you got here and why you joined the crew.
        """
        with self.model.chat_session():
            self.backstory = self.model.generate(context) or ""

    def define_fears_and_wants(self, actions: Optional[list] = None):
        """
        Single-generation approach: one call that returns labeled lines:
        Trait: <trait> | Want: <short phrase> | Fear: <short phrase>

        Only non-empty Want/Fear phrases are added to the lists.
        """
        actions = actions or []
        trait_list = ", ".join(self.personality)

        prompt = (
            f"You are a character on the FS Madame de Pompadour.\n"
            f"Name: {self.name}\n"
            f"Personality traits: {self.personality}\n"
            f"Backstory: {self.backstory}\n"
            f"Recent actions: {actions}\n\n"
            f"{trait_list}: For each trait, output exactly ONE line using this format:\n"
            "Trait: <trait> | Want: <short phrase> | Fear: <short phrase>\n\n"
            "If you don't have a want or fear for a trait, leave that field empty.\n"
            "Do NOT add extra commentary."
        )

        with self.model.chat_session():
            raw = (self.model.generate(prompt) or "").strip()

        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        pattern = re.compile(r"Trait:\s*(?P<trait>[^|]+)\|\s*Want:\s*(?P<want>[^|]*)\|\s*Fear:\s*(?P<fear>.*)")

        for ln in lines:
            m = pattern.match(ln)
            if not m:
                continue
            want = m.group("want").strip()
            fear = m.group("fear").strip()

            if want:
                self.add_new_wish(want)
            if fear:
                self.add_new_fear(fear)

        # minimal dedupe & limit
        self.wants = list(dict.fromkeys(self.wants))[:6]
        self.fears = list(dict.fromkeys(self.fears))[:6]

        
        self.global_information = [
            self.wants,
            self.fears,
            self.backstory,
            self.tasks
        ]
        self.global_prompt = self._compose_global_prompt()



    def lose_hp(self, amount: float):
        self.health -= amount
        if self.health <= 0:
            self.alive = False

    def add_task(self, task: str):
        self.tasks.append(task)
        self.captain_task = f"Your superiors have given you tasks: {self.tasks}" if len(self.tasks) > 0 else ""
        
        self.global_information = [
            self.wants,
            self.fears,
            self.backstory,
            self.tasks
        ]
        self.global_prompt = self._compose_global_prompt()

    @command
    def remove_task(self, task: str):
        if task in self.tasks:
            self.tasks.remove(task)
            self.captain_task = f"You have decided to ignore: {task}"
            
            self.global_information = [
                self.wants,
                self.fears,
                self.backstory,
                self.tasks
            ]
            self.global_prompt = self._compose_global_prompt()

    @command
    def add_new_fear(self, fear):
        if fear and isinstance(fear, str):
            s = fear.strip()
            if s and s not in self.fears:
                self.fears.append(s)

    @command
    def add_new_wish(self, want):
        # fixed: append to wants not fears
        if want and isinstance(want, str):
            s = want.strip()
            if s and s not in self.wants:
                self.wants.append(s)

    @command
    def remove_fear(self, fear):
        if fear in self.fears:
            self.fears.remove(fear)

    @command
    def remove_want(self, want):
        # fixed: remove from wants (no recursion)
        if want in self.wants:
            self.wants.remove(want)

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
    def acquire_item(self, arg: str) -> str:
        """Acquires a new item for personal inventory."""
        item = arg
        if not item:
            return f"{self.name} considers acquiring something, but decides against it."
        self.inventory.add(item)
        return f"{self.name} acquires a '{item}'."

    @command
    def get_inventory(self, arg: Optional[str] = None) -> str:
        """Checks their own inventory."""
        items = self.inventory.inventory
        if not items:
            return f"{self.name} checks their pockets and finds them empty."
        return f"{self.name} takes stock of their belongings: {', '.join(items)}."

    @command
    def use_item(self, arg: str) -> str:
        """Uses an item from inventory in a contextual, narrative way."""
        item = arg
        if not item:
            return f"{self.name} considers using a tool but doesn't pick one."
        if item not in self.inventory.inventory:
            return f"{self.name} can't use '{item}'—it's not in their inventory."
        return f"{self.name} uses the '{item}'."

    @command
    def task_is_completed(self, arg: str) -> str:
        """Reports that one of their assigned tasks is now completed. The argument must be the exact task string."""
        task = arg
        if not self.tasks:
            return f"{self.name} has no orders to execute."
        if task not in self.tasks:
            return f"{self.name} reports on a task, but '{task}' was not in their orders."
        self.remove_task(task)
        return f"{self.name} reports they have finished the task: '{task}'."
