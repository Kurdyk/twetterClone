import random

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
            follow_graph.add_follow(current_id, target_id)
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
            follow_graph.remove_follow(current_id, target_id)

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
    return followers


def get_followed(username):
    from flaskr.users import user_index
    db = get_db()
    target_id = user_index[username].id
    followed = db.session.query(User) \
        .join(Follow, Follow.followed_id == User.id) \
        .filter(Follow.follower_id == target_id) \
        .all()
    return followed


# User recommandation
class FollowGraph:

    def __init__(self):
        self.edges = dict()  # from vertices to vertices

    def delete_user(self, user_id: int):
        try:
            del self.edges[user_id]
            for key in self.edges:
                self.edges[key].remove(user_id)
        except KeyError:
            pass

    def add_follow(self, follower_id: int, followed_id: int):
        try:
            self.edges[follower_id].add(followed_id)
        except KeyError:
            self.edges[follower_id] = {followed_id}

    def remove_follow(self, follower_id: int, followed_id: int):
        try:
            self.edges[follower_id].remove(followed_id)
            if len(self.edges[follower_id]) == 0:
                del self.edges[follower_id]
        except KeyError:
            print("Unknown user")

    def recommandation(self, source_user_id: int, max_depth: int):
        if source_user_id not in self.edges:
            print("not following anyone, random suggestions")
            return random.sample(self.edges.keys(), min(max_depth, len(self.edges)))
        result = set()
        id_set = set()
        explored_set = set()
        frontier = [source_user_id]
        current_depth = 0
        while len(frontier) > 0 and current_depth <= max_depth:
            current_id = frontier.pop(0)
            explored_set.add(current_id)
            try:
                for neighboor_id in self.edges[current_id]:
                    if neighboor_id not in explored_set:
                        frontier.append(neighboor_id)
                    if neighboor_id not in self.edges[source_user_id]:
                        id_set.add(neighboor_id)
            except KeyError:  # no follow on current_id
                pass
            current_depth += 1
        # recover actual users
        db = get_db()
        for user_id in id_set:
            result.add(db.session.query(User).filter(User.id == user_id).first())
        return result

    def print(self):
        for key in self.edges:
            print("User {} follows {}".format(key, self.edges[key]))


# Global follow variable
follow_graph = FollowGraph()  # need to init it with init_follow_graph


def init_follow_graph():
    db = get_db()
    follows = db.session.query(Follow).all()
    for follow_item in follows:
        follow_graph.add_follow(follow_item.follower_id, follow_item.followed_id)
