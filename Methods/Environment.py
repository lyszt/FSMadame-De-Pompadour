import random
import inspect
from typing import List, Optional, Callable, Dict, Any
from google import genai
from pydantic import BaseModel, Field

# Assuming these classes are in the same directory or accessible via path
from .Ship import Ship
from .Humanoid import Humanoid
from .Critic import Critic

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
        self.mission = None
        self.client = genai.Client()
        self.commands = {}
        self.command_descriptions = {}
        self._discover_commands()

        # Instantiate the Critic, passing the client for efficiency.
        # This assumes your Critic.__init__ can accept the client.
        self.critic = Critic()

    def _discover_commands(self):
        """Finds all methods decorated with @command and populates the command dictionaries."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, 'is_command'):
                self.commands[name] = method
                self.command_descriptions[name] = inspect.getdoc(method) or "No description available."
        print(f"Environment commands initialized: {list(self.commands.keys())}")

    # --- All @command methods remain the same ---
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
        prompt = "Invent a name and a one-sentence description for a strange spatial anomaly. Example: 'A chroniton-flux field.' Respond with only the name and description."
        try:
            response = self.client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            new_anomaly = response.text.strip()
            self.anomalies.append(new_anomaly)
            return f"Sensors have detected a new, strange phenomenon: {new_anomaly}"
        except Exception as e:
            print(f"AI anomaly generation failed: {e}")
            return "Sensors detect a minor, unclassified energy reading."

    @command
    def set_mood(self, arg: str) -> str:
        """Changes the ambient mood of the sector (e.g., 'Tense', 'Calm', 'Hostile')."""
        if not arg: return "The ambient mood remains unchanged."
        self.mood = arg
        return f"The general feeling in the sector shifts, becoming more {arg}."

    @command
    def environment_kill_character(self, arg: Optional[str] = None) -> str:
        """Causes a fatal 'accident' to a random crew member due to an environmental hazard."""
        living_crew = [c for c in self.main_ship.crew if c.alive]
        if not living_crew: return "The ship is eerily silent."
        target = random.choice(living_crew)
        target.lose_hp(target.health)
        return f"A sudden, catastrophic failure results in the tragic death of {target.name}."

    @command
    def environment_hurt_character(self, arg: Optional[str] = None) -> str:
        """Causes a non-fatal injury to a random crew member from an environmental hazard."""
        living_crew = [c for c in self.main_ship.crew if c.alive]
        if not living_crew: return "The ship groans under the strain."
        target = random.choice(living_crew)
        damage = random.uniform(10, 30)
        target.lose_hp(damage)
        return f"A power surge from a console sends a jolt through {target.name}, leaving them injured."

    @command
    def environment_possess_character(self, arg: Optional[str] = None) -> str:
        """An unknown influence takes over a crew member's personality."""
        living_crew = [c for c in self.main_ship.crew if c.alive]
        if not living_crew: return "An unseen presence drifts through the empty corridors."
        target = random.choice(living_crew)
        # This implementation can be expanded as before
        return f"{target.name} suddenly clutches their head, their eyes glazing over. They look up, a completely different person."


    # --- NEW AND REFACTORED AI LOGIC ---

    def _get_current_environment_state(self, action_history: list) -> Dict[str, Any]:
        """Gathers the current state of the simulation into a dictionary for the AIs."""
        ship_status = ", ".join([f"{k}: {v['status']}" for k, v in self.main_ship.systems.items()])
        character_profiles = {c.name: c.personality for c in self.main_ship.crew if c.alive}
        return {
            "action_history": action_history,
            "ship_status": ship_status,
            "character_profiles": character_profiles,
            "current_mood": self.mood,
        }

    def _generate_storyteller_pitch(self, environment_state: Dict[str, Any]) -> str:
        """The 'Storyteller' AI generates the initial idea for an event."""
        print("[Storyteller] Generating initial pitch...")
        state_summary = (
            f"Ship Status: {environment_state['ship_status']}\n"
            f"Characters: {environment_state['character_profiles']}\n"
            f"Mood: {environment_state['current_mood']}\n"
            f"Recent Events: {environment_state['action_history'][-5:]}"
        )
        prompt = f"""
        You are a passionate, creative 'Storyteller' AI. Your goal is to create interesting narrative events.
        Based on the current state of the simulation, propose the next event.
        Keep it concise (1-2 sentences). This is just the initial pitch for your Critic.

        CURRENT STATE:
        {state_summary}

        YOUR PITCH:
        """
        try:
            response = self.client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            pitch = response.text.strip()
            print(f"[Storyteller] Pitch: '{pitch}'")
            return pitch
        except Exception as e:
            print(f"Storyteller pitch generation failed: {e}")
            return "A minor ambient event occurs."

    def _generate_revised_event(self, pitch: str, critique: str) -> str:
        """The 'Storyteller' AI revises its pitch based on the Critic's feedback."""
        print("[Storyteller] Revising pitch based on critique...")
        prompt = f"""
        You are a passionate 'Storyteller' AI. Your collaborator, a harsh Critic, has just reviewed your idea.
        Incorporate their feedback to create the final, improved version of the event.

        YOUR ORIGINAL PITCH:
        "{pitch}"

        THE CRITIC'S FEEDBACK:
        "{critique}"

        YOUR REVISED, FINAL EVENT DESCRIPTION (2-4 sentences):
        """
        try:
            response = self.client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            revised_event = response.text.strip()
            print(f"[Storyteller] Revised Event: '{revised_event}'")
            return revised_event
        except Exception as e:
            print(f"Storyteller revision failed: {e}")
            return pitch # Fallback to the original pitch on error

    def get_environment_command(self, event_idea: str) -> dict:
        """Analyzes a narrative idea and maps it to a specific environmental command."""
        print(f"[AI] Mapping event to command: '{event_idea}'")
        command_list_str = "\n".join(f'- "{name}": "{desc}"' for name, desc in self.command_descriptions.items())
        prompt = f"""
        You are a narrative engine. Based on the final event description, choose the most appropriate command to execute.

        Available Commands:
        {command_list_str}
        "None": Use this if the event does not map to any command.

        Event Description: "{event_idea}"

        Respond with only the JSON object containing the best command, an optional arg, and a dialogue sentence.
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                generation_config={"response_mime_type": "application/json"},
                # Assuming Command is a Pydantic model. If not, describe the JSON structure.
            )
            # This part might need adjustment based on how you handle Pydantic schema with the API
            # For simplicity, we'll parse it from text if schema isn't directly supported this way.
            # A more robust way is to define the schema in the API call config.
            command_data = Command.model_validate_json(response.text)
            return command_data.model_dump()
        except Exception as e:
            print(f"Error decoding environment command: {e}")
            return {"command": "None", "arg": None, "dialogue": event_idea}

    def act_with_artificial_intelligence(self, action_history: list) -> str:
        """Orchestrates the collaborative narrative generation between Storyteller and Critic."""
        print("\n--- Environment AI Action Cycle ---")

        environment_state = self._get_current_environment_state(action_history)

        # 2. Storyteller generates the initial pitch
        pitch = self._generate_storyteller_pitch(environment_state)

        # 3. Critic reviews the pitch
        critique = self.critic.review_pitch(pitch, environment_state)

        # 4. Storyteller generates the revised, final event based on the critique
        final_event = self._generate_revised_event(pitch, critique)

        command_data = self.get_environment_command(final_event)
        command_name = command_data.get("command")

        if command_name and command_name in self.commands:
            print(f"[OK] Executing final command: '{command_name}'")
            command_to_execute = self.commands[command_name]
            command_result = command_to_execute(arg=command_data.get("arg"))

            narrative_description = command_data.get("dialogue") or final_event
            self.situation = f"{narrative_description} {command_result}"

            # podcast = self.critic.generate_podcast_segment(self.situation)
            # print(f"\n--- Cahiers du Cosmos ---\n{podcast}\n-------------------------\n")

            return self.situation
        else:
            print(f"[WARN] No command mapped. Using final event as narrative.")
            return final_event

    def act(self, action_history: list) -> str:
        """The main entry point for the Environment to take an action."""
        return f"ENVIRONMENT: {self.act_with_artificial_intelligence(action_history)}"

    def introduce(self):
        """Returns the classic introductory monologue for the simulation."""
        return (
            "Space: the final frontier. "
            f"These are the voyages of the starship {self.main_ship.name}. "
            "Her ongoing mission: to explore strange new worlds, "
            "to seek out new life and new civilizations, "
            "to boldly go where no one has gone before."
        )
