from api.main.auth.forms import RegistrationForm
from api.main.database import Users, UsersSchema, db
from flask import request, render_template


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
