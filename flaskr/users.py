import functools
import os

from flask import (
    Blueprint, current_app, flash, g, jsonify, redirect, request, render_template, send_from_directory, session, url_for
)
from sqlalchemy import update

from flaskr.db import User, get_db, Tweet
from flaskr.auth import login_required
from flaskr.follows import is_following, get_followed, get_followers, follow_graph
from werkzeug.utils import secure_filename


bp = Blueprint('users', __name__, url_prefix='/users')

user_index = dict()


@bp.route("/", methods=["GET"])
def get_all_users_descending():
    db = get_db()
    users = db.session.query(User).order_by(User.id).all()

    return jsonify(json_list=[user.serialize for user in users]), 200


def update_user_index(user: User):
    user_index[user.username] = user
    return None


def init_user_index():
    """
    Initialize the user index at serveur launch
    """
    users = get_db().session.query(User).order_by(User.id.desc()).all()
    for user in users:
        update_user_index(user)
    return None


@bp.route("/search/<username>", methods=["GET"])
@login_required
def search_for_email(username):
    # Find the user
    # username = request.args.get('search')
    try:
        user = user_index[username]
    except KeyError:
        return "No such user", 402
    # Find his tweets
    db = get_db()
    tweets = db.session.query(Tweet).order_by(
        Tweet.id.desc()).filter(Tweet.uid == user.id).all()
    own_profile = session['user_id'] == user.id
    already_follows = is_following(username)
    followers = get_followers(username)
    followed = get_followed(username)
    follow_graph.print()
    recommandation = follow_graph.recommandation(session["user_id"], 5)
    return render_template('users/profile.html', user=user, tweets=tweets,
                           own_profile=own_profile, already_follows=already_follows,
                           followed=followed, followers=followers, nb_followers=len(
                               followers),
                           recommandation=recommandation)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and \
           get_extension(filename) in ALLOWED_EXTENSIONS


def get_extension(filename):
    return filename.rsplit('.', 1)[1].lower()


@bp.route("/avatar/upload", methods=["POST"])
@login_required
def upload_avatar():
    if request.method == 'POST':
        sent_filename = request.form['filename']
        if len(request.files) == 0:
            return 'Missing file in request', 500
        file = request.files[sent_filename]
        if file.filename == '':
            return 'Missing filename in request', 500
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            newfilename = secure_filename(str(session['user_id']) +
                                          '_avatar.' + get_extension(filename))

            file.save(os.path.join(
                current_app.config['UPLOAD_FOLDER'], newfilename))
            file.close()

            try:
                db = get_db()
                stmt = update(User).where(User.id == session['user_id']).values(
                    avatar=newfilename)
                db.session.execute(stmt)
                db.session.commit()
                user = db.session.query(User).where(
                    User.id == session['user_id']).first()
                update_user_index(user)
                return 'Success', 200
            except Exception as e:
                return 'Error adding avatar to user', 500


@bp.route('/avatar/<path:path>')
def get_user_avatar(path):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], path)
