import random
from google import genai

from .Humanoid import Humanoid
from .Inventory import Inventory

class Poor(Humanoid):
    def __init__(self, name, net_worth, age):
        super().__init__(name, age, net_worth)


    def eat_possessions(self) -> None:
        self.inventory.empty()
        print(f"{self.name} comeu suas possessões! Que delicia!")

    def receive_alms(self, item):
        print(f"{self.name} recebeu um {item} como esmola. 'Muito obrigado!' - Disse {self.name}")
        self.inventory.add(item)

    def remove_possession(self, item):
        self.inventory.remove(item)

    def get_inventory(self) -> Inventory:
        return self.inventory

    def idle_action(self):
        with open("Methods/Datasets/poor_actions.txt", "r") as f:
            name_list = [line.strip() for line in f if line.strip()]
        return random.choice(name_list)

    def against_another_neutral(self):
        with open("Methods/Datasets/poor_target_actions_neutral.txt", "r") as f:
            name_list = [line.strip() for line in f if line.strip()]
        return random.choice(name_list)

    def act(self, actors_around: list, action_history: list):
        options = ["to_oneself", "against_another", "intelligently"]
        choice = random.choice(options)
        match choice:
            case "to_oneself":
                return f"{self.name} {self.idle_action()}."
            case "against_another":
                return f"{self.name} {self.against_another_neutral()} {random.choice(actors_around)}."
            case "intelligently":
                print("Generating intelligent action.")
                return self.act_with_artificial_intelligence(actors_around=actors_around, action_history=action_history)

    def act_with_artificial_intelligence(self, actors_around: list, action_history: list):
        client = genai.Client()
        my_recent_actions = []
        other_recent_actions = []

        # Separate the global history into "mine" and "others"
        for action in action_history[-5:]: # Look at the last 5 overall actions
            if action.startswith(self.name):
                my_recent_actions.append(action)
            else:
                other_recent_actions.append(action)

        # Format the lists for the prompt
        my_actions_str = "\n".join(f"- {action}" for action in my_recent_actions) if my_recent_actions else "None"
        other_actions_str = "\n".join(f"- {action}" for action in other_recent_actions) if other_recent_actions else "None"

        people_nearby = ', '.join(actor.name for actor in actors_around) if actors_around else 'None'

        prompt = f"""You are a character in a text-based simulation. Your name is {self.name}.
        Your personality is that of a poor, weary, and hopeless person. You are generally distrustful and apathetic.
        
        Here is the current situation:
        - People near you: {people_nearby}
        - Your recent actions (what you did):
        {my_actions_str}
        - Other recent actions (what happened around you):
        {other_actions_str}
        
        Your task is to decide what {self.name} does next.
        You can react to what others did, or continue with your own thoughts. Be creative and let your personality and the situation guide you.
        The response must be a single, complete sentence in the third person.
        
        Write the complete sentence for your new action now.
        """

        try:
            # Legado, desativado em 24 de setembro de 2025
            response = client.models.generate_content(
                model="gemini-1.5-flash-002", contents=prompt
            )
            ai_action_sentence = response.text.strip()
            return ai_action_sentence

        except Exception as e:
            print(f"AI action failed: {e}. Falling back to default action.")
            return f"{self.name} {self.idle_action()}."
