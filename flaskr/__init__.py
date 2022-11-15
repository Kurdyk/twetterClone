import os

from flask import Flask
from flaskr.tweets import init_index


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = 'dev'
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        app.instance_path, 'flaskr.sqlite')
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = 0

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import users
    app.register_blueprint(users.bp)

    from . import tweets
    app.register_blueprint(tweets.bp)

    with app.app_context():
        init_index()

    return app
