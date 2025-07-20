from flask import Flask, jsonify
from flask_login import LoginManager

from config import config
from db_sync import db_session
from models import User

app = Flask(__name__)
app.debug = config.DEBUG
app.config.from_object(config)

login_manager = LoginManager(app)
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db_session.get(User, user_id)


@login_manager.unauthorized_handler
def handle_unauthorized():
    return jsonify({"error": "Access denied! Authentication required!"}), 401


@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "URL Not Found"}), 404


from views import *

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
