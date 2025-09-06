import random
import inspect
from typing import List, Optional, Callable

from google import genai
from pydantic import BaseModel, Field

from .Humanoid import Humanoid
from .Ship import Ship

class _CharacterSheetSchema(BaseModel):
    name: str = Field(..., description="The character's full name.")
    age: int = Field(..., description="The character's age, appropriate for their backstory.")
    race: str = Field(..., description="A sci-fi species or race for the character (e.g., Human, Martian, Arcturian).")
    profession: str = Field(..., description="The character's primary role or job on the ship (e.g., Engineer, Medic, Stowaway).")
    appearance: str = Field(..., description="A brief, one-sentence physical description of the character.")
    core_attribute: str = Field(..., description="The character's single strongest attribute (e.g., Intelligent, Charismatic, Strong, Agile).")
    primary_skill: str = Field(..., description="The character's most developed practical skill (e.g., Engineering, Negotiation, Marksmanship, Piloting).")
    personality_traits: List[str] = Field(..., description="A list of three distinct personality traits that define their behavior.")
    motivation: str = Field(..., description="What fundamentally drives this character? (e.g., 'To earn enough money to retire,' 'To uncover a political conspiracy').")
    secret: str = Field(..., description="A hidden secret the character is protecting.")
    backstory: str = Field(..., description="A brief, one or two-sentence backstory explaining their origin and why they are on this ship.")

class Command(BaseModel):
    command: Optional[str] = Field(None, description="The specific command to be executed.")
    arg: Optional[str] = Field(None, description="The argument for the command, if needed.")
    dialogue: Optional[str] = Field(None, description="A line of dialogue for the character to say.")

def command(func: Callable) -> Callable:
    """Decorator to register a method as an AI-callable command."""
    func.is_command = True
    return func

