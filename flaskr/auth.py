import functools
import time

from flask import (
    Blueprint, flash, g, jsonify, redirect, render_template, request, session, url_for
)
from sqlalchemy import select
from flaskr.db import User, get_db
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().session.query(User).where(User.id == user_id).first()


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.session.query(User).where(User.email == email).first()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.password, password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for("tweets.index"))

        return error, 401

    return render_template('auth/register_login.html', action="login")


@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not email:
            error = 'Email is required'

        if error is None:
            try:
                new_user = User(
                    username=username,
                    email=email,
                    password=generate_password_hash(password),
                )
                db.session.add(new_user)
                db.session.commit()
            except Exception:  # Not good I know but it works where db.IntegrityError doesn't
                error = f"User {username} is already registered or {email} is already used."
                return error, 402
            else:
                from flaskr.users import update_user_index
                update_user_index(new_user)
                session.clear()
                session['user_id'] = new_user.id
                return redirect(url_for("tweets.index"))

    return render_template('auth/register_login.html', action="register")


@bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('tweets.index'))
