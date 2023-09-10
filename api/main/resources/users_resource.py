from flask_restful import Resource
from api.main.flask_app import db
from api.main.database import Users
from flask_restful import reqparse


class UserController(Resource):
    def __init__(self, **kwargs) -> None:
        self.parser: reqparse.RequestParser = kwargs["parser"]

    def get(self, user_id: str):
        db_user = db.session.query(Users).filter_by(user_id=user_id).first()
        if db_user is None:
            return {"message": "User not found"}, 404
        return db_user.serialize(), 200

    # def get(self):
    #     users = db.session.query(Users).all()
    #     return [user.serialize() for user in users], 200

    def post(self):
        data = self.parser.parse_args()
        users = db.session.query(Users).filter_by(username=data["username"]).all()

        if Users.username_exists(data["username"], users):
            return {"message": f"User with username: {data['username']} already exists!"}, 400

        if Users.email_exists(data["email"], users):
            return {"message": f"User with email: {data['email']} already exists!"}, 400
        user = Users(**data)
        db.session.add(user)
        db.session.commit()
        return user.serialize(), 201
