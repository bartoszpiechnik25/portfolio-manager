from flask_restful import Resource, Api, marshal_with, reqparse
from flask import Flask, abort
from api.main.model.llm import LLM, LLMType, GenerationConfig
from api.main.config import CONFIG
from api.main.common.util import create_sql_parser, t5_sql_response


class LLMController(Resource):
    def __init__(self, **kwargs) -> None:
        self.model: LLM = kwargs["model"]
        self.parser: reqparse.RequestParser = kwargs["parser"]

    @marshal_with(t5_sql_response)
    def post(self):
        data = self.parser.parse_args()
        try:
            generation_config = GenerationConfig(**data)
            prompt = self.model.create_prompt(data["sql_table"], data["question"])
            result = self.model.generate_response(prompt, generation_config)
        except Exception as e:
            abort(400, str(e))
        result["code"] = 200
        return result


app = Flask(__name__)
api = Api(app)

sql_model = LLM(LLMType.SQL)
sql_parser = create_sql_parser()

api.add_resource(
    LLMController,
    CONFIG.TEX2SQL_ENDPOINT,
    resource_class_kwargs={"model": sql_model, "parser": sql_parser},
)

if __name__ == "__main__":
    app.run(debug=True)
