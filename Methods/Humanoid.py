import os
import random
import re
import traceback
import csv
import uuid
from abc import ABC, abstractmethod
from typing import Callable, Optional, List
from google import genai
from pydantic import BaseModel, Field

from .Inventory import Inventory
from .NameGenerator import NameGenerator


def command(func: Callable) -> Callable:
    """Decorator to register a method as an AI-callable command."""
    func.is_command = True
    return func

class FearsAndWantsSchema(BaseModel):
    wants: List[str] = Field(..., description="A list of the character's core desires.")
    fears: List[str] = Field(..., description="A list of the character's core fears.")

class Humanoid(ABC):
    def __init__(self, name: str, age: int, net_worth: float, actor_manager: 'ActorManager', mini_llm):
        self.id = uuid.uuid4()
        self.name: str = name
        self.age: int = age
        self.net_worth: float = net_worth
        self.alive: bool = True
        self.health: float = 100.0
        self.inventory: Inventory = Inventory()
        self.tasks = []
        self.actor_manager = actor_manager
        # mini_llm is just a reference, not a GPT4All instance
        self.model = mini_llm

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

        print(f"Using small model to generate {self.name}'s personality", flush=True)
        self.set_backstory()
        print(self.backstory, flush=True)
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
        role_name = self.__class__.__name__
        wealth = random.choice(["starving", "poor","rich", "economical elite", "nobility"])

        full_planet_description = NameGenerator().generate_planet()
        planet_parts = full_planet_description.split(',')
        planet_of_origin = planet_parts[0] if planet_parts else "an unknown world"


        with open("Methods/Datasets/patronymes.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            family_names = [row[0].strip() for row in reader]
            next(reader, None)
        family_name = random.choice(family_names).lower().capitalize()

        context = f"""
        You are a creative writer developing a character for a sci-fi simulation.
        Your task is to write a compelling, first-person backstory (2-3 sentences) by weaving the following key elements into a creative narrative.
        Do NOT just list the elements back. Invent something from this.
    
        ## Key Elements ##
        - Name: {self.name}
        - Role: A {role_name}
        - Origin: From {planet_of_origin}
        - Family: The {family_name} family, who are {wealth}
        - Personality: {self.personality}   
    
        ## Instructions ##
        - The backstory must be in the first-person ("I...").
        - It must explain why a person with this background and personality joined the crew of the starship FS Madame de Pompadour.
        - Do NOT include any text other than the backstory itself.
    
        Write the backstory now.
        """
        raw = self.actor_manager.submit_prompt(context).strip()
        self.backstory = raw.strip()

    def define_fears_and_wants(self, actions: Optional[list] = None):
        """
        Uses the Gemini API to generate a character's core wants and fears
        based on their profile, expecting a structured JSON response.
        """
        actions = actions or []

        prompt = f"""
        You are a character psychologist. Based on the following character profile,
        determine their core wants and fears.
    
        ## Character Profile
        - Name: {self.name}
        - Personality: {self.personality}
        - Backstory: {self.backstory}
        - Recent Actions: {actions[-3:]}
    
        ## Your Task
        Generate a JSON object containing two keys: "wants" and "fears".
        - For each key, provide a list of 2 to 3 short, descriptive phrases.
        - The wants and fears should be a direct consequence of the character's personality and backstory.
    
        CRUCIAL: Your response must ONLY be the raw JSON object. Do not include any other text, explanations, or markdown formatting.
        """
        client = genai.Client()
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": FearsAndWantsSchema,
                }
            )
            print(f"Fears/Wants decision from AI: {response.text}")
            schema = FearsAndWantsSchema.model_validate_json(response.text)

            # Use the validated data
            self.wants.extend(schema.wants)
            self.fears.extend(schema.fears)

        except Exception as e:
            print(f"Error parsing fears and wants for {self.name}: {e}")
            # Fallback in case of error
            self.wants.append("Survive the day")
            self.fears.append("The unknown")

        # --- The rest of your function remains the same ---
        # Minimal dedupe & limit
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
        self.global_information = [self.wants, self.fears, self.backstory, self.tasks]
        self.global_prompt = self._compose_global_prompt()

    @command
    def remove_task(self, task: str):
        if task in self.tasks:
            self.tasks.remove(task)
            self.captain_task = f"You have decided to ignore: {task}"
            self.global_information = [self.wants, self.fears, self.backstory, self.tasks]
            self.global_prompt = self._compose_global_prompt()

    @command
    def add_new_fear(self, fear):
        if fear and isinstance(fear, str):
            s = fear.strip()
            if s and s not in self.fears:
                self.fears.append(s)

    @command
    def add_new_wish(self, want):
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
        if want in self.wants:
            self.wants.remove(want)

    @command
    def punch(self, target_name: str) -> str:
        if not target_name:
            return f"{self.name} swings at the air, looking foolish."
        target = next((actor for actor in self.actor_manager.actors.values() if target_name.lower() in actor.name.lower()), None)
        if not target:
            return f"{self.name} looks around for '{target_name}' but can't find them."
        if not target.alive:
            return f"{self.name} looks at {target.name}'s body but does nothing."
        target.lose_hp(random.uniform(1, 10))
        if not target.alive:
            return f"{self.name} finishes {target_name} with a deadly punch, which sends him ragdolling, now unalive."
        places_to_punch = ["jaw", "nose", "stomach", "ribs", "shoulder"]
        return f"{self.name} punches {target.name} right in the {random.choice(places_to_punch)}."

    @command
    def shoot(self, target_name: str) -> str:
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
        item = arg
        if not item:
            return f"{self.name} considers acquiring something, but decides against it."
        self.inventory.add(item)
        return f"{self.name} acquires a '{item}'."

    @command
    def get_inventory(self, arg: Optional[str] = None) -> str:
        items = self.inventory.inventory
        if not items:
            return f"{self.name} checks their pockets and finds them empty."
        return f"{self.name} takes stock of their belongings: {', '.join(items)}."

    @command
    def use_item(self, arg: str) -> str:
        item = arg
        if not item:
            return f"{self.name} considers using a tool but doesn't pick one."
        if item not in self.inventory.inventory:
            return f"{self.name} can't use '{item}'—it's not in their inventory."
        return f"{self.name} uses the '{item}'."

    @command
    def task_is_completed(self, arg: str) -> str:
        task = arg
        if not self.tasks:
            return f"{self.name} has no orders to execute."
        if task not in self.tasks:
            return f"{self.name} reports on a task, but '{task}' was not in their orders."
        self.remove_task(task)
        return f"{self.name} reports they have finished the task: '{task}'."
