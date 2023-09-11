import uuid
from api.main.flask_app import db
from typing import List, Dict

FIELDS = [
    "username",
    "password",
    "email",
    "name",
    "surname",
]


class Users(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    username = db.Column(db.db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True, default=None)
    surname = db.Column(db.String(255), nullable=True, default=None)

    def __repr__(self) -> str:
        return "User(id={}, username={}, password={}, email={}, name={}, surname={})".format(
            self.user_id, self.username, self.password, self.email, self.name, self.surname
        )

    def serialize(self):
        return {
            "user_id": str(self.user_id),
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "name": self.name,
            "surname": self.surname,
        }

    @staticmethod
    def required_fields_in_request_body(args: dict) -> bool:
        fields = ["username", "email", "password"]
        return all(field in args for field in fields)

    @staticmethod
    def valid_field_in_request_body(args: Dict[str, str], fields: List[str] = FIELDS) -> bool:
        return all(arg in fields for arg in args)
