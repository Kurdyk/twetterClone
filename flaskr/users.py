import functools

from flask import (
    Blueprint, g, jsonify
)
from flaskr.db import User, get_db

bp = Blueprint('users', __name__, url_prefix='/users')


@bp.route("/", methods=["GET"])
def get_all_users_descending():
    db = get_db()
    users = db.session.query(User).order_by(User.id).all()

    return jsonify(json_list=[user.serialize for user in users]), 200
