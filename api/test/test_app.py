from api.main.flask_app import db, create_app
from api.main.config import CONFIG
from api.main.common.util import create_user_parser
from api.main.resources.users_resource import UserResource, UsersResource

app, api = create_app(test=True)

db.init_app(app)

user_parser = create_user_parser()
api.add_resource(
    UserResource,
    f"{CONFIG.USER_ENDPOINT}/<username>",
    CONFIG.USER_ENDPOINT,
    resource_class_kwargs={"parser": user_parser},
)

api.add_resource(UsersResource, CONFIG.USERS_ENDPOINT)

with app.app_context():
    db.create_all()
