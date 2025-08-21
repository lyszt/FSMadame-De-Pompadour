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
from .Environment import Environment # Assuming Environment class is in this file


# Pydantic model to define the structure for the AI's JSON output.
class Command(BaseModel):
    command: Optional[str] = Field(None, description="The specific command to be executed from the available list.")
    arg: Optional[str] = Field(None, description="The argument required by the command, such as an item or target name.")
    dialogue: Optional[str] = Field(None, description="A single, impactful line of dialogue for the captain to say while performing the action.")


def command(func: Callable) -> Callable:
    """Decorator to register a method as an AI-callable command."""
    func.is_command = True
    return func


class Captain(Humanoid):
    """
    Represents the commanding officer of a starship, a figure of authority and strategic thinking.
    The Captain uses an AI layer to interpret high-level intentions into specific, executable commands.
    """
    def __init__(self, name: str, net_worth: float, age: int, ship_command: Ship, environment: Environment):
        """
        Initializes the Captain instance.
        """
        self.ship: Ship = ship_command
        super().__init__(f"Captain {name}", age, net_worth)

        self.client = genai.Client()
        self.environment = environment

        # Dictionaries to hold the discovered commands and their descriptions
        self.commands = {}
        self.command_descriptions = {}
        self._discover_commands()

    def _discover_commands(self):
        """
        Automatically finds all methods decorated with @command.
        """
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, 'is_command'):
                self.commands[name] = method
                self.command_descriptions[name] = inspect.getdoc(method) or "No description available."
        print(f"Captain commands initialized: {list(self.commands.keys())}")


    @command
    def jettison_cargo(self) -> str:
        """Orders the ship's entire cargo hold to be jettisoned into space."""
        if len(self.ship.cargo.inventory) < 1:
            return "The cargo hold is already empty."
        self.ship.cargo.empty()
        return "The cargo bay doors open, and all contents are jettisoned into space."

    @command
    def acquire_item(self, item: str) -> str:
        """Formally acquires a new item for the captain's personal inventory."""
        if not item:
            return "The captain thinks about acquiring an item, but doesn't specify what."
        self.inventory.add(item)
        return f"The item '{item}' is now in the captain's personal possession."

    @command
    def remove_item(self, item: str) -> str:
        """Removes a specific item from the captain's personal inventory."""
        if not item:
            return "The captain prepares to discard an item, but then stops."
        try:
            self.inventory.remove(item)
            return f"The captain discards the '{item}' he was carrying."
        except ValueError:
            return f"The captain checks his pockets for '{item}' but doesn't have it."

    @command
    def get_inventory(self) -> str:
        """Returns a list of items in the captain's personal inventory."""
        items = self.inventory.inventory
        if len(items) < 1:
            return "The captain checks his pockets and finds them empty."
        return f"The captain checks his personal belongings and finds: {', '.join(items)}."

    @command
    def request_status_report(self) -> str:
        """Asks the ship's computer for a full status report on all major systems."""
        report = self.ship.status_report()
        system_strings = [
            f"{name.replace('_', ' ').title()} at {data['health']:.0f}% ({data['status']})"
            for name, data in report["systems"].items()
        ]
        status_lines = f"Overall Integrity: {report['integrity']:.0f}%\n- " + "\n- ".join(system_strings)
        return f"The main screen displays the ship's status:\n{status_lines}"

    @command
    def order_repairs(self, arg: str) -> str:
        """Orders the engineering team to repair a damaged ship system. The captain gives the order; the crew must carry it out."""
        system_name = arg.lower() if arg else ""
        if not system_name or system_name not in self.ship.get_systems().keys():
            return "The chief engineer responds that the order was unclear."
        return f"An order is dispatched to engineering to prioritize repairs on the {system_name.replace('_', ' ')} system."

    @command
    def fire_weapons(self, arg: str) -> str:
        """Orders the ship's weapon systems to fire upon a specific target."""
        target_name = arg
        if not target_name:
            return "The weapons officer reports no target was specified."

        visible_ships = self.environment.get_visible_ships()
        target_ship = next((ship for ship in visible_ships if ship.name.lower() == target_name.lower()), None)

        if not target_ship:
            return f"Sensors cannot find a target named '{target_name}' in this sector."

        shot_hits = self.ship.weapon_system.shoot(target_ship, self.ship)
        if shot_hits:
            return f"The {self.ship.weapon_system.name} fires at {target_ship.name} and scores a direct hit!"
        else:
            return f"The {self.ship.weapon_system.name} fires at {target_ship.name}, but the shot misses."


    @command
    def check_cargo_manifest(self) -> str:
        """Checks the manifest of the ship's main cargo hold."""
        cargo_items = self.ship.cargo.inventory
        if len(cargo_items) < 1:
            return "The inventory manifest shows the cargo hold is empty."
        return f"The cargo manifest lists: {', '.join(map(str, cargo_items))}."

    @command
    def idle_action(self) -> str:
        """Pulls a random, command-themed action from a file."""
        try:
            with open("Methods/Datasets/captain_actions.txt", "r", encoding="utf-8") as f:
                action_list = [line.strip() for line in f if line.strip()]
            return random.choice(action_list) if action_list else "stands at ease"
        except FileNotFoundError:
            return "reviews a datapad"

    @command
    def against_another_neutral(self) -> str:
        """Pulls a random neutral action targeting another character."""
        try:
            with open("Methods/Datasets/captain_target_actions_neutral.txt", "r", encoding="utf-8") as f:
                action_list = [line.strip() for line in f if line.strip()]
            return random.choice(action_list) if action_list else "glances at"
        except FileNotFoundError:
            return "acknowledges"

    @command
    def punch(self, target: Humanoid):
        """Starts a physical altercation with another character."""
        if not target:
            return f"{self.name} swings at the air."
        if not target.alive:
            return f"{self.name} looks at {target.name}'s body but does nothing."
        target.lose_hp(random.uniform(1,10))
        places_to_punch = ["jaw", "nose", "stomach", "ribs", "chest", "shoulder"]
        return f"{self.name} punches {target.name} right in the {random.choice(places_to_punch)}."

    @command
    def shoot(self, target: Humanoid):
        """Uses a personal weapon against another character."""
        if not target:
            return f"{self.name} draws a weapon but has no target."
        if not target.alive:
            return f"{self.name} aims their weapon at {target.name}'s body but doesn't fire."
        damage = random.uniform(15,50)
        if target.health - damage <= 0:
            target.lose_hp(damage)
            return f"{self.name} pulled his weapon and killed {target.name}."
        else:
            target.lose_hp(damage)
            return f"{self.name} shot and wounded {target.name}."

    def get_captain_command(self, action_sentence: str) -> dict:
        """
        Analyzes a descriptive action sentence to determine which specific command, argument, and dialogue to use.
        """
        print(f"Deciding command for action: '{action_sentence}'")
        command_list_str = "\n".join(
            f'- "{name}": "{desc}"' for name, desc in self.command_descriptions.items()
        )
        valid_systems = list(self.ship.get_systems().keys())

        prompt = f"""
        You are a command interpreter for a starship captain in a simulation. Based on the captain's intended action, choose the most appropriate command, extract its argument, and create a line of dialogue.

        Available Commands:
        {command_list_str}
        
        "None": Use this if the action is purely conversational or doesn't map to a command.

        Instructions:
        1. Analyze the captain's intended action below.
        2. If it clearly maps to one of the available commands, identify that command.
        3. If the command requires an argument (like an item name or a character's name), extract it for the "arg" field.
        4. Generate a single, in-character line of dialogue for the captain that fits the action. Place it in the "dialogue" field.
        5. If the action does not correspond to any known command, return "None" for the command.
        6.  **Crucially, for the `order_repairs` command, you MUST translate the captain's words into one of the exact system names from this list: {valid_systems}. This translated name is the `arg`.**
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
            print(f"Command decision from AI: {response.text}")
            command_obj = Command.model_validate_json(response.text)
            return command_obj.model_dump()
        except Exception as e:
            print(f"Error decoding command from LLM: {e}")
            return {"command": "None", "arg": None, "dialogue": None}

    def act_with_artificial_intelligence(self, actors_around: list, action_history: list, actions: list) -> str:
        """
        Uses a generative AI to determine the next action based on personality and recent events.
        """
        my_recent_actions = actions[0]
        other_recent_actions = actions[1]

        my_actions_str = "\n".join(f"- {action}" for action in my_recent_actions) if my_recent_actions else "None"
        other_actions_str = "\n".join(f"- {action}" for action in other_recent_actions) if other_recent_actions else "None"
        entities_nearby = ', '.join(actor.name for actor in actors_around if actor.name != self.name) if actors_around else 'no one else'

        # CORRECTED: This is the new, improved prompt to prevent logic loops.
        prompt = f"""
        You are a character in a text-based simulation aboard the French military starship, FS Madame de Pompadour.
        Your name is {self.name}.
        
        ## Your Role and Context
        You are the Captain, the commanding officer of the entire vessel. Your goal is to resolve situations, not just report on them.
        To your benefit or not, your personality traits are: {self.personality}. Act upon those traits.

        ## Current Situation
        - **Officers/Crew nearby:** {entities_nearby}
        - **Your recent actions (what you did):**
        {my_actions_str}
        - **Other recent events (what happened around you):**
        {other_actions_str}
        - **The current ship-wide situation:**
        {self.environment.situation}

        ## Your Task & Rules
        1.  **Analyze the situation:** Look at the ship-wide situation and recent events.
        2.  **Avoid Redundancy:** If you have recently requested a status report or asked for information about the current problem, **do not do the same thing.**
        3.  **Take Decisive Action:** Your job is to move the situation forward. Instead of asking for information that was just provided, issue a direct order to solve the problem. Order your crew.
        4.  **Be a Commander:** Your action must be a clear command or a direct interaction with a crew member or ship system.

        Based on these rules, what is your next decisive action? The response must be a single, complete sentence in the third person, including dialogue.

        Write the complete sentence for {self.name}'s next action now.
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            ai_action_sentence = response.text.strip()
            return ai_action_sentence
        except Exception as e:
            print(f"AI action generation failed: {e}. Falling back to default idle action.")
            return f"{self.name} {self.idle_action()}."

    def act(self, actors_around: list, action_history: list) -> str | None:
        """
        Decides the next action, choosing between a simple action,
        an action against another, or a more complex, AI-driven action.
        """
        my_recent_actions = [action for action in action_history[-self.memory_depth:] if action.startswith(self.name)]

        if not my_recent_actions:
            # Fallback to simple, non-AI actions if there's no history
            options = ["to_oneself", "against_another"]
            choice = random.choice(options)
            if choice == "against_another" and not actors_around:
                choice = "to_oneself"
            match choice:
                case "to_oneself":
                    return f"{self.name} {self.idle_action()}."
                case "against_another":
                    target = random.choice(actors_around)
                    return f"{self.name} {self.against_another_neutral()} {target.name}."

        print(f"\n--- Captain AI Action Cycle for {self.name} ---")

        others_recent_actions = [action for action in action_history[-5:] if not action.startswith(self.name)]
        action_sentence = self.act_with_artificial_intelligence(
            actors_around=actors_around, action_history=action_history, actions=[my_recent_actions, others_recent_actions]
        )

        if not action_sentence:
            return f"{self.name} {self.idle_action()}."

        command_data = self.get_captain_command(action_sentence)
        command_name = command_data.get("command")

        if command_name and command_name in self.commands:
            print(f"Executing mapped command: '{command_name}'")
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
                final_narrative += f' "{clean_dialogue}," he says.'

            final_narrative += f" {command_result}"
            return final_narrative
        else:
            print("No specific command mapped. Using generated sentence as action.")
            return action_sentence
