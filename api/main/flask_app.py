from flask_restful import Api
from flask import Flask
from api.main.resources.sql_resource import SQLController
from api.main.resources.summary_resource import SummaryController
from api.main.model.llm import LLM, LLMType
from api.main.config import CONFIG
from api.main.common.util import (
    create_sql_parser,
    create_summary_request_parser,
    create_currencies,
    create_users,
    create_etfs,
    create_stocks_data,
    create_etf_investment_data,
    create_stock_investments_data,
)
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from sqlalchemy import insert

db = SQLAlchemy()
ma = Marshmallow()
bcrypt = Bcrypt()
from api.main.resources.users_resource import UserResource, UsersResource
from api.main.resources.asset_resource import Asset, Assets
from api.main.resources.investments_resource import UserInvestedAssets, Invest


def create_app(test: bool = False, db_only: bool = False, **kwargs):
    app = Flask(__name__)
    if test:
        app.config["SQLALCHEMY_DATABASE_URI"] = CONFIG.TEST_DATABASE_URI
        app.config["TESTING"] = True
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


def db_init(app: Flask = None, api: Api = None):
    from api.main.database import Currency, Users, ETF, Stock, InvestedETFs, InvestedStocks

    db.init_app(app)
    ma.init_app(app)
    bcrypt.init_app(app)

    with app.app_context():
        db.metadata.drop_all(db.engine)
        db.create_all()
        db.session.execute(insert(Currency).values(create_currencies()))
        db.session.add_all([Users(**user) for user in create_users()])
        db.session.execute(insert(ETF).values(create_etfs()))
        db.session.execute(insert(Stock).values(create_stocks_data()))
        db.session.execute(insert(InvestedETFs), create_etf_investment_data())
        db.session.execute(insert(InvestedStocks), create_stock_investments_data())
        db.session.commit()
    print(f"Connected to {app.config['SQLALCHEMY_DATABASE_URI']}")

    api.add_resource(UserResource, f"{CONFIG.USER_ENDPOINT}/<username>", CONFIG.USER_ENDPOINT)
    api.add_resource(UsersResource, CONFIG.USERS_ENDPOINT)
    api.add_resource(Asset, f"{CONFIG.ASSET_ENDPOINT}/<string:investment_type>")
    api.add_resource(Assets, f"{CONFIG.ASSETS_ENDPOINT}/<string:investment_type>")
    api.add_resource(
        UserInvestedAssets,
        f"{CONFIG.INVESTMENTS_ENDPOINT}/<username>",
    )
    api.add_resource(
        Invest,
        f"{CONFIG.INVEST_ENDPOINT}/<string:username>/<string:investment_type>",
    )
