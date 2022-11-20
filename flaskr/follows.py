
from flask import (
    Blueprint, session, request
)

from flaskr.db import get_db, Follow, User
from flaskr.auth import login_required

bp = Blueprint('follow', __name__, url_prefix='/follow')


@bp.route("/<username>", methods=["POST", "DELETE"])
@login_required
def follow(username):
    from flaskr.users import user_index
    db = get_db()
    current_id = session["user_id"]
    target_id = user_index[username].id
    if request.method == "POST":
        try:
            new_follow = Follow(
                follower_id=current_id,
                followed_id=target_id,
            )
            db.session.add(new_follow)
            db.session.commit()
        except db.IntergrityErrro:
            return "error while trying to follow", 402
        else:
            return "Success", 200
    else:   # request.method == "DELETE"
        try:
            unfollow = db.session.query(Follow)\
                .filter(Follow.follower_id == current_id, Follow.followed_id == target_id)\
                .first()
            db.session.delete(unfollow)
            db.session.commit()
        except Exception:
            return "error while trying to unfollow", 402
        else:
            return "Success", 200


def is_following(username):
    from flaskr.users import user_index
    db = get_db()
    current_id = session["user_id"]
    target_id = user_index[username].id
    follow_status = db.session.query(Follow)\
        .filter(Follow.follower_id == current_id, Follow.followed_id == target_id)\
        .first()
    return follow_status is None


def get_followers(username):
    from flaskr.users import user_index
    db = get_db()
    target_id = user_index[username].id
    followers = db.session.query(User)\
        .join(Follow, Follow.follower_id == User.id)\
        .filter(Follow.followed_id == target_id)\
        .all()
    print(followers)
    return followers


def get_followed(username):
    from flaskr.users import user_index
    db = get_db()
    target_id = user_index[username].id
    followed = db.session.query(User) \
        .join(Follow, Follow.followed_id == User.id) \
        .filter(Follow.follower_id == target_id) \
        .all()
    print(followed)
    return followed
