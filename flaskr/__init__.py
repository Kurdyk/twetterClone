import os

from flask import Flask
from flaskr.tweets import init_index
from flaskr.users import init_user_index
from flaskr.follows import init_follow_graph


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = 'dev'
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        app.instance_path, 'flaskr.sqlite')
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = 0
    app.config["UPLOAD_FOLDER"] = os.path.join(app.instance_path, 'uploads')

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError as e:
        pass

    try:
        os.makedirs(app.config["UPLOAD_FOLDER"])
    except OSError as e:
        pass

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import users
    app.register_blueprint(users.bp)

    from . import tweets
    app.register_blueprint(tweets.bp)
    app.add_url_rule('/', endpoint='tweets.index')

    from . import follows
    app.register_blueprint(follows.bp)

    with app.app_context():
        init_index()
        init_user_index()
        init_follow_graph()

    return app
