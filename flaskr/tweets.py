import os
import openai
from flask import (
    Blueprint, current_app, g, jsonify, render_template, session, request, redirect, url_for
)
from flaskr.auth import login_required

from flaskr.db import Like, Tweet, get_db, User

bp = Blueprint('tweets', __name__, url_prefix='/tweets')

tweet_index = dict()  # used to store word -> tweet relationship


@bp.route("/all", methods=["GET"])
@login_required
def get_all_tweets_raw():
    db = get_db()
    tweets = db.session.query(Tweet).order_by(Tweet.id).all()

    return jsonify(json_list=[tweet.serialize for tweet in tweets]), 200


def map_tweets_to_authors(tweets):
    db = get_db()
    authors = [db.session.query(User).filter(
        tweet.uid == User.id).first() for tweet in tweets]
    return zip(tweets, authors)


@bp.route("/", methods=["GET"])
@login_required
def index():
    db = get_db()
    likes = dict()
    tweets = db.session.query(Tweet).order_by(Tweet.id.desc()).all()
    likedTweets = db.session.query(Like).filter(
        Like.user_id == session["user_id"]).all()

    for like in likedTweets:
        likes[like.tweet_id] = like
    return render_template('tweets/all_tweets.html', tweets_authors=map_tweets_to_authors(tweets), liked_tweets=likes)


@bp.route("/search_word", methods=["GET"])
def search_for_word():
    db = get_db()
    tweets = list()
    # Do we need to sanitize the input?
    word = request.args.get('search').lower()  # the index is in lower case
    try:
        all_ids = tweet_index[word]
    except KeyError:
        # Empty page
        return render_template('tweets/all_tweets.html', tweets_authors=map_tweets_to_authors(tweets))

    for tweet_id in all_ids:
        tweets += db.session.query(Tweet).order_by(Tweet.id.desc()
                                                   ).filter(Tweet.id == tweet_id).all()

    return render_template('tweets/all_tweets.html', tweets_authors=map_tweets_to_authors(tweets))


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


def delete_from_index(tweet_id : int):
    for word in tweet_index:
        try:
            tweet_index[word].remove(tweet_id)
        except KeyError:
            pass
    return


@bp.route("/new_tweet", methods=["POST"])
@login_required
def add_new_tweet():
    user_id = session["user_id"]
    title = request.form["title"]
    # We need to sanitize the input
    content = request.form["content"]

    return postTweet(Tweet(
        uid=user_id,
        title=title,
        content=content,
    ))


@bp.route("/delete", methods=["DELETE"])
@login_required
def delete_tweet():
    tweet_id = int(request.data)
    db = get_db()
    try:  # find and delete the tweet from the DB
        tweet = db.session.query(Tweet).filter(Tweet.id == tweet_id).first()
        db.session.delete(tweet)
        db.session.commit()
    except Exception:
        return "error while trying to delete tweet", 402
    else:   # delete in DB is success: removing from index
        delete_from_index(tweet_id)
    return "Success", 200


@bp.route("/new_tweet/generate", methods=["POST"])
@login_required
def generateTweet():
    user_id = session["user_id"]
    title = request.form["title"]
    content = request.form["content"]

    with open(os.path.join(current_app.instance_path, 'secrets.txt')) as f:
        api_key = f.read()

    openai.api_key = api_key
    response = openai.Completion.create(
        model="text-davinci-002",
        # Change this to change what the prompt does
        prompt="Rewrite this in the style of William Shakespeare:\n\n"+content,
        temperature=0,
        max_tokens=60,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

    return postTweet(Tweet(
        uid=user_id,
        title=title,
        content=response['choices'][0]['text'],
    ))


def postTweet(new_tweet):
    db = get_db()
    try:
        db.session.add(new_tweet)
        db.session.commit()
    except db.IntegrityError:
        return 'DB Integrity Error', 505
    else:
        update_index(new_tweet)
        return redirect(url_for("tweets.index"))


@bp.route("/get", methods=["GET"])
@login_required
def getTweet():
    tweetId = request.args.get('id')
    db = get_db()
    try:
        rows = db.session.query(Tweet, User).join(User).filter(
            Tweet.id == tweetId and User.id == Tweet.uid).first()

        return dict(zip(['tweet', 'user'], [i.serialize for i in rows])), 200
    except Exception as e:
        print(e)
        return 'Unable to find tweet', 404


@bp.route("/like", methods=["POST", "DELETE"])
@login_required
def likeTweet():
    db = get_db()
    tweetId = request.json.get("tweetId")
    userId = session["user_id"]

    if request.method == "POST":
        new_like = Like(tweet_id=tweetId, user_id=userId)
        try:
            db.session.add(new_like)
            db.session.commit()
        except Exception as e:
            print(e)
            return 'Error', 505

    elif request.method == "DELETE":
        try:
            Like.query.filter(
                Like.tweet_id == tweetId and Like.user_id == userId).delete()
            db.session.commit()
        except Exception as e:
            print(e)
            return 'Error', 505

    return 'Success', 200
