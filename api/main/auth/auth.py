from api.main.auth.forms import RegistrationForm, LoginForm
from api.main.database import Users, UsersSchema, db
from api.main import login_manager
from flask import request, render_template, flash, url_for, redirect
from sqlalchemy import select
from flask_login import login_user, current_user, login_required, logout_user


def index():
    user_name = None
    if current_user.is_authenticated:
        user_name = current_user.username
    return render_template("index.html", user_name=user_name), 200


@login_required
def profile():
    user = current_user
    return render_template("profile.html", user=user), 200


def register():
    form = RegistrationForm()
    if form.validate_on_submit() and request.method == "POST":
        user = Users(
            username=form.data["username"],
            email=form.data["email"],
            password=form.data["password"],
            name=form.data["name"],
            surname=form.data["surname"],
        )
        db.session.add(user)
        db.session.commit()
        return UsersSchema().dump(user), 201

    return render_template("register.html", form=form), 200


@login_manager.user_loader
def load_user(user_id):
    return db.session.scalars(select(Users).where(Users.id == user_id)).first()


def login():
    form = LoginForm()
    print(form.data)
    if form.validate_on_submit():
        user = db.session.scalars(select(Users).where(Users.username == form.username.data)).first()
        if not login_user(user, form.remember_me.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        next = request.args.get("next")
        if next is None or not next.startswith("/"):
            next = url_for("profile")
        return redirect(next)
    return render_template("login.html", form=form), 200


@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("index")), 200
