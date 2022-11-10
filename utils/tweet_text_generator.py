
import random
import string


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
