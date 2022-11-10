
import click
from flask import current_app, g
from select import select
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select

db = SQLAlchemy()


def init_app(app):
    with app.app_context():
        db.init_app(app)
        db.create_all()
        app.cli.add_command(add_random_user)


def get_db():
    if 'db' not in g:
        g.db = db
    return g.db


@click.command('add-random-user')
def add_random_user():
    from utils.tweet_text_generator import random_user
    user = random_user()
    new_user = User(
        username=user["name"],
        email=user["email"],
        password=user["password"],
    )
    db.session.add(new_user)
    db.session.commit()
    click.echo('Added random user.')


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(24), nullable=False)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password
        }
