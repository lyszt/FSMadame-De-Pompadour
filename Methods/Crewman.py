import random
import inspect
from typing import Optional, Callable, List

from google import genai
from pydantic import BaseModel, Field

from .Humanoid import Humanoid
from .Ship import Ship
from .Environment import Environment

class Command(BaseModel):
    command: Optional[str] = Field(None, description="The specific command to be executed from the available list.")
    arg: Optional[str] = Field(None, description="The argument required by the command, such as an item or target name.")
    dialogue: Optional[str] = Field(None, description="A single, impactful line of dialogue for the character to say while performing the action.")

def command(func: Callable) -> Callable:
    """Decorator to register a method as an AI-callable command."""
    func.is_command = True
    return func

class Crewman(Humanoid):
    def __init__(self, name: str, net_worth: float, age: int, ship: Ship, environment: Environment, actor_manager):
        super().__init__(f"Crewman {name}", age, net_worth, actor_manager)
        self.ship = ship
        self.environment = environment
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
        print(f"Crewman commands initialized for {self.name}: {list(self.commands.keys())}")


    @command
    def repair_system(self, arg: str) -> str:
        """Attempts to repair a damaged ship system."""
        system_name = arg.lower().strip().replace(" ", "_") if arg else ""
        valid_systems = list(self.ship.get_systems().keys())
        print(f"Ai tried to fix: {arg}")

        if not system_name or system_name not in valid_systems:
            return f"{self.name} tinkers with a console but makes no real progress."

        system_health = self.ship.get_systems()[system_name]['health']
        if system_health >= 100.0:
            return f"{self.name} inspects the {system_name.replace('_', ' ')} system, finding it's in working order."

        repair_amount = random.uniform(5, 10)
        self.ship.repair_system(system_name, repair_amount)

        new_health = self.ship.get_systems()[system_name]['health']
        return f"{self.name} works on the damaged {system_name.replace('_', ' ')} system, managing to restore it to {new_health:.0f}%."

    def get_crewman_command(self, action_sentence: str, actors_around: List[Humanoid]) -> dict:
        """Analyzes a descriptive action sentence to determine which specific command to execute."""
        print(f"Deciding command for {self.name}: '{action_sentence}'")
        command_list_str = "\n".join(
            f'- "{name}": "{desc}"' for name, desc in self.command_descriptions.items()
        )
        valid_systems = list(self.ship.get_systems().keys())
        entities_nearby = ', '.join(actor.name for actor in actors_around if actor.name != self.name) if actors_around else 'no one else'

        prompt = f"""
        You are a command interpreter for a starship crewman in a simulation. Based on the crewman's intended action, choose the most appropriate command.

        Available Commands:
        {command_list_str}
        "None": Use this if the action is purely conversational, observational, or doesn't map to a command.

        Nearby Characters: {entities_nearby}
        
        **Crucially, for `repair_system`, the 'arg' MUST be an exact string from the valid systems list.**

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
        my_recent_actions = actions[0]
        other_recent_actions = actions[1]

        my_actions_str = "\n".join(f"- {action}" for action in my_recent_actions) if my_recent_actions else "None"
        other_actions_str = "\n".join(f"- {action}" for action in other_recent_actions) if other_recent_actions else "None"
        entities_nearby = ', '.join(actor.name for actor in actors_around if actor.name != self.name) if actors_around else 'no one else'

        system_status_report = self.ship.status_report()
        system_strings = [f"{name}: {data['health']:.0f}% ({data['status']})" for name, data in system_status_report["systems"].items()]
        system_status_str = ", ".join(system_strings)

        prompt = f"""
        You are a character in a text-based simulation aboard the French military starship, FS Madame de Pompadour.
        Your name is {self.name}.
        Your personality traits are: {self.personality}
        
        ## Current Situation
        - Ship Systems Status: {system_status_str}
        - Crewmembers nearby: {entities_nearby}
        - Your recent actions (what you did):
        {my_actions_str}
        - Other recent events (what happened around you):
        {other_actions_str}
        - The current ship-wide situation: {self.environment.mood}
        - The ship's mission: {self.environment.mission}
        {self.global_prompt}
        
        ## Your Task
        Based on the situation (especially any assigned tasks or damaged ship systems), what is your next action?
        The response must be a single, complete sentence in the third person describing your action.
        It should be interactive and involve another crewmember or a ship system if possible. 
        Add dialogue using quotations where appropriate.

        Write the complete sentence for {self.name}'s next action now.
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"AI action failed for {self.name}: {e}.")
            return f"{self.name} stares blankly at a bulkhead."

    def act(self, actors_around: list, action_history: list) -> str | None:
        """Decides the next action, choosing between a simple action or a more complex, AI-driven action."""
        my_recent_actions = [action for action in action_history[-self.memory_depth:] if action.startswith(self.name)]
        others_recent_actions = [action for action in action_history[-5:] if not action.startswith(self.name)]

        print(f"\n--- Crewman AI Action Cycle for {self.name} ---")

        action_sentence = self.act_with_artificial_intelligence(
            actors_around=actors_around, action_history=action_history, actions=[my_recent_actions, others_recent_actions]
        )

        if not action_sentence:
            return f"{self.name} stares blankly at a bulkhead."

        command_data = self.get_crewman_command(action_sentence, actors_around)
        command_name = command_data.get("command")

        if command_name and command_name in self.commands:
            print(f"Executing mapped command for {self.name}: '{command_name}'")
            command_to_execute = self.commands[command_name]
            sig = inspect.signature(command_to_execute)

            kwargs_to_pass = {}
            arg_value = command_data.get("arg")

            if 'target' in sig.parameters:
                target_obj = next((actor for actor in actors_around if arg_value and arg_value.lower() in actor.name.lower()), None)
                kwargs_to_pass['target'] = target_obj
            else:
                kwargs_to_pass['arg'] = arg_value

            command_result = command_to_execute(**kwargs_to_pass)
            dialogue = command_data.get("dialogue")

            final_narrative = action_sentence.strip()
            if not final_narrative.endswith(('.', '!', '?')):
                final_narrative += '.'

            if dialogue:
                clean_dialogue = dialogue.strip().strip('"')
                final_narrative += f' "{clean_dialogue}"'

            if command_result and command_result not in final_narrative:
                final_narrative += f" ({command_result})"

            return final_narrative
        else:
            print(f"No specific command mapped for {self.name}. Using generated sentence as action.")
            return action_sentence


