import random
import string

from flaskr.db import get_db, User, add_random_user


def random_user():
    random_animal = ""
    with open('./utils/animals.txt') as f:
        lines = [line.rstrip('\n') for line in f]
        random_animal = random.choice(lines)

    random_adjective = ""
    with open('./utils/adjectives.txt') as f:
        lines = [line.rstrip('\n') for line in f]
        random_adjective = random.choice(lines)

    return {
        "name": random_adjective + " " + random_animal,
        "email": ''.join(random.choice(string.ascii_letters) for _ in range(random.randrange(1, 25)))+"@gmail.com",
        "password": "password"
    }


def random_tweet():
    with open('./utils/animals.txt') as f:
        animals = [line.rstrip('\n') for line in f]
    with open('./utils/adjectives.txt') as f:
        adjectives = [line.rstrip('\n') for line in f]
    users_id = get_db().session.query(User.id).all()
    if not users_id:
        print("no user found, create an user before")
        exit(1)
    uid = random.choice(users_id)['id']
    return {
        'uid': uid,
        'title': " ".join(random.sample(animals + adjectives, 5)),
        'content': " ".join(random.sample(animals + adjectives, 10))
    }
