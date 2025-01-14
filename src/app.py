from fastai import *
from fastai.vision import *
import fastai
import yaml
import sys
from io import BytesIO
from typing import List, Dict, Union, ByteString, Any
import os
import flask
from flask import Flask, abort
import requests
import torch
import json
import PIL
import base64

with open("src/config.yaml", 'r') as stream:
    APP_CONFIG = yaml.full_load(stream)

app = Flask(__name__)


def load_model(path=".", model_name="model.pkl"):
    learn = load_learner(path)
    return learn


def load_image_url(url: str) -> Image:
    response = requests.get(url)
    img = open_image(BytesIO(response.content))
    return img


def load_image_bytes(raw_bytes: ByteString) -> Image:
    img = open_image(BytesIO(raw_bytes))
    return img


def predict(img, n: int = 3) -> Dict[str, Union[str, List]]:
    pred_class, pred_idx, outputs = model.predict(img)
    pred_probs = outputs / sum(outputs)
    pred_probs = pred_probs.tolist()
    predictions = []
    for image_class, output, prob in zip(model.data.classes, outputs.tolist(), pred_probs):
        output = round(output, 1)
        prob = round(prob, 2)
        predictions.append(
            {"class": image_class.replace("_", " "), "output": output, "prob": prob}
        )

    predictions = sorted(predictions, key=lambda x: x["output"], reverse=True)
    predictions = predictions[0:n]
    return {"class": str(pred_class), "predictions": predictions}


@app.route('/api/classify', methods=['POST', 'GET'])
def upload_file():
    if flask.request.method == 'GET':
        url = flask.request.args.get("url")
        if url != None:
            img = load_image_url(url)
            response = requests.get(url)
            bytes = BytesIO(response.content)
    else:
        bytes = flask.request.files['file'].read()
        img = load_image_bytes(bytes)
        bytes = io.BytesIO(bytes)
    global img_pil
    img_pil = PIL.Image.open(bytes)
    img_pil = img_pil.resize((512, 384), PIL.Image.ANTIALIAS)
    imgByteArr = BytesIO()
    img_pil.save(imgByteArr, format='JPEG')
    img = load_image_bytes(imgByteArr.getvalue())
    
    res = predict(img)
    return flask.jsonify(res)


@app.route('/api/classify_base', methods=['POST', 'GET'])
def upload_file_base_SF():
    if flask.request.method == 'GET':
        abort(400)
    req_data = flask.request.json
    if ('base64' not in req_data):
        print("Couldn't extract data from json")
        abort(400)

    base_sixtyfour_data = req_data['base64']
    if (base_sixtyfour_data == None):
        print("Couldn't extract data from json")
        abort(400)
        
    try:
        bytes = io.BytesIO(base64.b64decode(base_sixtyfour_data))
    except:
        print("Couldn't convert base64 to byte stream")
        abort(400)
    
    global img_pil

    try:
        img_pil = PIL.Image.open(bytes)
    except:
        print("Couldn't convert base64 to PIL image")
        abort(400)
    
    img_pil = img_pil.resize((512, 384), PIL.Image.ANTIALIAS)
    imgByteArr = BytesIO()
    img_pil.save(imgByteArr, format='JPEG')
    img = load_image_bytes(imgByteArr.getvalue())
    
    res = predict(img)
    return flask.jsonify(res)
    


@app.route('/api/classes', methods=['GET'])
def classes():
    classes = sorted(model.data.classes)
    return flask.jsonify(classes)


@app.route('/ping', methods=['GET'])
def ping():
    return "pong"


@app.route('/config')
def config():
    return flask.jsonify(APP_CONFIG)


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"

    response.cache_control.max_age = 0
    return response


@app.route('/<path:path>')
def static_file(path):
    if ".js" in path or ".css" in path:
        return app.send_static_file(path)
    else:
        return app.send_static_file('index.html')


@app.route('/')
def root():
    return app.send_static_file('index.html')


def before_request():
    app.jinja_env.cache = {}


model = load_model('models')

if __name__ == '__main__':
    port = os.environ.get('PORT', 5000)

    if "prepare" not in sys.argv:
        app.jinja_env.auto_reload = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        app.run(debug=False, host='0.0.0.0', port=port)
        # app.run(host='0.0.0.0', port=port)
