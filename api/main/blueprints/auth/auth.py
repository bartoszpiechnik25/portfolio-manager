from flask import Blueprint, request, render_template, redirect, url_for, flash
from api.main.blueprints.forms import RegistrationForm, LoginForm
from api.main.database import Users, UsersSchema, db
from api.main import login_manager
from sqlalchemy import select
from flask_login import login_user, login_required, logout_user


auth = Blueprint("auth", __name__, url_prefix="/auth")


@auth.route("/register", methods=["POST", "GET"])
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


@auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalars(select(Users).where(Users.username == form.username.data)).first()
        if not login_user(user, form.remember_me.data):
            flash("Invalid username or password")
            return redirect(url_for("auth.login"))
        next = request.args.get("next")
        if next is None or not next.startswith("/"):
            next = url_for("index.profile")
        return redirect(next)
    return render_template("login.html", form=form), 200


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for("index.index_page"))


@login_manager.user_loader
def load_user(user_id):
    return db.session.scalars(select(Users).where(Users.user_id == user_id)).first()
