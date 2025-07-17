import json
import random
import typing

from Methods.Poor import Poor
# Essentials
from flask import Flask, render_template, jsonify
from flask_cors import CORS
# Custom Methods
from Methods.NameGenerator import NameGenerator
from Methods.ActorManager import ActorManager
app = Flask(__name__)
CORS(app, resources={r"/action": {"origins": "http://localhost:5173"}})

actor_manager: ActorManager = ActorManager()
# In order to make the simulation, we need to populate
# Our manager with NPCS
actor_manager.populate(10)

def perform_random_act():
    act_of_random: str = actor_manager.act_randomnly()
    return jsonify(body = act_of_random, status=200)

@app.route('/action')
def interactions():
    try:
        return perform_random_act()
    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == '__main__':

    app.run(debug=True)