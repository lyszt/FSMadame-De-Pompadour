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
from .Environment import Environment

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

class Crewman(Humanoid):
    """
    Represents a jaded and resourceful character drifting through space.
    Their actions are often cynical and focused on self-preservation,
    shaped by the harsh realities of the void and driven by an AI command system.
    """
    def __init__(self, name: str, net_worth: float, age: int, ship: Ship, environment: Environment):
        super().__init__(f"Crewman {name}", age, net_worth)
        self.ship = ship
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
        print(f"Crewman commands initialized for {self.name}: {list(self.commands.keys())}")


    @command
    def throw_away_own_stuff(self) -> str:
        """Empties the entire personal inventory into a disposal chute."""
        if len(self.inventory.inventory) < 1:
            return f"{self.name} checks their pockets but finds them empty."
        self.inventory.empty()
        return f"{self.name} finds a disposal chute and gets rid of all their personal items. 'Less weight, less problems,' they mutter."

    @command
    def acquire_item(self, item: str) -> str:
        """Acquires a new item for their personal inventory, viewing it with cynical pragmatism."""
        if not item:
            return f"{self.name} considers acquiring something, but can't decide what."
        self.inventory.add(item)
        return f"{self.name} acquires a '{item}'. They give it a cursory glance before stowing it away."

    @command
    def remove_item(self, item: str) -> str:
        """Removes a specific item from their personal inventory."""
        if not item:
            return f"{self.name} thinks about getting rid of an item, but doesn't."
        try:
            self.inventory.remove(item)
            return f"{self.name} discards their '{item}'."
        except ValueError:
            return f"{self.name} looks for a '{item}' to discard, but doesn't have one."

    @command
    def get_inventory(self) -> str:
        """Checks their own personal inventory."""
        items = self.inventory.inventory
        if len(items) < 1:
            return f"{self.name} checks their pockets and finds nothing."
        return f"{self.name} takes stock of their personal belongings: {', '.join(items)}."

    @command
    def punch(self, target: Humanoid) -> str:
        """Starts a physical altercation with another crew member."""
        if not target:
            return f"{self.name} swings at the air, looking foolish."
        target.lose_hp(random.uniform(1, 10))
        places_to_punch = ["jaw", "nose", "stomach", "ribs", "shoulder", "eye", "ear"]
        return f"{self.name} punches {target.name} right in the {random.choice(places_to_punch)}."

    @command
    def shoot(self, target: Humanoid) -> str:
        """Uses a personal weapon against another crew member. A highly aggressive and dangerous act."""
        if not target:
            return f"{self.name} nervously draws a weapon but has no one to aim at."
        damage = random.uniform(15, 50)
        if target.health - damage <= 0:
            target.lose_hp(damage)
            return f"{self.name} pulls out a concealed weapon and kills {target.name} in a shocking act of violence."
        else:
            target.lose_hp(damage)
            return f"{self.name} shoots and wounds {target.name}."

    # --- Original Action Methods (Preserved) ---

    def idle_action(self) -> str:
        """Pulls a random, mundane space-themed action from a file."""
        try:
            with open("Methods/Datasets/crewman_actions.txt", "r") as f:
                action_list = [line.strip() for line in f if line.strip()]
            return random.choice(action_list)
        except FileNotFoundError:
            return "stares blankly at a bulkhead."

    def against_another_neutral(self) -> str:
        """Pulls a random neutral action targeting another character."""
        try:
            with open("Methods/Datasets/crewman_target_actions_neutral.txt", "r") as f:
                action_list = [line.strip() for line in f if line.strip()]
            return random.choice(action_list)
        except FileNotFoundError:
            return "gives a slight nod to"


    def get_crewman_command(self, action_sentence: str) -> dict:
        """Analyzes a descriptive action sentence to determine which specific command to execute."""
        print(f"Deciding command for {self.name}: '{action_sentence}'")
        command_list_str = "\n".join(
            f'- "{name}": "{desc}"' for name, desc in self.command_descriptions.items()
        )

        prompt = f"""
        You are a command interpreter for a starship crewman in a simulation. Based on the crewman's intended action, choose the most appropriate command, extract its argument, and create a line of dialogue.

        Available Commands:
        {command_list_str}
        "None": Use this if the action does not map to any command.

        Instructions:
        1. Analyze the crewman's intended action below.
        2. If it maps to one of the available commands, identify that command.
        3. If the command requires an argument (like an item or another crewman's name), extract it for the "arg" field.
        4. Generate a single, in-character line of dialogue for the crewman that fits the action. Place it in the "dialogue" field.
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
        my_recent_actions = actions[0]
        other_recent_actions = actions[1]

        my_actions_str = "\n".join(f"- {action}" for action in my_recent_actions) if my_recent_actions else "None"
        other_actions_str = "\n".join(f"- {action}" for action in other_recent_actions) if other_recent_actions else "None"
        entities_nearby = ', '.join(actor.name for actor in actors_around if actor.name != self.name) if actors_around else 'no one else'

        prompt = f"""
        You are a character in a text-based simulation aboard the French military starship, FS Madame de Pompadour.
        Your name is {self.name}.
        
        ## Your Role and Context
        You are one of the many enlisted crewmembers on the lower decks, the "common folk" of the ship. You wear a standard-issue uniform,
         performing the day-to-day tasks that keep the vessel operational. Your life is a routine of 
         duties, shared mess halls, and cramped corridors filled with your fellow crew.
          You are not an officer or a specialist; you are part of the ship's essential rank-and-file.
         To your benefit, or not, your personality traits are: {self.personality}
         
        ## Current Situation
        - Crewmembers nearby: {entities_nearby}
        - Your recent actions (what you did):
        {my_actions_str}
        - Other recent events (what happened around you):
        {other_actions_str}
        - The current ship-wide situation: {self.environment.mood}

        ## Your Task
        Based on the events listed above and your role as a standard crewman, what do you do next? 
        Your action should be something a typical person in your position might do. It could be related
         to a simple ship duty, a mundane reaction to a crewmate, or a personal act while moving through the ship.
         The ship's mission: {self.environment.mission}
        
        The response must be a single, complete sentence in the third person describing your character's
        action. Do not add any extra explanation.
        Your action should be interactive and reflect your life. It should involve another 
        crewmember if possible, focusing on conversation, shared tasks, or simple social exchanges. 
        Avoid passive or silent actions where you don't interact with anyone.
        Add dialogues using quotations.

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

        print(f"\n--- Crewman AI Action Cycle for {self.name} ---")

        action_sentence = self.act_with_artificial_intelligence(
            actors_around=actors_around, action_history=action_history, actions=[my_recent_actions, others_recent_actions]
        )

        if not action_sentence:
            return f"{self.name} {self.idle_action()}."

        command_data = self.get_crewman_command(action_sentence)
        command_name = command_data.get("command")

        if command_name and command_name in self.commands:
            print(f"Executing mapped command for {self.name}: '{command_name}'")
            command_to_execute = self.commands[command_name]
            sig = inspect.signature(command_to_execute)

            kwargs_to_pass = {}
            arg_value = command_data.get("arg")

            if 'target' in sig.parameters:
                target_name_part = arg_value.split()[-1] if arg_value else "" # Try to get the name
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
