from flask import Flask
from flask_cors import CORS, cross_origin
from app.controllers import api, download_lidar, route


app = Flask(__name__)
CORS(app)

app.register_blueprint(route.route)
app.register_blueprint(api.api)
app.register_blueprint(download_lidar.download_lidar)
