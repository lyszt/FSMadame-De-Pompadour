import asyncio
import io
import json
import os
import random
import sys
from uuid import UUID, uuid4

# Death to windows

if sys.platform == 'win32':
    os.environ["PATH"] += os.pathsep + "C:/ffmpeg/bin"
    from pydub import AudioSegment
    from pydub.utils import which

    AudioSegment.converter = which("ffmpeg") or "C:/ffmpeg/bin/ffmpeg.exe"
import io
import sys
import traceback
import typing
import tempfile
from collections import deque
from gtts import gTTS
import dotenv
from Methods.Crewman import Crewman
# Essentials
from flask import Flask, render_template, jsonify, send_file, request
from flask_cors import CORS
from googletrans import Translator
from openai import OpenAI
# Custom Methods
from Methods.NameGenerator import NameGenerator
from Methods.ActorManager import ActorManager

# Globals
DEBUG_MODE: bool = True

app = Flask(__name__)

CORS(app, resources={r"/action": {"origins": "http://localhost:5173"},
                     "/text_to_speech": {"origins": "http://localhost:5173"},
                     "/get_actors": {"origins": "http://localhost:5173"},
                     "/get_character_details": {"origins": "http://localhost:5173"}})
dotenv.load_dotenv(dotenv.find_dotenv())

client = OpenAI()

# In order to make the simulation, we need to populate
# Our manager with NPCS
if not DEBUG_MODE:
    actor_manager: ActorManager = ActorManager()
    actor_manager.populate(5)
    action_history: deque = deque(maxlen=100)


def perform_random_act():
    act_of_random: str = actor_manager.act_randomly(action_history=list(action_history))
    action_history.append(act_of_random)
    return act_of_random


@app.route('/action')
def interactions():
    if DEBUG_MODE: return {"debug": True, "body":"[PLACEHOLDER]"}, 200
    try:
        if DEBUG_MODE: return {"debug": False, "body":perform_random_act()}, 200
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


@app.route('/text_to_speech', methods=['POST'])
def text_to_speech(translate: bool = False):
    if DEBUG_MODE: return None

    data = request.get_json()
    text = data.get('text', '')
    if translate:
        translation = asyncio.run(Translator().translate(data, "pt"))
        text = translation.text
    if not text:
        return {'error': 'No text provided'}, 400

    filename = "./gen_audio.mp3"

    with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text
    ) as response:
        response.stream_to_file(filename)

    return send_file(
        filename,
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name="output.mp3"
    )

@app.route('/get_actors')
def get_list_of_crewmembers():
    if DEBUG_MODE:
        return jsonify({
            "body": {str(uuid4()): "John Doe" for i in range(10)},
            "status": 200
        })
    try:
        return actor_manager.get_actor_list()
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


@app.route('/get_character_details', methods=['POST'])
def get_character_details():
    if DEBUG_MODE:
        return jsonify({
            "personality": ["Very cool guy"],
            "backstory": "Used to make pizzas",
            "wants": ["Icecream"],
            "fears": ["Icebeam"]
        })

    """
    Fetches all key narrative attributes for a given character ID.
    """
    data = request.get_json()
    if not data:
        return jsonify(error="Invalid request"), 400

    id_number = data.get('id_number')
    if not id_number:
        return jsonify(error="Missing id_number"), 400

    try:
        character = actor_manager.get_actor_by_id(UUID(id_number))

        details = {
            "personality": character.personality,
            "backstory": getattr(character, 'backstory', 'No backstory available.'),
            "wants": getattr(character, 'wants', []),
            "fears": getattr(character, 'fears', [])
        }
        return jsonify(details)

    except (KeyError, AttributeError) as e:
        return jsonify(error=f"Character not found or attribute missing: {e}"), 404
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    if DEBUG_MODE: print("Entering DEBUG Mode for Front End Development.")
    app.run()
