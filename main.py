import asyncio
import io
import json
import os
import random
import sys
from uuid import UUID

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

app = Flask(__name__)

CORS(app, resources={r"/action": {"origins": "http://localhost:5173"},
                     "/text_to_speech": {"origins": "http://localhost:5173"},
                     "/get_actors": {"origins": "http://localhost:5173"},
                     "/get_personality": {"origins": "http://localhost:5173"}})
dotenv.load_dotenv(dotenv.find_dotenv())

client = OpenAI()

actor_manager: ActorManager = ActorManager()
# In order to make the simulation, we need to populate
# Our manager with NPCS
actor_manager.populate(3)
action_history: deque = deque(maxlen=100)


def perform_random_act():
    act_of_random: str = actor_manager.act_randomnly(action_history=list(action_history))
    action_history.append(act_of_random)
    return jsonify(body=act_of_random, status=200)


@app.route('/action')
def interactions():
    try:
        return perform_random_act()
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500


@app.route('/text_to_speech', methods=['POST'])
def text_to_speech(translate: bool = False):

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
    try:
        return actor_manager.get_actor_list()
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

@app.route('/get_personality', methods=['POST'])
def get_personality_traits():
    data = request.get_json()
    if not data:
        return jsonify(error="Invalid request"), 400

    id_number = data.get('id_number')
    if not id_number:
        return jsonify(error="Missing id_number"), 400

    personality = actor_manager.get_actor_by_id(UUID(id_number)).personality
    return jsonify(personality)


if __name__ == '__main__':
    app.run(debug=True)
