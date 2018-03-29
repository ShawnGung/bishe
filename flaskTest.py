from flask import Flask,jsonify,abort,request
import finalInterface as fI
import json
from flask_cors import *
app = Flask(__name__)

CORS(app, supports_credentials=True)
@app.route('/HelloWorld/')
def hello_world():
    return 'Hello World!'

@app.route('/getCityCenter/',methods=['POST'])
def getCityCenter():
    if not request.json or 'city' not in request.json:
        abort(400)
    cityName = request.json['city']
    center = fI.getCityCenter(cityName)
    centerJson = json.loads(center)
    resp = jsonify({'center':centerJson['center']})
    return resp

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8383,debug=True)
