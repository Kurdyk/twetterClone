
from flask import (
    Blueprint, g, jsonify, render_template, session, request, redirect, url_for
)
from flaskr.auth import login_required

from flaskr.db import Tweet, get_db, User

bp = Blueprint('tweets', __name__, url_prefix='/tweets')

tweet_index = dict()  # used to store word -> tweet relationship


@bp.route("/all", methods=["GET"])
@login_required
def get_all_tweets_raw():
    db = get_db()
    tweets = db.session.query(Tweet).order_by(Tweet.id).all()

    return jsonify(json_list=[tweet.serialize for tweet in tweets]), 200


@bp.route("/", methods=["GET"])
@login_required
def index():
    db = get_db()
    authors = list()
    tweets = db.session.query(Tweet).order_by(Tweet.id.desc()).all()
    for tweet in tweets:
        authors.append(db.session.query(User.username).filter(
            tweet.uid == User.id).all()[0][0])
    return render_template('tweets/all_tweets.html', tweets_authors=zip(tweets, authors))


@bp.route("/search_word", methods=["GET"])
def search_for_word():
    db = get_db()
    authors = list()
    tweets = list()
    # Do we need to sanitize the input?
    word = request.args.get('search').lower()  # the index is in lower case
    try:
        all_ids = tweet_index[word]
    except KeyError:
        # Empty page
        return render_template('tweets/all_tweets.html', tweets_authors=zip(tweets, authors))
    # removable when we figure out the join to get users and tweets together
    for tweet_id in all_ids:
        tweets += db.session.query(Tweet).order_by(Tweet.id.desc()
                                                   ).filter(Tweet.id == tweet_id).all()
    for tweet in tweets:
        authors.append(db.session.query(User.username).filter(
            tweet.uid == User.id).all()[0][0])
    return render_template('tweets/all_tweets.html', tweets_authors=zip(tweets, authors))


def init_index():
    """
    Initialize the tweet index at serveur launch
    """
    tweets = get_db().session.query(Tweet).order_by(Tweet.id.desc()).all()
    for tweet in tweets:
        update_index(tweet)
    return None


def update_index(tweet: Tweet):
    content = tweet.content + " " + tweet.title
    for word in content.split(" "):
        if word.isalnum():  # so we can search for number too if we want
            word = word.lower()
            try:
                tweet_index[word].add(tweet.id)
            except KeyError:
                tweet_index[word] = {tweet.id}
    return None


@bp.route("/new_tweet", methods=["POST"])
@login_required
def add_new_tweet():
    user_id = session["user_id"]
    title = request.form["title"]
    # We need to sanitize the input
    content = request.form["content"]
    db = get_db()

    try:
        new_tweet = Tweet(
            uid=user_id,
            title=title,
            content=content,
        )
        db.session.add(new_tweet)
        db.session.commit()
    except db.IntegrityError:
        return 'DB Integrity Error', 505
    else:
        update_index(new_tweet)
        return redirect(url_for("tweets.index"))
