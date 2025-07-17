import json
import os
import random
import traceback
import typing

import dotenv

from Methods.Crewman import Crewman
# Essentials
from flask import Flask, render_template, jsonify
from flask_cors import CORS
# Custom Methods
from Methods.NameGenerator import NameGenerator
from Methods.ActorManager import ActorManager
app = Flask(__name__)
CORS(app, resources={r"/action": {"origins": "http://localhost:5173"},
                      "/get_actors": {"origins": "http://localhost:5173"}})

dotenv.load_dotenv(dotenv.find_dotenv())
actor_manager: ActorManager = ActorManager()
# In order to make the simulation, we need to populate
# Our manager with NPCS
actor_manager.populate(10)
action_history: list = []

def perform_random_act():
    act_of_random: str = actor_manager.act_randomnly(action_history=action_history)
    action_history.append(act_of_random)
    return jsonify(body = act_of_random, status=200)

@app.route('/action')
def interactions():
    try:
        return perform_random_act()
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

@app.route('/get_actors')
def get_list_of_crewmembers():
    try:
        return actor_manager.get_actor_list()
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

if __name__ == '__main__':

    app.run(debug=True)