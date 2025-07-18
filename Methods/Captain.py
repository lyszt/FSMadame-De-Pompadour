import random

from google import genai

from .Humanoid import Humanoid
from .Inventory import Inventory

class Captain(Humanoid):
    """
    Represents the commanding officer of a starship, a figure of authority and strategic thinking.
    Their actions are decisive and reflect their responsibility for the ship and crew.
    """
    def __init__(self, name, net_worth, age):
        super().__init__(f"Captain {name}", age, net_worth)

    def jettison_cargo(self) -> str:
        """Orders the entire inventory to be jettisoned from the vessel."""
        self.inventory.empty()
        return f"Captain {self.name} gives the order to jettison the cargo. 'Make it so,' they say, watching the main viewscreen."

    def acquire_item(self, item: str) -> str:
        """Formally acquires a new item, having it logged and stored."""
        self.inventory.add(item)
        return f"Captain {self.name} is presented with a '{item}'. They inspect it with a critical eye before nodding. 'Log it.'"

    def remove_item(self, item: str):
        """Removes a specific item from the inventory."""
        self.inventory.remove(item)

    def get_inventory(self) -> Inventory:
        """Returns the character's inventory."""
        return self.inventory

    def idle_action(self) -> str:
        """Pulls a random, command-themed action from a file."""
        with open("Methods/Datasets/captain_actions.txt", "r") as f:
            action_list = [line.strip() for line in f if line.strip()]
        return str.lower(random.choice(action_list))

    def against_another_neutral(self) -> str:
        """Pulls a random neutral action targeting another character."""
        with open("Methods/Datasets/captain_target_actions_neutral.txt", "r") as f:
            action_list = [line.strip() for line in f if line.strip()]
        return str.lower(random.choice(action_list))

    def act(self, actors_around: list, action_history: list) -> str | None:
        """
        Decides the next action, choosing between a simple action,
        an action against another, or a more complex, AI-driven action.
        """

        my_recent_actions = []
        others_recent_actions = []

        # Analyze the last 5 events in the action history
        for action in action_history[-5:]:
            if not action.startswith(self.name):
                others_recent_actions.append(action)

        for action in action_history[-self.memory_depth:]:
            if action.startswith(self.name):
                my_recent_actions.append(action)

        if len(my_recent_actions) == 0:
            options = ["to_oneself", "against_another"]
            choice = random.choice(options)
            if choice == "against_another" and not actors_around:
                choice = "to_oneself" # Fallback if no one is around
            match choice:
                case "to_oneself":
                    return f"{self.name} {self.idle_action()}."
                case "against_another":
                    target = random.choice(actors_around)
                    return f"{self.name} {self.against_another_neutral()} {target.name}."

        print("Generating AI response...")
        actions = [my_recent_actions, others_recent_actions]
        return self.act_with_artificial_intelligence(
            actors_around=actors_around, action_history=action_history, actions=actions
        )

    def act_with_artificial_intelligence(self, actors_around: list, action_history: list, actions: list) -> str:
        """
        Uses a generative AI to determine the next action based on personality and recent events.
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
        You are the Captain, the commanding officer of the entire vessel. 
        You wear a distinguished officer's uniform and bear the ultimate responsibility for the ship, its crew, and the success of its mission.
        Your have the responsibility to be decisive, strategic, and reflect your authority. You interact with your bridge officers and command staff.
        To your benefit, or not, your personality traits are: {[trait for trait in self.personality]}
        Based on the events listed above and your role as a proactive Captain, generate your next action. 
        This action must involve direct interaction with another person or the ship's 
        command systems.
         
        It should be a clear, decisive command, a question to an officer, o
        or a direct response to a situation. Avoid passive, silent, or internal actions. 
        The response must be a single, complete sentence in the third person describing your character's interactive action. Do not add any extra explanation.
        Add dialogue using quotes.
        ## Current Situation
        - **Officers/Crew nearby:** {entities_nearby}
        - **Your recent actions (what you did):**
        {my_actions_str}
        - **Other recent events (what happened around you):**
        {other_actions_str}

        ## Your Task
        Based on the events listed above and your role as the Captain, what do you do next? 
        Your action should be something a commanding officer would do. It could be giving an order, reviewing strategic data, addressing a bridge officer, or making a command decision.
        
        The response must be a single, complete sentence in the third person describing your character's action. Do not add any extra explanation.

        Write the complete sentence for {self.name}'s next action now.
        """
        client = genai.Client()
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite", contents=prompt
            )
            ai_action_sentence = response.text.strip()
            return ai_action_sentence

        except Exception as e:
            print(f"AI action failed: {e}. Falling back to default idle action.")
            return f"{self.name} {self.idle_action()}."
