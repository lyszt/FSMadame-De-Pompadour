import asyncio
import io
import json
import os
import random
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
# Custom Methods
from Methods.NameGenerator import NameGenerator
from Methods.ActorManager import ActorManager
app = Flask(__name__)
CORS(app, resources={r"/action": {"origins": "http://localhost:5173"},
                     "/text_to_speech": {"origins": "http://localhost:5173"},
                      "/get_actors": {"origins": "http://localhost:5173"}})
dotenv.load_dotenv(dotenv.find_dotenv())
actor_manager: ActorManager = ActorManager()
# In order to make the simulation, we need to populate
# Our manager with NPCS
actor_manager.populate(5)
action_history: deque = deque(maxlen=100)

def perform_random_act(translate: bool = False):
    act_of_random: str = actor_manager.act_randomnly(action_history=list(action_history))
    # Soon to be added translation feature
    if translate:
        translation = asyncio.run(Translator().translate(act_of_random, "pt"))
        translated_text = translation.text
        action_history.append(translated_text)
        return jsonify(body=translated_text, status=200)
    else:
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
def text_to_speech():
    data = request.get_json()
    text = data.get('text', '')
    if not text:
        return {'error': 'No text provided'}, 400

    tts = gTTS(text=text, lang='en', tld='co.uk')
    audio_bytes = io.BytesIO()
    tts.write_to_fp(audio_bytes)
    audio_bytes.seek(0)

    return send_file(
        audio_bytes,
        mimetype='audio/mpeg',
        as_attachment=False,
        download_name='speech.mp3'
    )

@app.route('/get_actors')
def get_list_of_crewmembers():
    try:
        return actor_manager.get_actor_list()
    except Exception as e:
        traceback.print_exc()
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)