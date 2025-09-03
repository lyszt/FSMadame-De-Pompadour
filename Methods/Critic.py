import random
from google import genai
from typing import List, Dict, Any

# We assume these classes exist from your project structure,
# but we don't need to import them to type hint.
# from .Ship import Ship
# from .Humanoid import Humanoid

class Critic:
    """
    An AI agent that acts as a narrative critic, reviewing proposed story events
    from the Environment's Storyteller AI and providing feedback based on its
    personality and the current state of the simulation.
    """
    def __init__(self):
        """
        Initializes the Critic.

        Args:
            personality (str): A description of the critic's personality and artistic tastes.
            client (genai.Client): The initialized client for the AI model.
        """
        with open("Methods/Datasets/personality_traits.txt", "r") as f:
            personality_list = [line.strip() for line in f if line.strip()]
        self.personality = []
        while len(self.personality) != 3:
            random_trait = random.choice(personality_list)
            if random_trait not in self.personality:
                self.personality.append(random_trait)

        self.dialogue_history: List[Dict[str, str]] = []
        self.client = genai.Client()
        print(f"Critic personality: {self.personality}")

    def _add_to_history(self, speaker: str, text: str):
        """Adds an entry to the dialogue history."""
        self.dialogue_history.append({"speaker": speaker, "text": text})
        # Keep the history from getting excessively long
        if len(self.dialogue_history) > 10:
            self.dialogue_history.pop(0)

    def review_pitch(self, pitch: str, environment_state: Dict[str, Any]) -> str:
        """
        Reviews a story pitch from the Storyteller and provides a revision or approval.

        Args:
            pitch (str): The initial event idea from the Storyteller AI.
            environment_state (Dict[str, Any]): A snapshot of the current game state.

        Returns:
            str: The critic's feedback, which could be an approval or a suggested revision.
        """
        print(f"[Critic] Reviewing pitch: '{pitch}'")
        self._add_to_history("Storyteller", pitch)

        # Prepare a condensed string of the environment state for the prompt
        state_summary = f"""
        - Recent Events: {environment_state.get('action_history', [])[-3:]}
        - Character Profiles: {environment_state.get('character_profiles', 'N/A')}
        - Ship Status: {environment_state.get('ship_status', 'N/A')}
        - Current Mood: {environment_state.get('current_mood', 'N/A')}
        """

        prompt = f"""
        You are a narrative critic with a specific personality: "{self.personality}".
        Your collaborator, a passionate but impulsive "Storyteller," has just proposed an idea for the next event in a space simulation.
        Your job is to act as an editor. You must ensure the story is cohesive, thematically resonant, and respects the established characters.

        CONTEXT:
        {state_summary}

        OUR RECENT CONVERSATION:
        {self.dialogue_history}

        THE STORYTELLER'S PITCH:
        "{pitch}"

        YOUR TASK:
        Write your response.
        1. If the pitch is good, approve it but add a small, insightful comment.
        2. If the pitch is weak, random, or betrays character, you MUST reject it and provide a clear, actionable revision. Your revision should tie the event to a specific character's personality or a recent event.
        3. Keep your response concise (2-4 sentences) and in character.
        """


        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            critique = response.text.strip()
        except Exception as e:
            print(f"Critic AI failed to generate review: {e}")
            critique = "Fine. Let's just get on with it."

        self._add_to_history("Critic", critique)
        print(f"[Critic] Response: '{critique}'")
        return critique

    def generate_podcast_segment(self, final_event_summary: str, player_action_summary: str = "") -> str:
        """
        Generates a player-facing 'podcast' segment commenting on a recent event.

        Args:
            final_event_summary (str): A summary of the event that just occurred.
            player_action_summary (str): Optional summary of how the player/characters reacted.

        Returns:
            str: A formatted string representing the podcast dialogue.
        """
        prompt = f"""
        You are a narrative critic with a specific personality: "{self.personality}".
        You co-host a show with a passionate "Storyteller" where you discuss a space simulation you are both directing.
        You have just finished a scene. Based on your recent internal debate and the final outcome, generate a short, in-character podcast segment.

        YOUR INTERNAL DEBATE THAT LED TO THIS SCENE:
        {self.dialogue_history}

        THE FINAL OUTCOME OF THE SCENE:
        {final_event_summary}

        HOW THE "ACTORS" (CHARACTERS/PLAYER) REACTED:
        {player_action_summary or "The consequences are still unfolding."}

        YOUR TASK:
        Write the podcast dialogue. Both you and the Storyteller should speak. Your dialogue should reflect your personality and reference your previous disagreement. Comment on whether the final outcome was a success and how the characters' reactions played out.

        Example Format:
        Storyteller: [Passionate opening statement]
        Critic: [ A phrase according to your personality ]
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"Critic AI failed to generate podcast: {e}")
            return "Storyteller: Well... that was certainly something.\nCritic: Indeed. The less said, the better."
