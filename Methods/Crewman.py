import random

from google import genai

from .Humanoid import Humanoid
from .Inventory import Inventory

class Crewman(Humanoid):
    """
    Represents a jaded and resourceful character drifting through space.
    Their actions are often cynical and focused on self-preservation,
    shaped by the harsh realities of the void.
    """
    def __init__(self, name, net_worth, age):
        super().__init__(f"Crewman {name}", age, net_worth)

    def jettison_cargo(self) -> None:
        """Empties the entire inventory into the void of space."""
        self.inventory.empty()
        print(f"{self.name} opens the airlock and jettisons all their goods and objects. 'Less weight, less problems,' they mutter.")

    def acquire_item(self, item: str):
        """Acquires a new item, viewing it with cynical pragmatism."""
        print(f"{self.name} acquires a '{item}'. They give it a cursory glance before stowing it away.")
        self.inventory.add(item)

    def remove_item(self, item: str):
        """Removes a specific item from the inventory."""
        self.inventory.remove(item)

    def get_inventory(self) -> Inventory:
        """Returns the character's inventory."""
        return self.inventory

    def idle_action(self) -> str:
        """Pulls a random, mundane space-themed action from a file."""
        # Note: You must create this file with space-themed actions.
        with open("Methods/Datasets/crewman_actions.txt", "r") as f:
            action_list = [line.strip() for line in f if line.strip()]
        return random.choice(action_list)

    def against_another_neutral(self) -> str:
        """Pulls a random neutral action targeting another character."""
        # Note: You must create this file with space-themed target actions.
        with open("Methods/Datasets/crewman_target_actions_neutral.txt", "r") as f:
            action_list = [line.strip() for line in f if line.strip()]
        return random.choice(action_list)

    def act(self, actors_around: list, action_history: list) -> str | None:
        """
        Decides the next action, choosing between a simple action,
        an action against another, or a more complex, AI-driven action.
        """
        options = ["to_oneself", "against_another", "intelligently"]
        choice = random.choice(options)

        # Ensure actors_around isn't empty for "against_another"
        if choice == "against_another" and not actors_around:
            choice = "to_oneself" # Fallback if no one is around

        match choice:
            case "to_oneself":
                return f"{self.name} {self.idle_action()}."
            case "against_another":
                target = random.choice(actors_around)
                return f"{self.name} {self.against_another_neutral()} {target.name}."
            case "intelligently":
                print("--- Engaging AI for intelligent action generation. ---")
                return self.act_with_artificial_intelligence(
                    actors_around=actors_around, action_history=action_history
                )

    def act_with_artificial_intelligence(self, actors_around: list, action_history: list) -> str:
        """
        Uses a generative AI to determine the next action based on personality and recent events.
        """
        my_recent_actions = []
        other_recent_actions = []

        # Analyze the last 5 events in the action history
        for action in action_history[-5:]:
            if action.startswith(self.name):
                my_recent_actions.append(action)
            else:
                other_recent_actions.append(action)

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

        ## Current Situation
        - **Crewmembers nearby:** {entities_nearby}
        - **Your recent actions (what you did):**
        {my_actions_str}
        - **Other recent events (what happened around you):**
        {other_actions_str}

        ## Your Task
        Based on the events listed above and your role as a standard crewman, what do you do next? 
        Your action should be something a typical person in your position might do. It could be related to a simple ship duty, a mundane reaction to a crewmate, or a personal act while moving through the ship.
        
        The response must be a single, complete sentence in the third person describing your character's action. Do not add any extra explanation.

        Write the complete sentence for {self.name}'s next action now.
        """
        client = genai.Client()
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash", contents=prompt
            )
            ai_action_sentence = response.text.strip()
            return ai_action_sentence

        except Exception as e:
            print(f"AI action failed: {e}. Falling back to default idle action.")
            return f"{self.name} {self.idle_action()}."

