import functools

import sqlalchemy.orm.exc
from flask import (
    Blueprint, g, jsonify, request, render_template, session, redirect, url_for
)
from sqlalchemy import or_

from flaskr.db import User, get_db, Tweet, Follow, Like
from flaskr.auth import login_required
from flaskr.follows import is_following, get_followed, get_followers, follow_graph
from flaskr.tweets import delete_from_index


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
    tweets = db.session.query(Tweet).order_by(Tweet.id.desc()).filter(Tweet.uid == user.id).all()
    own_profile = session['user_id'] == user.id
    already_follows = is_following(username)
    followers = get_followers(username)
    followed = get_followed(username)
    recommandation = follow_graph.recommandation(session["user_id"], 5)
    return render_template('users/profile.html', user=user, tweets=tweets,
                           own_profile=own_profile, already_follows=already_follows,
                           followed=followed, followers=followers, nb_followers=len(followers),
                           recommandation=recommandation)


@bp.route("/delete", methods=["DELETE"])
@login_required
def delete_user():
    user_id = int(request.data)
    db = get_db()
    try:
        user = db.session.query(User).filter(User.id == user_id).first()
        likes = db.session.query(Like).filter(Like.user_id == user_id).all()    # user likes
        for like in likes:
            db.session.delete(like)
        tweets = db.session.query(Tweet).filter(Tweet.uid == user_id).all()
        for tweet in tweets:
            likes_on_tweet = db.session.query(Like).filter(Like.tweet_id == tweet.id).all()     # likes received
            for like in likes_on_tweet:
                db.session.delete(like)
            db.session.delete(tweet)
        follows = db.session.query(Follow).filter(or_(Follow.follower_id == user_id, Follow.followed_id == user_id)).all()
        for follow in follows:
            db.session.delete(follow)
        db.session.delete(user)
        db.session.commit()
    except Exception as e:
        print(e)
        return "Error while deleting user", 402

    follow_graph.delete_user(user_id)  # delete from follow graph
    for tweet in tweets:  # delete his tweets from index
        delete_from_index(tweet.id)
    return redirect(url_for("tweets.index"))
