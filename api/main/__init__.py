from flask_restful import Api
from flask import Flask
from api.main.resources.sql_resource import SQLController
from api.main.resources.summary_resource import SummaryController
from api.main.model.llm import LLM, LLMType
from api.main.config import ENDPOINTS_CONFIG, CONFIG
from api.main.common.error_handler import page_not_found
from api.main.common.util import (
    create_sql_parser,
    create_summary_request_parser,
    create_currencies,
    create_users,
    create_etfs,
    create_stocks_data,
    create_etf_investment_data,
    create_stock_investments_data,
    create_etf_providers,
    create_replication_methods,
)
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from sqlalchemy import insert

login_manager = LoginManager()
login_manager.login_view = "auth.login"
db = SQLAlchemy()
ma = Marshmallow()
bcrypt = Bcrypt()
mail = Mail()

from api.main.resources.users_resource import UserResource, UsersResource
from api.main.resources.asset_resource import Asset, Assets
from api.main.resources.investments_resource import UserInvestedAssets, Invest
from api.main.blueprints.auth.auth import auth
from api.main.blueprints.index import index


def create_app(config_name: str):
    app = Flask(__name__)
    app.config.from_object(CONFIG[config_name])
    CONFIG[config_name].init_app(app)

    from api.main.database import (
        Currency,
        Users,
        ETF,
        Stock,
        InvestedETFs,
        InvestedStocks,
        ETFProviders,
        ETFReplicationMethods,
    )

    api = Api(app)
    db.init_app(app)
    ma.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    app.register_error_handler(404, page_not_found)
    app.register_blueprint(auth)
    app.register_blueprint(index)

    with app.app_context():
        db.metadata.drop_all(db.engine)
        db.create_all()
        db.session.execute(insert(Currency).values(create_currencies()))
        db.session.execute(insert(ETFReplicationMethods).values(create_replication_methods()))
        db.session.add_all([Users(**user) for user in create_users()])
        db.session.execute(insert(ETFProviders).values(create_etf_providers()))
        db.session.execute(insert(ETF).values(create_etfs()))
        db.session.execute(insert(Stock).values(create_stocks_data()))
        db.session.execute(insert(InvestedETFs), create_etf_investment_data())
        db.session.execute(insert(InvestedStocks), create_stock_investments_data())
        db.session.commit()
    print(f"Connected to {app.config['SQLALCHEMY_DATABASE_URI']}")

    api.add_resource(
        UserResource, f"{ENDPOINTS_CONFIG.USER_ENDPOINT}/<username>", ENDPOINTS_CONFIG.USER_ENDPOINT
    )
    api.add_resource(UsersResource, ENDPOINTS_CONFIG.USERS_ENDPOINT)
    api.add_resource(Asset, f"{ENDPOINTS_CONFIG.ASSET_ENDPOINT}/<string:investment_type>")
    api.add_resource(Assets, f"{ENDPOINTS_CONFIG.ASSETS_ENDPOINT}/<string:investment_type>")
    api.add_resource(
        UserInvestedAssets,
        f"{ENDPOINTS_CONFIG.INVESTMENTS_ENDPOINT}/<username>",
    )
    api.add_resource(
        Invest,
        f"{ENDPOINTS_CONFIG.INVEST_ENDPOINT}/<string:username>/<string:investment_type>",
    )

    if not CONFIG[config_name].DB_ONLY:
        sql_model = LLM(LLMType.SQL)
        sql_parser = create_sql_parser()

        summary_model = LLM(LLMType.SUMMARY)
        summary_parser = create_summary_request_parser()

        api.add_resource(
            SQLController,
            ENDPOINTS_CONFIG.TEX2SQL_ENDPOINT,
            resource_class_kwargs={"model": sql_model, "parser": sql_parser},
        )

        api.add_resource(
            SummaryController,
            ENDPOINTS_CONFIG.SUMMARY_ENDPOINT,
            resource_class_kwargs={"model": summary_model, "parser": summary_parser},
        )

    return app
