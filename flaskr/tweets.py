
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


@bp.route("search_word/<word>", methods=["GET"])
def search_for_word(word):
    db = get_db()
    authors = list()
    tweets = list()
    word = word.lower()
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
                tweet_index[word].append(tweet.id)
            except KeyError:
                tweet_index[word] = [tweet.id]
    return None


@bp.route("/new_tweet", methods=["GET", "POST"])
@login_required
def add_new_tweet():
    if request.method == "GET":
        return
    # For test purposes
    user_id = session["user_id"]
    print(request.form.to_dict())
    title = request.form["title"]
    content = request.form["content"]
    print(user_id, title, content)
    # Untested because it crashes before
    db = get_db()
    author = db.session.query(User.id).filter(
        User.username == user_id).all()  # might miss some [0][0]
    try:
        new_tweet = Tweet(
            uid=user_id,
            title=title,
            content=content,
        )
        db.session.add(new_tweet)
        db.session.commit()
    except db.IntegrityError:
        print("DB intergrity error")
        return redirect(url_for("tweets.index"))
    else:
        return redirect(url_for("tweets.index"))
