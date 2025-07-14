import typing

from Methods.Poor import Poor
# Essentials
from flask import Flask, render_template


app = Flask(__name__)

def performSimulation():
    Robson: Poor = Poor(name='Robson', age=50, net_worth=0)
    final_html: str = ""
    for i in range(5):
        final_html += f"{Robson.act()} <br>"
    return render_template("index.html", final_html=final_html)

@app.route('/')
def interactions():
    return performSimulation()


if __name__ == '__main__':
    app.run(debug=True)