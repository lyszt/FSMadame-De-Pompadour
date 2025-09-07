import random
import inspect
import json
from typing import Optional, Callable, List

# Ensure you have the necessary libraries installed:
# pip install google-generativeai pydantic
from google import genai
from pydantic import BaseModel, Field

# Assuming these are your local project files
from .Humanoid import Humanoid
from .Inventory import Inventory
from .Ship import Ship

# Pydantic model to define the structure for the AI's JSON output.
class Command(BaseModel):
    command: Optional[str] = Field(None, description="The specific command to be executed from the available list.")
    arg: Optional[str] = Field(None, description="The argument required by the command, such as an item or target name.")
    dialogue: Optional[str] = Field(None, description="A single, impactful line of dialogue for the character to say while performing the action.")

# A simple decorator to mark methods as being available to the AI.
def command(func: Callable) -> Callable:
    """Decorator to register a method as an AI-callable command."""
    func.is_command = True
    return func

class Doctor(Humanoid):
    """
    Represents the ship's medical officer, responsible for the health and well-being of the crew.
    The Doctor uses an AI layer to interpret high-level intentions into specific medical actions.
    """
    def __init__(self, name: str, net_worth: float, age: int, environment: 'Environment', actor_manager, mini_llm):
        """
        Initializes the Doctor instance.
        """
        super().__init__(f"Doctor {name}", age, net_worth, actor_manager, mini_llm)
        self.environment = environment

        # --- AI System Initialization ---
        self.client = genai.Client()
        self.commands = {}
        self.command_descriptions = {}
        self._discover_commands()

    def _discover_commands(self):
        """Automatically finds all methods decorated with @command."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, 'is_command'):
                self.commands[name] = method
                self.command_descriptions[name] = inspect.getdoc(method) or "No description available."
        print(f"Doctor commands initialized for {self.name}: {list(self.commands.keys())}")

    # --- Medical Commands ---
    @command
    def treat_patient(self, target: Humanoid) -> str:
        """Heals a wounded crew member, restoring their health."""
        if not target:
            return f"{self.name} looks for a patient but finds no one in need."
        if not target.alive:
            return f"{self.name} checks {target.name}'s vitals and confirms they are gone."
        if target.health >= 100:
            return f"{self.name} scans {target.name} and finds they are in perfect health."

        healing_amount = random.uniform(20, 40)
        target.health = min(100, int(target.health + healing_amount))
        return f"{self.name} applies a medical hypospray to {target.name}, who looks visibly relieved."

    @command
    def run_diagnostics(self, target: Humanoid) -> str:
        """Performs a full diagnostic scan on a crew member to assess their health."""
        if not target:
            return f"{self.name} readies their medical scanner but has no one to scan."
        if not target.alive:
            return f"The diagnostic scan of {target.name} shows no signs of life."

        health_status = "perfect health"
        if target.health < 30:
            health_status = "critical condition"
        elif target.health < 70:
            health_status = "moderate injuries"
        elif target.health < 100:
            health_status = "minor scrapes and bruises"

        return f"A medical tricorder buzzes softly as it scans {target.name}. The readout indicates they are in {health_status}."



    def idle_action(self) -> str:
        """Pulls a random, medical-themed action from a file."""
        try:
            with open("Methods/Datasets/doctor_actions.txt", "r", encoding="utf-8") as f:
                action_list = [line.strip() for line in f if line.strip()]
            return random.choice(action_list)
        except FileNotFoundError:
            return "reviews a medical chart on a datapad."

    def against_another_neutral(self) -> str:
        """Pulls a random neutral action targeting another character."""
        try:
            with open("Methods/Datasets/doctor_target_actions_neutral.txt", "r", encoding="utf-8") as f:
                action_list = [line.strip() for line in f if line.strip()]
            return random.choice(action_list)
        except FileNotFoundError:
            return "gives a reassuring nod to"

    def get_doctor_command(self, action_sentence: str) -> dict:
        """Analyzes a descriptive action sentence to determine which specific command to execute."""
        print(f"Deciding command for {self.name}: '{action_sentence}'")
        command_list_str = "\n".join(
            f'- "{name}": "{desc}"' for name, desc in self.command_descriptions.items()
        )

        prompt = f"""
        You are a command interpreter for a starship's doctor in a simulation. Based on the doctor's intended action, choose the most appropriate command, extract its argument, and create a line of dialogue.

        Available Commands:
        {command_list_str}
        "None": Use this if the action does not map to any command.

        Instructions:
        1. Analyze the doctor's intended action below.
        2. If it maps to one of the available commands, identify that command.
        3. If the command requires an argument (like an item or another crewman's name), extract it for the "arg" field.
        4. Generate a single, in-character line of dialogue for the doctor that fits the action. Place it in the "dialogue" field.
        5. If the action is conversational or doesn't match any command, return "None" for the command.

        Intended Action: "{action_sentence}"

        Respond with only the JSON object.
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": Command,
                }
            )
            print(f"Command decision from AI for {self.name}: {response.text}")
            command_obj = Command.model_validate_json(response.text)
            return command_obj.model_dump()
        except Exception as e:
            print(f"Error decoding command from LLM for {self.name}: {e}")
            return {"command": "None", "arg": None, "dialogue": None}

    def act_with_artificial_intelligence(self, actors_around: list, action_history: list, actions: list) -> str:
        """Uses a generative AI to determine the next action based on personality and recent events."""
        my_recent_actions, other_recent_actions = actions[0], actions[1]
        my_actions_str = "\n".join(f"- {action}" for action in my_recent_actions) if my_recent_actions else "None"
        other_actions_str = "\n".join(f"- {action}" for action in other_recent_actions) if other_recent_actions else "None"
        entities_nearby = ', '.join(actor.name for actor in actors_around if actor.name != self.name) if actors_around else 'no one else'

        wounded_crew = [f"{p.name} (Health: {p.health:.0f}%)" for p in actors_around if p.health < 100 and p.alive]
        wounded_str = ", ".join(wounded_crew) if wounded_crew else "No one appears to be injured."

        prompt = f"""
        You are a character in a text-based simulation aboard the French military starship, FS Madame de Pompadour.
        Your name is {self.name}.
        The ship's mission: {self.environment.mission}
        ## Your Role and Context
        You are the ship's Doctor. Your primary goal is to ensure the crew's well-being, diagnose illnesses, and treat injuries. You are a figure of calm and expertise in crises.
        To your benefit, or not, your personality traits are: {self.personality}. Act upon those traits.

        ## Current Situation
        - Crew members nearby: {entities_nearby}
        - Medical status of nearby crew: {wounded_str}
        - Your recent actions (what you did):
        {my_actions_str}
        - Other recent events (what happened around you):
        {other_actions_str}
        - The current ship-wide situation: {self.environment.situation}
        
        ## Your Task
        Based on the events and your role, what is your next action? Prioritize injured crew.
        Your action must be a single, complete sentence in the third person.
        It should be interactive, involving another crewmember if possible.
        Avoid passive or silent actions. Add dialogue using quotations.
        {self.global_prompt}
        Write the complete sentence for {self.name}'s next action now.
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-lite", contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"AI action failed for {self.name}: {e}. Falling back to default idle action.")
            return f"{self.name} {self.idle_action()}."

    def act(self, actors_around: list, action_history: list) -> str | None:
        """Decides the next action, choosing between a simple action or a more complex, AI-driven action."""
        my_recent_actions = [action for action in action_history[-self.memory_depth:] if action.startswith(self.name)]
        others_recent_actions = [action for action in action_history[-5:] if not action.startswith(self.name)]

        print(f"\n--- Doctor AI Action Cycle for {self.name} ---")

        action_sentence = self.act_with_artificial_intelligence(
            actors_around=actors_around, action_history=action_history, actions=[my_recent_actions, others_recent_actions]
        )

        if not action_sentence:
            return f"{self.name} {self.idle_action()}."

        command_data = self.get_doctor_command(action_sentence)
        command_name = command_data.get("command")

        if command_name and command_name in self.commands:
            print(f"Executing mapped command for {self.name}: '{command_name}'")
            command_to_execute = self.commands[command_name]
            sig = inspect.signature(command_to_execute)

            kwargs_to_pass = {}
            arg_value = command_data.get("arg")

            if 'target' in sig.parameters:
                target_name_part = arg_value.split()[-1] if arg_value else ""
                target_obj = next((actor for actor in actors_around if target_name_part in actor.name), None)
                kwargs_to_pass['target'] = target_obj
            elif 'item' in sig.parameters:
                kwargs_to_pass['item'] = arg_value
            elif 'arg' in sig.parameters:
                kwargs_to_pass['arg'] = arg_value

            command_result = command_to_execute(**kwargs_to_pass)
            dialogue = command_data.get("dialogue")

            final_narrative = action_sentence.strip()
            if not final_narrative.endswith(('.', '!', '?')):
                final_narrative += '.'

            if dialogue:
                clean_dialogue = dialogue.strip().strip('"')
                final_narrative += f' "{clean_dialogue}"'

            final_narrative += f" {command_result}"
            return final_narrative
        else:
            print(f"No specific command mapped for {self.name}. Using generated sentence as action.")
            return action_sentence
