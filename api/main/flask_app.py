from flask_restful import Api
from flask import Flask
from api.main.resources.sql_resource import SQLController
from api.main.resources.summary_resource import SummaryController
from api.main.model.llm import LLM, LLMType
from api.main.config import CONFIG
from api.main.common.util import (
    create_sql_parser,
    create_summary_request_parser,
    create_user_parser,
)
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(test: bool = False, db_only: bool = False, **kwargs):
    app = Flask(__name__)
    if test:
        app.config["SQLALCHEMY_DATABASE_URI"] = CONFIG.TEST_DATABASE_URI
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = CONFIG.DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    api = Api(app)

    if db_only:
        return app, api

    sql_model = LLM(LLMType.SQL) if "sql_model" not in kwargs else kwargs["sql_model"]
    sql_parser = create_sql_parser()

    summary_model = (
        LLM(LLMType.SUMMARY) if "summary_model" not in kwargs else kwargs["summary_model"]
    )
    summary_parser = create_summary_request_parser()

    api.add_resource(
        SQLController,
        CONFIG.TEX2SQL_ENDPOINT,
        resource_class_kwargs={"model": sql_model, "parser": sql_parser},
    )

    api.add_resource(
        SummaryController,
        CONFIG.SUMMARY_ENDPOINT,
        resource_class_kwargs={"model": summary_model, "parser": summary_parser},
    )
    return app, api


app, api = create_app(test=True)


# if __name__ == "__main__":
from api.main.resources.users_resource import UserController

db.init_app(app)

user_parser = create_user_parser()
api.add_resource(
    UserController, "/users/<user_id>", "/users", resource_class_kwargs={"parser": user_parser}
)

with app.app_context():
    db.create_all()
