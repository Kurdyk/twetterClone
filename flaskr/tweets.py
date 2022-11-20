
from flask import (
    Blueprint, g, jsonify, render_template, session, request, redirect, url_for
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


@bp.route("/", methods=["GET"])
@login_required
def index():
    db = get_db()
    authors = list()
    likes = dict()
    tweets = db.session.query(Tweet).order_by(Tweet.id.desc()).all()
    likedTweets = db.session.query(Like).filter(
        Like.user_id == session["user_id"]).all()

    print("Liked tweets: " + str(likedTweets))

    for tweet in tweets:
        authors.append(db.session.query(User.username).filter(
            tweet.uid == User.id).all()[0][0])
    for like in likedTweets:
        likes[like.tweet_id] = like

    return render_template('tweets/all_tweets.html', tweets_authors=zip(tweets, authors), liked_tweets=likes)


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
