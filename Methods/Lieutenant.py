import random
import inspect
from typing import Optional, Callable

from google import genai
from pydantic import BaseModel, Field

from .Humanoid import Humanoid
from Methods.System.Ship.Ship import Ship


class Command(BaseModel):
    command: Optional[str] = Field(None, description="The specific command to be executed from the available list.")
    arg: Optional[str] = Field(None, description="The argument required by the command, such as an item or target name.")
    dialogue: Optional[str] = Field(None, description="A single, impactful line of dialogue for the lieutenant to say while performing the action.")


def command(func: Callable) -> Callable:
    """Decorator to register a method as an AI-callable command."""
    func.is_command = True
    return func


class Lieutenant(Humanoid):
    """
    Represents the executive officer of a starship, second-in-command.
    The Lieutenant is responsible for executing the captain's orders and managing
    crew-level tasks. Archetypally: tactical executor, bridge between captain and crew.
    Note: Personality is not set here; it is provided externally.
    """

    def __init__(self, name: str, net_worth: float, age: int, ship_command: Ship, environment: 'Environment', actor_manager, mini_llm):
        self.ship: Ship = ship_command
        self.environment: 'Environment' = environment

        super().__init__(f"Lieutenant {name}", age, net_worth, actor_manager, mini_llm)

        self.client = genai.Client()

        # Discover lieutenant commands
        self.commands = {}
        self.command_descriptions = {}
        self._discover_commands()

    def _discover_commands(self):
        """Automatically finds all methods decorated with @command."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, 'is_command'):
                self.commands[name] = method
                self.command_descriptions[name] = inspect.getdoc(method) or "No description available."
        print(f"Lieutenant commands initialized: {list(self.commands.keys())}")

    # --------------------------
    # Lieutenant Commands
    # --------------------------

    def assist_repairs(self, system: str) -> str:
        """Personally assists the engineering crew with repairing a system."""
        if not system or system not in self.ship.get_systems().keys():
            return f"{self.name} offers to help, but the repair target is unclear."
        return f"{self.name} joins engineering crews to expedite repairs on the {system.replace('_', ' ')}."


    @command
    def idle_action(self) -> str:
        """Pulls a random idle action."""
        options = [
            "paces thoughtfully across the bridge",
            "adjusts the collar of their uniform",
            "reviews tactical readouts",
            "shares a quick word with the helm officer"
        ]
        return f"{self.name} {random.choice(options)}."


    def get_lieutenant_command(self, action_sentence: str) -> dict:
        """
        Analyzes a descriptive action sentence to determine which specific command, argument, and dialogue to use.
        """
        print(f"Deciding command for lieutenant action: '{action_sentence}'")
        command_list_str = "\n".join(
            f'- "{name}": "{desc}"' for name, desc in self.command_descriptions.items()
        )
        valid_systems = list(self.ship.get_systems().keys())

        prompt = f"""
        You are a command interpreter for a starship lieutenant in a simulation. Based on the lieutenant's intended action, choose the most appropriate command, extract its argument, and create a line of dialogue.
        
        Available Commands:
        {command_list_str}

        "None": Use this if the action is purely conversational or doesn't map to a command.

        Instructions:
        1. Analyze the lieutenant's intended action below.
        2. If it clearly maps to one of the available commands, identify that command.
        3. If the command requires an argument (like a destination, item, or system name), extract it for the "arg" field.
        4. Generate a single, in-character line of dialogue for the lieutenant that fits the action.
        5. If the action does not correspond to any known command, return "None" for the command.
        6. For the `assist_repairs` command, you MUST translate the lieutenant's words into one of the exact system names from this list: {valid_systems}.

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
            print(f"Lieutenant command decision from AI: {response.text}")
            command_obj = Command.model_validate_json(response.text)
            return command_obj.model_dump()
        except Exception as e:
            print(f"Error decoding command from LLM: {e}")
            return {"command": "None", "arg": None, "dialogue": None}

    def act_with_artificial_intelligence(self, actors_around: list, action_history: list, actions: list) -> str:
        """
        Uses a generative AI to determine the lieutenant's next action based on personality and recent events.
        """
        my_recent_actions = actions[0]
        other_recent_actions = actions[1]

        my_actions_str = "\n".join(f"- {action}" for action in my_recent_actions) if my_recent_actions else "None"
        other_actions_str = "\n".join(f"- {action}" for action in other_recent_actions) if other_recent_actions else "None"
        entities_nearby = ', '.join(actor.name for actor in actors_around if actor.name != self.name) if actors_around else 'no one else'

        prompt = f"""
        You are a character in a text-based simulation aboard the French military starship, FS Madame de Pompadour.
        Your name is {self.name}.

        ## Your Role and Context
        You are the Lieutenant, second-in-command of the vessel. Your role is to carry out the Captain's orders and take tactical initiative when necessary.
        Your personality traits are: {self.personality}. Act upon those traits.
        The ship's mission: {self.environment.mission}
        ## Current Situation
        - **Officers/Crew nearby:** {entities_nearby}
        - **Your recent actions (what you did):**
        {my_actions_str}
        - **Other recent events (what happened around you):**
        {other_actions_str}
        - **The current ship-wide situation:**
        {self.environment.situation}

        ## Your Task & Rules
        1. If you have pending orders from the Captain, act to carry them out.
        2. If no orders are pending, take tactical initiative: motivate crew, assist repairs, or lead a team.
        3. Avoid redundant requests for information; prefer decisive execution.
        4. Always move the situation forward.
        {self.global_prompt}
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

    # --------------------------
    # Behavior
    # --------------------------

    def act(self, actors_around: list, action_history: list) -> str | None:
        """Decides the lieutenant's next action using orders, simple actions, or AI-driven actions."""
        # Always prioritize pending orders
        if self.tasks:
            return self.execute_next_order()

        my_recent_actions = [action for action in action_history[-self.memory_depth:] if action.startswith(self.name)]
        print(f"\n--- Lieutenant AI Action Cycle for {self.name} ---")

        others_recent_actions = [action for action in action_history[-5:] if not action.startswith(self.name)]
        action_sentence = self.act_with_artificial_intelligence(
            actors_around=actors_around, action_history=action_history, actions=[my_recent_actions, others_recent_actions]
        )

        if not action_sentence:
            return f"{self.name} {self.idle_action()}."

        command_data = self.get_lieutenant_command(action_sentence)
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
            elif 'destination' in sig.parameters:
                kwargs_to_pass['destination'] = arg_value
            elif 'system' in sig.parameters:
                kwargs_to_pass['system'] = arg_value
            elif 'order' in sig.parameters:
                kwargs_to_pass['order'] = arg_value
            elif 'item' in sig.parameters:
                kwargs_to_pass['item'] = arg_value

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
