
from flask import (
    Blueprint, g, jsonify, render_template
)

from flaskr.db import Tweet, get_db, User

bp = Blueprint('tweets', __name__, url_prefix='/tweets')

index = dict()  # used to store word -> tweet relationship


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


@bp.route("/<word>", methods=["GET"])
def search_for_word(word):
    db = get_db()
    authors = list()
    tweets = list()
    word = word.lower()
    try:
        all_ids = index[word]
    except KeyError:
        return render_template('tweets/all_tweets.html', tweets_authors=zip(tweets, authors))  # Empty page
    for tweet_id in all_ids:
        tweets += db.session.query(Tweet).order_by(Tweet.id.desc()).filter(Tweet.id == tweet_id).all()
    for tweet in tweets:
        authors.append(db.session.query(User.username).filter(tweet.uid == User.id).all()[0][0])
    return render_template('tweets/all_tweets.html', tweets_authors=zip(tweets, authors))


def init_index():
    """
    Initialize the tweet index at serveur launch
    """
    tweets = get_db().session.query(Tweet).order_by(Tweet.id.desc()).all()
    for tweet in tweets:
        content = tweet.content + " " + tweet.title
        for word in content.split(" "):
            if word.isalnum():  # so we can search for number too if we want
                word = word.lower()
                try:
                    index[word].append(tweet.id)
                except KeyError:
                    index[word] = [tweet.id]
    return None
