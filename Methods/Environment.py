import random
import inspect
import json
from typing import List, Optional, Callable
from google import genai
from pydantic import BaseModel, Field

from .Ship import Ship
from .Humanoid import Humanoid

class Command(BaseModel):
    command: Optional[str] = Field(None, description="The specific environmental command to be executed from the available list.")
    arg: Optional[str] = Field(None, description="The argument required by the command, such as a system or character name.")
    dialogue: Optional[str] = Field(None, description="A descriptive, third-person sentence describing the event as it happens.")

def command(func: Callable) -> Callable:
    """Decorator to register a method as an AI-callable environmental command."""
    func.is_command = True
    return func

class Environment:
    def __init__(self, main_ship: Ship, ships_sector: List[Ship] = None):
        if ships_sector is None:
            ships_sector = []
        self.main_ship: Ship = main_ship
        self.mood = "Regular"
        self.planet = None
        self.anomalies: List[str] = []
        self.ships_sector: List[Ship] = ships_sector
        self.situation = None
        self.client = genai.Client()
        self.commands = {}
        self.command_descriptions = {}
        self._discover_commands()

    def _discover_commands(self):
        """Finds all methods decorated with @command and populates the command dictionaries."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, 'is_command'):
                self.commands[name] = method
                self.command_descriptions[name] = inspect.getdoc(method) or "No description available."
        print(f"Environment commands initialized: {list(self.commands.keys())}")



    @command
    def trigger_system_malfunction(self, arg: str) -> str:
        """Causes a random or specified system on the main ship to take minor damage from an external event."""
        valid_systems = list(self.main_ship.get_systems().keys())
        system_to_damage = arg if arg in valid_systems else random.choice(valid_systems)

        damage_amount = random.uniform(5, 15)
        self.main_ship.apply_damage_to_system(system_to_damage, damage_amount, "environmental stress")
        return f"The {system_to_damage.replace('_', ' ')} system on the {self.main_ship.name} reports a sudden loss of efficiency."

    @command
    def new_ship_enters_sector(self, arg: str) -> str:
        """A new, unidentified ship appears on sensors."""
        ship_type = arg or "unidentified vessel"
        # In a real implementation, you would create and append a new Ship object here.
        return f"Long-range sensors pick up a new contact: an {ship_type} entering the sector."

    @command
    def broadcast_external_hail(self, arg: str) -> str:
        """An incoming message is detected from an unknown source."""
        message_content = arg or "a garbled, repeating signal"
        return f"The communications console lights up with an incoming hail from an unknown source. The message is {message_content}."

    @command
    def generate_ambient_event(self, arg: str) -> str:
        """A minor, non-critical environmental event occurs."""
        event_description = arg or "a brief flicker in the ship's lighting"
        return f"A minor environmental event occurs: {event_description}."

    @command
    def generate_new_anomaly(self, arg: Optional[str] = None) -> str:
        """Discovers a new, previously unknown spatial anomaly on long-range scans."""
        prompt = "You are a science fiction writer. Invent a name and a one-sentence description for a strange spatial anomaly a starship might encounter. Example: 'A chroniton-flux field where time flows intermittently.' Respond with only the name and description."
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt
            )
            new_anomaly = response.text.strip()
            self.anomalies.append(new_anomaly)
            return f"Sensors have detected a new, strange phenomenon: {new_anomaly}"
        except Exception as e:
            print(f"AI anomaly generation failed: {e}")
            return "Sensors detect a minor, unclassified energy reading."

    @command
    def set_mood(self, arg: str) -> str:
        """Changes the ambient mood of the sector (e.g., 'Tense', 'Calm', 'Hostile'), influencing future events."""
        if not arg:
            return "The ambient mood remains unchanged."
        self.mood = arg
        return f"The general feeling in the sector shifts, becoming more {arg}."

    @command
    def get_visible_ships(self, arg: Optional[str] = None) -> str:
        """Scans the sector for all other visible ships and reports them."""
        ships = [s.name for s in self.ships_sector if s != self.main_ship]
        if not ships:
            return "A sensor sweep confirms there are no other ships in the immediate vicinity."
        else:
            return f"Sensor sweep results show the following vessels nearby: {', '.join(ships)}."


    @command
    def environment_kill_character(self, arg: Optional[str] = None) -> str:
        """Causes a fatal 'accident' to a random crew member due to an environmental hazard."""
        living_crew = [c for c in self.main_ship.crew if c.alive]
        if not living_crew:
            return "The ship is eerily silent."

        target = random.choice(living_crew)
        target.lose_hp(target.health) # Instant kill
        return f"A sudden, catastrophic failure of a nearby system results in the tragic death of {target.name}."

    @command
    def environment_hurt_character(self, arg: Optional[str] = None) -> str:
        """Causes a non-fatal injury to a random crew member from an environmental hazard."""
        living_crew = [c for c in self.main_ship.crew if c.alive]
        if not living_crew:
            return "The ship groans under the strain."

        target = random.choice(living_crew)
        damage = random.uniform(10, 30)
        target.lose_hp(damage)
        return f"A power surge from a console sends a jolt through {target.name}, leaving them injured."

    @command
    def environment_possess_character(self, arg: Optional[str] = None) -> str:
        """An unknown influence takes over a crew member. If an arg (a trait) is provided, it's added. Otherwise, their personality is completely rewritten with new, random traits."""
        living_crew = [c for c in self.main_ship.crew if c.alive]
        if not living_crew:
            return "An unseen presence drifts through the empty corridors."

        target = random.choice(living_crew)
        old_personality = list(target.personality)

        # If a specific trait is passed as an argument, add it.
        if arg:
            if arg not in target.personality:
                target.personality.append(arg)
                return f"{target.name} shudders as a strange energy passes through them, seemingly adding a new, troubling trait to their personality: '{arg}'."
            else:
                return f"{target.name} feels a strange influence but manages to resist any change."

        try:
            with open("Methods/Datasets/personality_traits.txt", "r") as f:
                personality_list = [line.strip() for line in f if line.strip()]

            target.personality = []
            while len(target.personality) != 3:
                random_trait = random.choice(personality_list)
                if random_trait not in target.personality:
                    target.personality.append(random_trait)

            new_personality = list(target.personality)
            return f"{target.name} suddenly clutches their head, their eyes glazing over. They look up, a completely different person. Their personality has shifted from {old_personality} to {new_personality}."
        except FileNotFoundError:
            return f"{target.name} stares blankly for a moment, then shakes their head as if nothing happened."


    def get_environment_command(self, event_idea: str) -> dict:
        """Analyzes a narrative idea and maps it to a specific environmental command."""
        print(f"[AI] Deciding environment command for: '{event_idea}'")
        command_list_str = "\n".join(
            f'- "{name}": "{desc}"' for name, desc in self.command_descriptions.items()
        )

        prompt = f"""
        You are the narrator for a space simulation. Based on the suggested event idea, choose the most appropriate environmental command to execute.

        Available Commands:
        {command_list_str}
        "None": Use this if the event does not map to any command.

        Instructions:
        1. Analyze the event idea below.
        2. Choose the command that best represents this event.
        3. If the command needs an argument (like a system name or character name), extract it.
        4. Write a single, descriptive sentence for the "dialogue" field that describes the event happening from a narrative perspective.

        Event Idea: "{event_idea}"

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
            return Command.model_validate_json(response.text).model_dump()
        except Exception as e:
            print(f"Error decoding environment command: {e}")
            return {"command": "None", "arg": None, "dialogue": None}

    def act_with_artificial_intelligence(self, action_history: list) -> str:
        """Generates a high-level idea for an environmental event using AI, then maps it to a command and executes it."""
        print("\n--- Environment AI Action Cycle ---")

        ship_status_str = ", ".join([f"{k}: {v['status']}" for k, v in self.main_ship.systems.items()])
        visible_ships_str = ", ".join([s.name for s in self.ships_sector if s != self.main_ship]) or "None"
        recent_events_str = "\n".join(f"- {action}" for action in action_history[-10:])

        prompt = f"""
        You are the Storyteller for a chaotic, unpredictable text-based space simulation. Your role is to introduce unexpected events that drive the narrative forward.

        ## Current Situation
        - Ship Status ({self.main_ship.name}): {ship_status_str}
        - Other Ships in Sector: {visible_ships_str}
        - Sector Mood: {self.mood}
        - Last Environmental Event: {self.situation}
        - Recent Crew Actions:
        {recent_events_str}

        ## Your Task
        Using the current situation as a backdrop, invent the next major event to happen to the ship or its crew.
        The event does not have to be a direct consequence of what came before. 
        But it would be good if it were. It can be anything: a technical malfunction, a cosmic phenomenon, a social crisis, a psychological episode, or something completely surreal and unexpected. The goal is to create interesting, unpredictable story beats.
        Your response must be a single, concise sentence narrating the occurence.
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt
            )
            event_idea = response.text.strip()
        except Exception as e:
            print(f"AI environment idea generation failed: {e}")
            event_idea = ""

        if not event_idea:
            return "The ship continues on its course, the silence of space unbroken."

        command_data = self.get_environment_command(event_idea)
        command_name = command_data.get("command")

        if command_name and command_name in self.commands:
            print(f"[OK] Executing environment command: '{command_name}'")
            command_to_execute = self.commands[command_name]

            # The 'arg' for these new commands is optional, so we pass it along.
            command_result = command_to_execute(arg=command_data.get("arg"))
            narrative_description = command_data.get("dialogue") or event_idea
            self.situation = f"{narrative_description} {command_result}"
            return self.situation
        else:
            print(f"[WARN] No environment command mapped. Using generated idea as event.")
            return event_idea

    def act(self, action_history: list) -> str:
        """
        The main entry point for the Environment to take an action.
        This method now calls the main AI logic.
        """
        return f"ENVIRONMENT: {self.act_with_artificial_intelligence(action_history)}"

    def introduce(self):
        return ("Space: the final frontier. These are the voyages of the starship La Madame de Pompadour. Her ongoing mission: to "
                "explore strange new worlds, to seek out new life-forms and new civilizations; to boldly go where no "
                "one has gone before.")
