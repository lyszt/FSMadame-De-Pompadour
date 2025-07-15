import json
import typing

from Methods.Poor import Poor
# Essentials
from flask import Flask, render_template, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/action": {"origins": "http://localhost:5173"}})

def performSimulation():
    Robson: Poor = Poor(name='Robson', age=50, net_worth=0)
    return jsonify(body = Robson.act(), status=200)

@app.route('/action')
def interactions():
    return performSimulation()


if __name__ == '__main__':
    app.run(debug=True)