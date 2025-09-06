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
    unarmed_attack_verb: str = Field(..., description="A short, descriptive verb phrase for how this character attacks unarmed, based on their race and appearance (e.g., 'punches', 'slashes with its talons at', 'slams its metallic fist into').")
    weapon_attack_verb: str = Field(..., description="A short, descriptive verb phrase for how this character attacks with a generic ranged weapon, based on their primary skill (e.g., 'fires a wild shot at', 'coolly takes aim and shoots at', 'unleashes a volley towards').")
    kill_description: str = Field(..., description="A short, flavorful sentence describing how this character delivers a finishing blow, reflecting their personality (e.g., 'ends the fight with brutal efficiency', 'looks away as they deliver the final shot', 'shows a moment of regret before finishing it').")

class Command(BaseModel):
    command: Optional[str] = Field(None, description="The specific command to be executed.")
    arg: Optional[str] = Field(None, description="The argument for the command, if needed (e.g., a target's name or a system name).")
    dialogue: Optional[str] = Field(None, description="A line of dialogue for the character to say.")
    magnitude: Optional[str] = Field(None, description="For actions with variable power (like heal or sabotage), a descriptive level: 'minor', 'moderate', or 'critical'.")

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
            actor_manager,
            net_worth: float = 100.0
    ):
        self.ship = ship
        self.environment = environment
        self.client = genai.Client()

        # Instantiate self concept from prompt
        self._generate_and_apply_sheet(concept)
        super().__init__(self.name, self.age, net_worth, actor_manager)

        self.commands = {}
        self.command_descriptions = {}
        self._discover_commands()

    def _generate_and_apply_sheet(self, concept: str):
        """
        Calls the AI to generate character details from a concept and applies them directly to the instance.
        """
        print(f"Generating new AI character from concept: '{concept}'")

        prompt = f"""
        You are a character creator for a sci-fi RPG. Based on the following high-level concept,
        generate a complete, detailed character profile.

        CONCEPT: "{concept}"

        Based on the character's race, skills, and personality, also generate flavorful text for their actions.
        For example, a character with claws should 'slash with its talons', not 'punch'.
        A character with 'Marksmanship' should 'take a well-aimed shot', not 'fire wildly'.

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
            self.unarmed_attack_verb = sheet_data.unarmed_attack_verb
            self.weapon_attack_verb = sheet_data.weapon_attack_verb
            self.kill_description = sheet_data.kill_description

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
            self.unarmed_attack_verb = "slams its metallic fist into"
            self.weapon_attack_verb = "coolly fires at"
            self.kill_description = "terminates the target with cold efficiency."

    def _discover_commands(self):
        """Finds all methods decorated with @command."""
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, 'is_command'):
                self.commands[name] = method
                self.command_descriptions[name] = inspect.getdoc(method) or "No description available."
        print(f"Commands for {self.name} initialized: {list(self.commands.keys())}")

    # --- "GOD MODE" & SPECIAL COMMANDS ---

    @command
    def heal(self, target_name: str, magnitude: str = 'moderate') -> str:
        """Heals a target (or self) by name. The amount healed is determined by the AI's chosen magnitude."""
        if not target_name:
            return f"{self.name} channels energy, but has no target."

        target = next((actor for actor in self.actor_manager.actors.values() if target_name.lower() in actor.name.lower()), None)

        if not target:
            return f"{self.name} looks for {target_name} but can't find them."
        if not target.alive:
            return f"{self.name} attempts to heal {target_name}, but it's too late."

        healing_map = {
            'minor': random.uniform(10, 25),
            'moderate': random.uniform(30, 60),
            'critical': random.uniform(70, 100)
        }
        healing_amount = healing_map.get(magnitude.lower(), 40) # Default to moderate

        target.health = min(100, target.health + healing_amount)
        return f"{self.name} touches {target_name}, and a wave of {magnitude} energy restores them to {target.health:.0f}% health."

    @command
    def sabotage_ship_system(self, arg: str, magnitude: str = 'moderate') -> str:
        """Inflicts damage on a specific ship system. Damage is determined by the AI's chosen magnitude."""
        system_name = arg.lower().strip() if arg else ""
        if not system_name or system_name not in self.ship.get_systems():
            return f"{self.name} tries to sabotage a system, but can't find the right one."

        damage_map = {
            'minor': random.uniform(10, 25),
            'moderate': random.uniform(30, 50),
            'critical': random.uniform(60, 90)
        }
        damage = damage_map.get(magnitude.lower(), 40) # Default to moderate

        self.ship.apply_damage_to_system(system_name, damage, source=f"internal sabotage by {self.name}")
        return f"Sparks fly as {self.name} deliberately causes {magnitude} sabotage to the {system_name.replace('_', ' ')} system."

    @command
    def reveal_truth(self, target_name: str) -> str:
        """Forces a target character by name to reveal their hidden secret."""
        if not target_name:
            return f"{self.name} probes the air for secrets, but finds nothing."

        target = next((actor for actor in self.actor_manager.actors.values() if target_name.lower() in actor.name.lower()), None)

        if not target:
            return f"{self.name} tries to read the mind of {target_name}, but they are not nearby."

        secret = getattr(target, 'secret', 'a deep secret they have kept hidden until now')
        return f"Under {self.name}'s intense gaze, {target.name} is compelled to speak the truth, revealing that '{secret}'."

    @command
    def punch(self, target_name: str) -> str:
        """Starts a physical altercation. Damage is modified by the 'Strong' core attribute."""
        if not target_name:
            return f"{self.name} swings at the air, looking foolish."

        target = next((actor for actor in self.actor_manager.actors.values() if target_name.lower() in actor.name.lower()), None)

        if not target:
            return f"{self.name} looks around for {target_name} but can't find them."
        if not target.alive:
            return f"{self.name} looks at {target.name}'s body but does nothing."

        damage_modifier = 1.0
        if self.core_attribute.lower() == 'strong':
            damage_modifier = 1.75

        base_damage = random.uniform(5, 12)
        final_damage = base_damage * damage_modifier
        target.lose_hp(final_damage)

        if not target.alive:
            return self.kill_description.format(target_name=target.name)

        return f"{self.name} {self.unarmed_attack_verb} {target.name}."

    @command
    def shoot(self, target_name: str) -> str:
        """Uses a personal weapon. Damage is modified by the 'Marksmanship' primary skill."""
        if not target_name:
            return f"{self.name} draws a weapon but has no one to aim at."

        target = next((actor for actor in self.actor_manager.actors.values() if target_name.lower() in actor.name.lower()), None)

        if not target:
            return f"{self.name} aims their weapon, but can't find {target_name}."
        if not target.alive:
            return f"{self.name} aims their weapon at {target.name}'s body but doesn't fire."

        damage_modifier = 1.0
        if self.primary_skill.lower() == 'marksmanship':
            damage_modifier = 2.0

        base_damage = random.uniform(15, 50)
        final_damage = base_damage * damage_modifier
        target.lose_hp(final_damage)

        if not target.alive:
            return self.kill_description.format(target_name=target.name)
        else:
            return f"{self.name} {self.weapon_attack_verb} {target.name}."

    # --- AI-DRIVEN ACTION METHODS ---
    def get_character_command(self, action_sentence: str, actors_around: List[Humanoid]) -> dict:
        """Analyzes an intended action to map it to a specific command."""
        command_list_str = "\n".join(f'- "{name}": "{desc}"' for name, desc in self.command_descriptions.items())
        entities_nearby = ', '.join(actor.name for actor in actors_around if actor.name != self.name) if actors_around else 'no one else'
        valid_systems = list(self.ship.get_systems().keys())

        prompt = f"""
        You are a command interpreter for a character in a simulation. Based on the character's intended action, choose the most appropriate command.

        Available Commands:
        {command_list_str}
        "None": Use if the action is purely observational, conversational, or internal thought.

        Nearby Characters: {entities_nearby}

        **SPECIAL INSTRUCTIONS:**
        - For `sabotage_ship_system`, the 'arg' MUST be one of these exact system names: {valid_systems}.
        - For `heal` or `sabotage_ship_system`, you MUST also provide a `magnitude` field: 'minor', 'moderate', or 'critical'.
        - If the action targets a character (e.g., 'punch Bob'), the 'arg' must be that character's name.

        Intended Action: "{action_sentence}"
        
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
            return {"command": "None", "arg": None, "dialogue": None}

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
        """Orchestrates the character's turn, including target and magnitude resolution."""
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

            if 'target_name' in sig.parameters:
                kwargs_to_pass['target_name'] = arg_value
            elif 'arg' in sig.parameters:
                kwargs_to_pass['arg'] = arg_value

            if 'magnitude' in sig.parameters:
                kwargs_to_pass['magnitude'] = command_data.get('magnitude', 'moderate')

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

