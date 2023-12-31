from flask_restful import Resource
from api.main import db
from api.main.database import Users, UsersSchema
from flask import request, abort
from sqlalchemy import select, update, delete
from api.main.common.util import create_user_parser


class UserResource(Resource):
    def __init__(self) -> None:
        self.parser = create_user_parser()
        self.user_schema = UsersSchema()

    def get(self, username: str):
        db_user = db.session.scalars(select(Users).where(Users.username == username)).one_or_none()
        if db_user is None:
            abort(404, "User not found")
        return self.user_schema.dump(db_user), 200

    def post(self):
        data = self.parser.parse_args()

        users = db.session.execute(
            select(Users).where(Users.username == data["username"])
        ).one_or_none()
        if users is not None:
            abort(400, f"User with username: {data['username']} already exists!")

        emails = db.session.execute(select(Users).where(Users.email == data["email"])).one_or_none()
        if emails is not None:
            abort(400, f"User with email: {data['email']} already exists!")

        user = Users(**data)
        db.session.add(user)
        db.session.commit()
        return self.user_schema.dump(user), 201

    def delete(self, username: str):
        result = db.session.execute(delete(Users).where(Users.username == username))

        if result.rowcount == 0:
            abort(404, f"User '{username}' not found")

        db.session.commit()
        return "", 204

    def put(self, username: str):
        result = db.session.scalars(select(Users).where(Users.username == username)).one_or_none()
        if result is None:
            args = request.json
            args["username"] = username
            if not Users.required_fields_in_request_body(args):
                abort(
                    400,
                    f"Unable to find user '{username}'"
                    + "\nCan't create new user due to missing fields!",
                )
            user = Users(**args)
            db.session.add(user)
            db.session.commit()
            return self.user_schema.dump(user), 201
        else:
            if not Users.valid_field_in_request_body(request.json):
                abort(400, "Invalid fields in request body!")
            db.session.execute(update(Users).where(Users.username == username).values(request.json))
            db.session.commit()
            return self.user_schema.dump(result), 200


class UsersResource(Resource):
    def get(self):
        users = db.session.scalars(select(Users)).all()
        user_schema = UsersSchema()
        return [user_schema.dump(user) for user in users], 200
