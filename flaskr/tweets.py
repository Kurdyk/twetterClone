from flask import (
    Blueprint, g, jsonify, render_template
)

from flaskr.db import Tweet, get_db, User

bp = Blueprint('tweets', __name__, url_prefix='/tweets')


@bp.route("/all", methods=["GET"])
def get_all_tweets_raw():
    db = get_db()
    tweets = db.session.query(Tweet).order_by(Tweet.id).all()

    return jsonify(json_list=[tweet.serialize for tweet in tweets]), 200


@bp.route("/", methods=["GET"])
def get_all_tweets():
    db = get_db()
    authors = list()
    tweets = db.session.query(Tweet).order_by(Tweet.id.desc()).all()
    for tweet in tweets:
        authors.append(db.session.query(User.username).filter(tweet.uid == User.id).all()[0][0])
    return render_template('tweets/all_tweets.html', tweets_authors=zip(tweets, authors))


