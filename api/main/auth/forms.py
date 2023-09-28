from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
)
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, Regexp
from api.main import db
from sqlalchemy import select
from api.main.database import Users


class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(min=1, max=255)])
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=2, max=40),
            Regexp(
                "^[A-Za-z_][A-Za-z0-9_.]*$",
                0,
                "Username must contain only letters, numbers dots or underscores",
            ),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=5, max=64, message="Password must be between at lest 5 characters long"),
            EqualTo("confirm_password", message="Passwords must match"),
        ],
    )
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    name = StringField("Name", validators=[Length(min=0, max=255)])
    surname = StringField("Surname", validators=[Length(min=0, max=255)])
    submit = SubmitField("Sign Up")

    def validate_email(self, field):
        if db.session.execute(select(Users).where(Users.email == field.data)).one_or_none():
            raise ValidationError("Email already in use!")

    def validate_username(self, field):
        if db.session.execute(select(Users).where(Users.username == field.data)).one_or_none():
            raise ValidationError("Username already exists!")
