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

    @app.route("/docs")
    def api_docs():
        html_content = """
        <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>REST API Documentation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        h1 {
            color: #333;
        }
        p {
            color: #666;
        }
    </style>
</head>
<body>
    <h1>Welcome to FLAN-T5 REST API</h1>
    <p>This is the documentation of the REST API.
    Below, you'll find information about the available endpoints and how to use them.</p>

    <h2>Endpoints</h2>
    <ul>
        <li><strong>/api/summary</strong>: Create summary for a given article. </li>
        <li><strong>/api/text2sql</strong>: Generate SQL query given code generating
        table/tables and quetsion regarding this table.</li>
        <!-- Add more endpoints and descriptions as needed -->
    </ul>

    <h2>Usage</h2>
    <p>To use this API, make HTTP requests to the appropriate endpoints using the POST method.</p>

    <h2>Response Format</h2>
    <pre>
    {
        "status_code": "Integer",
        "generated_sequence": ["String"],
        "tokenizer_warning": "String"
    }
    </pre>

    <h2>Errors</h2>
    <p>Explain how your API handles errors and provides error responses,
    including error codes and descriptions.</p>

    <footer>
        <p>&copy; 2023 bartoszpiechnik25</p>
    </footer>
</body>
</html>
"""
        return html_content

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
