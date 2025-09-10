# ActorManager.py
import uuid
from multiprocessing import Queue, Process
from pathlib import Path
from flask import jsonify
import random

from Methods.System.Ship.Ship import Ship
from .Captain import Captain
from .Environment import Environment
from .Crewman import Crewman
from .Doctor import Doctor
from .Lieutenant import Lieutenant
from .NameGenerator import NameGenerator
from .Humanoid import Humanoid
import traceback
from gpt4all import GPT4All

def llm_worker(request_q: "Queue", response_q: "Queue", model_path: str, model_name: str):
    # Load model once
    model = GPT4All(model_name=model_name, model_path=model_path, verbose=True)
    print("Worker: Model loaded.", flush=True)

    while True:
        job = request_q.get()
        if job is None:
            break

        try:
            job_id, prompt = job
            output_parts = []

            # Preferred: streaming generator
            try:
                gen = model.generate(prompt, max_tokens=256, streaming=True)
                # gen should be an iterator that yields token strings
                for token in gen:
                    if isinstance(token, bytes):
                        token = token.decode("utf-8", errors="ignore")
                    print(token, end="", flush=True)
                    output_parts.append(token)
                print("", flush=True)  # newline after done
            except TypeError:
                # Fallback: use callback to receive tokens
                def _cb(token_id: int, response: str) -> bool:
                    # response is a chunk/token
                    print(response, end="", flush=True)
                    output_parts.append(response)
                    return True  # return False to stop generation early

                # This call will fill output_parts via callback and also return full_response
                full = model.generate(prompt, max_tokens=512, callback=_cb)
                # model.generate may also return the whole response (sometimes)
                if isinstance(full, (bytes, bytearray)):
                    full = full.decode("utf-8", errors="ignore")
                if full:
                    # If callback already printed tokens, this may duplicate;
                    # append only if not duplicate or if callback wasn't used.
                    if not output_parts or "".join(output_parts).strip() != str(full).strip():
                        print(full, flush=True)
                        output_parts.append(str(full))

            response_q.put((job_id, "".join(output_parts)))
        except Exception as e:
            tb = traceback.format_exc()
            print("[Worker] Exception during generation:", tb, flush=True)
            response_q.put((job_id, f"ERROR: {e}\n{tb}"))


class ActorManager:
    def __init__(self):
        self.actors = {}
        self.ship = Ship(crew=list(self.actors.values()), name="La Madame de Pompadour", accuracy=0.5)
        # queues for async requests
        self.request_q = Queue()
        self.response_q = Queue()

        try:
            home_directory = Path.home()
            model_folder = home_directory / "llm_models"
            print("Starting background LLM worker...")

            self.worker = Process(
                target=llm_worker,
                args=(self.request_q, self.response_q, str(model_folder), "mistral-7b-instruct-v0.1.Q3_K_M.gguf")
            )
            self.worker.daemon = True
            self.worker.start()

        except Exception:
            traceback.print_exc()
            print("Download the preferred model into ~/llm_models before running.")

        self.environment = Environment(main_ship=self.ship, ships_sector=None, actor_manager=self)
        self.captain = None

    def add(self, actor: Humanoid):
        self.actors[actor.id] = actor

    def populate(self, population: int):
        self.captain = Captain(
            name=NameGenerator().generate_name(),
            age=random.randint(0, 110),
            net_worth=random.uniform(0, 1e9),
            ship_command=self.ship,
            environment=self.environment,
            actor_manager=self,
            mini_llm=self.request_q
        )

        for _ in range(population):
            npc = Crewman(
                name=NameGenerator().generate_name(),
                age=random.randint(0, 110),
                net_worth=random.uniform(0, 1e9),
                ship=self.ship,
                environment=self.environment,
                actor_manager=self,
                mini_llm=self.request_q
            )
            self.actors[npc.id] = npc

        # add captain
        self.actors[self.captain.id] = self.captain

        # essential archetypes
        doc = Doctor(
            name=NameGenerator().generate_name(),
            age=random.randint(0, 110),
            net_worth=random.uniform(0, 1e9),
            environment=self.environment,
            actor_manager=self,
            mini_llm=self.request_q
        )
        self.actors[doc.id] = doc

        lieutenant = Lieutenant(
            name=NameGenerator().generate_name(),
            age=random.randint(0, 110),
            net_worth=random.uniform(0, 1e9),
            environment=self.environment,
            ship_command=self.ship,
            actor_manager=self,
            mini_llm=self.request_q
        )
        self.actors[lieutenant.id] = lieutenant

    def get_actor_by_id(self, id: uuid.UUID):
        return self.actors[id]

    def get_actor_list(self):
        serialized = {str(uuid): actor.name for uuid, actor in self.actors.items()}
        return jsonify({
            "body": serialized,
            "status": 200
        })

    def get_random_actor(self) -> Humanoid:
        if not self.actors:
            raise Exception("You must populate the actor manager before getting an actor.")
        return random.choice(list(self.actors.values()))

    def act_randomly(self, action_history) -> str:
        if len(action_history) == 1:
            return self.environment.introduce()
        if len(action_history) > 2 and "Captain" in action_history[-1] and all("ENVIRONMENT" not in action for action in action_history[-5:]):
            return self.environment.act(action_history)
        if not self.actors:
            raise Exception("You must populate the actor manager before making an action.")
        if len(action_history) == 0:
            return self.captain.set_initial_mission(list(self.actors.values()), action_history)
        else:
            if all(self.captain.name not in action for action in action_history[-5:]):
                return self.captain.act(list(self.actors.values()), action_history)
        action = random.choice(list(self.actors.values())).act(list(self.actors.values()), action_history)
        self.actors = {key: actor for key, actor in self.actors.items() if actor.alive}
        return action

    def submit_prompt(self, prompt: str) -> str:
        """Send a prompt to the background worker and get response (blocking)."""
        job_id = str(uuid.uuid4())
        self.request_q.put((job_id, prompt))

        while True:
            resp_id, text = self.response_q.get()
            if resp_id == job_id:
                return text
