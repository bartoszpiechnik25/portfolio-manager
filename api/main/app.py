from flask_restful import Api
from flask import Flask
from api.main.resources.sql_resource import SQLController
from api.main.resources.summary_resource import SummaryController
from api.main.model.llm import LLM, LLMType
from api.main.config import CONFIG
from api.main.common.util import create_sql_parser, create_summary_request_parser


def create_app():
    app = Flask(__name__)
    api = Api(app)

    sql_model = LLM(LLMType.SQL)
    sql_parser = create_sql_parser()

    summary_model = LLM(LLMType.SUMMARY)
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
    return app
