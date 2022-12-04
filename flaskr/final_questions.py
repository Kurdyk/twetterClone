import click

# Question 1


@click.command("symetric-relationship")
@click.option("--name", required=False, default=False, flag_value="name")
def symetric_relation(name):
    from flaskr.db import Follow, get_db
    db = get_db()
    follows = db.session.query(Follow).all()
    follows_as_pair = list()
    for follow in follows:
        follows_as_pair.append((follow.follower_id, follow.followed_id))
    seen = set()
    result = set()
    for pair in follows_as_pair:
        seen.add(pair)
        follower, followed = pair
        if (followed, follower) in seen:
            result.add(pair)
    print(f"symetric relations : {result}")
    if name:
        user_index = create_index()
        for pair in result:
            i, j = pair
            print(f"Symetric relation between: {user_index[i].username} and {user_index[j].username}")
    return None


def create_index():
    from flaskr.db import User, get_db
    db = get_db()
    result = dict()     # id -> User
    users = db.session.query(User).all()
    for user in users:
        result[user.id] = user
    return result

# Question 2


class FollowingGraph:

    def __init__(self):
        from flaskr.db import get_db, Follow
        self.edges = dict()  # from vertices to vertices
        db = get_db()
        follows = db.session.query(Follow).all()
        for follow in follows:
            try:
                self.edges[follow.followed_id].add(follow.follower_id)
            except KeyError:
                self.edges[follow.followed_id] = {follow.follower_id}

    def find_followers(self,  source_user_id: int, max_depth: int):
        from flaskr.db import User, get_db
        if source_user_id not in self.edges:
            print("Not followed by anyone")
            return None
        id_set = set()
        explored_set = set()
        frontier = [source_user_id]
        current_depth = 0
        while len(frontier) > 0 and current_depth <= max_depth:
            current_id = frontier.pop(0)
            explored_set.add(current_id)
            try:
                for neighboor_id in self.edges[current_id]:
                    if neighboor_id not in explored_set and neighboor_id not in frontier:
                        frontier.append(neighboor_id)
                    if neighboor_id != source_user_id:
                        id_set.add((neighboor_id, current_depth))
            except KeyError:  # no follow on current_id
                pass
            current_depth += 1
        # recover actual users
        db = get_db()
        for user_id, depth in id_set:
            username = db.session.query(User).filter(User.id == user_id).first().username
            print(f"At depth {depth}: follower {username}")
        return None

    def print(self):
        for key in self.edges:
            print("User {} is followed by {}".format(key, self.edges[key]))


@click.command("followers-graph")
@click.option("--depth", required=True, default=2)
@click.option("--user_id", required=True)
def get_followers_with_depth(depth, user_id):
    following_graph = FollowingGraph()
    following_graph.find_followers(int(user_id), int(depth))
