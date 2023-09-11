from flask_restful import Resource
from api.main.flask_app import db
from api.main.database import Users
from flask_restful import reqparse
from flask import request, abort
from sqlalchemy import select, update, delete


class UserResource(Resource):
    def __init__(self, **kwargs) -> None:
        self.parser: reqparse.RequestParser = kwargs["parser"]

    def get(self, username: str):
        db_user = db.session.execute(select(Users).where(Users.username == username)).first()
        if db_user is None:
            return {"message": "User not found"}, 404
        return db_user[0].serialize(), 200

    def post(self):
        data = self.parser.parse_args()

        users = db.session.execute(select(Users).where(Users.username == data["username"])).first()
        if users is not None:
            return {"message": f"User with username: {data['username']} already exists!"}, 400

        emails = db.session.execute(select(Users).where(Users.email == data["email"])).first()
        if emails is not None:
            return {"message": f"User with email: {data['email']} already exists!"}, 400

        user = Users(**data)
        db.session.add(user)
        db.session.commit()
        return user.serialize(), 201

    def delete(self, username: str):
        result = db.session.execute(select(Users).where(Users.username == username)).first()
        if result is None:
            return {"message": f"User '{username}' not found"}, 404
        db.session.execute(delete(Users).where(Users.username == username))
        db.session.commit()
        return "", 204

    def put(self, username: str):
        result = db.session.execute(select(Users).where(Users.username == username)).first()
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
            return user.serialize(), 201
        else:
            if not Users.valid_field_in_request_body(request.json):
                abort(400, "Invalid fields in request body!")
            db.session.execute(update(Users).where(Users.username == username).values(request.json))
            db.session.commit()
            return result[0].serialize(), 200


class UsersResource(Resource):
    def get(self):
        users = db.session.execute(select(Users)).all()
        return [user[0].serialize() for user in users], 200
