from flask import Blueprint, render_template
from flask_login import current_user, login_required


index = Blueprint("index", __name__, url_prefix="/")


@index.route("/", methods=["GET"])
def index_page():
    user_name = None
    if current_user.is_authenticated:
        user_name = current_user.username
    return render_template("index.html", user_name=user_name), 200


@index.route("/profile", methods=["GET"])
@login_required
def profile():
    if not current_user.confirmed:
        return render_template("unconfirmed.html")
    return render_template("profile.html", user=current_user), 200