class AICharacter(Humanoid):
    """
    An intelligent, autonomous character in the simulation. Inherits base
    humanoid properties and adds a sophisticated AI layer for decision-making.
    This character generates its own attributes via an AI call upon creation.
    """
    def __init__(
            self,
            concept: str,
            ship: Ship,
            environment: 'Environment',
            net_worth: float = 100.0
    ):
        self.ship = ship
        self.environment = environment
        self.client = genai.Client()

        # Instantiate self concept from prompt
        self._generate_and_apply_sheet(concept)
        super().__init__(self.name, self.age, net_worth)

        self.commands = {}
        self.command_descriptions = {}
        self._discover_commands()

    def _generate_and_apply_sheet(self, concept: str):
        """
        Calls the AI to generate character details from a concept and applies them directly to the instance.
        This method is called by __init__ to self-populate the character sheet.
        """
        print(f"Generating new AI character from concept: '{concept}'")

        prompt = f"""
        You are a character creator for a sci-fi RPG. Based on the following high-level concept,
        generate a complete, detailed character profile.

        CONCEPT: "{concept}"

        Fill out all fields of the character sheet. The output must be a single, valid JSON object.
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json", "response_schema": _CharacterSheetSchema}
            )

            sheet_data = _CharacterSheetSchema.model_validate_json(response.text)
            self.name = sheet_data.name
            self.age = sheet_data.age
            self.race = sheet_data.race
            self.profession = sheet_data.profession
            self.appearance = sheet_data.appearance
            self.core_attribute = sheet_data.core_attribute
            self.primary_skill = sheet_data.primary_skill
            self.personality_traits = sheet_data.personality_traits
            self.motivation = sheet_data.motivation
            self.secret = sheet_data.secret
            self.backstory = sheet_data.backstory

        except Exception as e:
            print(f"Failed to generate AI character from concept: {e}. Applying default fallback values.")
            self.name = "T-800"
            self.age = 35
            self.race = "Cyborg"
            self.profession = "Infiltrator"
            self.appearance = "A stoic figure with a metallic sheen beneath their skin."
            self.core_attribute = "Strong"
            self.primary_skill = "Marksmanship"
            self.personality_traits = ["Determined", "Laconic", "Unrelenting"]
            self.motivation = "To protect John Connor."
            self.secret = "Is a machine from the future."
            self.backstory = "Sent back in time to alter the course of a future war."

    def _discover_commands(self):
        """Finds all methods decorated with @command."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, 'is_command'):
                self.commands[name] = method
                self.command_descriptions[name] = inspect.getdoc(method) or "No description available."
        print(f"Commands for {self.name} initialized: {list(self.commands.keys())}")

    @command
    def perform_task(self, arg: str) -> str:
        """Performs a task related to their profession or a general ship duty."""
        task = arg or f"duties associated with being a {self.profession}"
        return f"{self.name} gets to work on {task}."

    @command
    def acquire_item(self, arg: str) -> str:
        """Acquires a new item for personal inventory."""
        if not arg: return f"{self.name} acquires nothing."
        self.inventory.add(arg)
        return f"The item '{arg}' is now in {self.name}'s possession."

    @command
    def get_inventory(self, arg: Optional[str] = None) -> str:
        """Returns a list of items in personal inventory."""
        items = self.inventory.inventory
        if not items:
            return f"{self.name} checks their pockets and finds them empty."
        return f"{self.name} checks their belongings and finds: {', '.join(items)}."

    @command
    def request_status_report(self, arg: Optional[str] = None) -> str:
        """Asks for a status report on ship systems."""
        report = self.ship.status_report()
        system_strings = [f"{name.replace('_', ' ').title()} at {data['health']:.0f}% ({data['status']})" for name, data in report["systems"].items()]
        status_lines = f"Overall Integrity: {report['integrity']:.0f}%\n- " + "\n- ".join(system_strings)
        return f"{self.name} checks a console which displays the ship's status:\n{status_lines}"

    @command
    def punch(self, target: Humanoid) -> str:
        """Starts a physical altercation with another character."""
        if not target:
            return f"{self.name} swings at the air, looking foolish."
        if not target.alive:
            return f"{self.name} looks at {target.name}'s body but does nothing."
        target.lose_hp(random.uniform(1, 10))
        if not target.alive:
            return f"{self.name} gives a final punch to finish {target.name}, now ragdolling in the ground."
        places_to_punch = ["jaw", "nose", "stomach", "ribs", "shoulder"]
        return f"{self.name} punches {target.name} in the {random.choice(places_to_punch)}."

    @command
    def shoot(self, target: Humanoid) -> str:
        """Uses a personal weapon against another character. A highly aggressive and dangerous act."""
        if not target:
            return f"{self.name} draws a weapon but has no one to aim at."
        if not target.alive:
            return f"{self.name} aims their weapon at {target.name}'s body but doesn't fire."
        damage = random.uniform(15, 50)
        target.lose_hp(damage)
        if not target.alive:
            return f"{self.name} pulls out a concealed weapon and kills {target.name} in a shocking act of violence."
        else:
            return f"{self.name} shoots and wounds {target.name}."

    def get_character_command(self, action_sentence: str, actors_around: List[Humanoid]) -> dict:
        """Analyzes an intended action to map it to a specific command."""
        command_list_str = "\n".join(f'- "{name}": "{desc}"' for name, desc in self.command_descriptions.items())
        entities_nearby = ', '.join(actor.name for actor in actors_around if actor.name != self.name) if actors_around else 'no one else'

        prompt = f"""
        You are a command interpreter for a character in a simulation.
        Based on the character's intended action, choose the most appropriate command from the list.
        
        Available Commands:
        {command_list_str}
        "None": Use if the action is purely observational or internal thought.

        Nearby Characters: {entities_nearby}

        Intended Action: "{action_sentence}"
        
        If the action targets a character (e.g., 'punch Bob', 'talk to Jane'), the 'arg' must be that character's name.
        Respond with only the JSON object for the best command.
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={"response_mime_type": "application/json", "response_schema": Command}
            )
            return Command.model_validate_json(response.text).model_dump()
        except Exception as e:
            print(f"Error decoding command for {self.name}: {e}")
            return {"command": "None", "arg": None, "dialogue": action_sentence}

    def act_with_artificial_intelligence(self, action_history: list, actors_around: List[Humanoid]) -> str:
        """Uses generative AI to determine the character's next action."""
        recent_events = "\n".join(f"- {action}" for action in action_history[-10:])
        entities_nearby = ', '.join(actor.name for actor in actors_around if actor.name != self.name) if actors_around else 'no one else'

        prompt = f"""
        You are a character in a text-based simulation on the starship FS Madame de Pompadour.
        
        ## Your Character Sheet
        - Name: {self.name}
        - Profession: {self.profession}
        - Personality: {self.personality_traits}
        - Motivation: {self.motivation}
        - Secret: {self.secret}

        ## Current Situation
        - Ship-wide situation: {self.environment.situation}
        - Nearby Characters: {entities_nearby}
        - Recent events:
        {recent_events}

        ## Your Task
        Based on your personality, motivation, and the current situation, what is your next action?
        Your action must be a single, complete sentence in the third person. It should be interactive if possible.

        Write the complete sentence for {self.name}'s next action now.
        """
        try:
            response = self.client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            return response.text.strip()
        except Exception as e:
            print(f"AI action generation for {self.name} failed: {e}")
            return f"{self.name} pauses, considering their next move."

    def act(self, action_history: list, actors_around: List[Humanoid]) -> str:
        """Orchestrates the character's turn."""
        print(f"\n--- AI Action Cycle for {self.name} ---")

        action_sentence = self.act_with_artificial_intelligence(action_history, actors_around)
        command_data = self.get_character_command(action_sentence, actors_around)
        command_name = command_data.get("command")

        if command_name and command_name in self.commands:
            print(f"Executing mapped command for {self.name}: '{command_name}'")
            command_to_execute = self.commands[command_name]
            sig = inspect.signature(command_to_execute)

            kwargs_to_pass = {}
            arg_value = command_data.get("arg")

            if 'target' in sig.parameters:
                target_obj = next((actor for actor in actors_around if arg_value and arg_value in actor.name), None)
                kwargs_to_pass['target'] = target_obj
            else: # Handles 'arg', 'item', etc.
                kwargs_to_pass['arg'] = arg_value

            command_result = command_to_execute(**kwargs_to_pass)
            dialogue = command_data.get("dialogue")

            final_narrative = action_sentence.strip()
            if not final_narrative.endswith(('.', '!', '?')):
                final_narrative += '.'

            if dialogue:
                final_narrative += f' "{dialogue.strip()}"'

            if command_result and command_result not in final_narrative:
                final_narrative += f" ({command_result})"

            return final_narrative
        else:
            return action_sentence

