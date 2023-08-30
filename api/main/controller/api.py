from flask_restful import Resource, Api
from flask import request, Flask, abort
import sys
import os

p = os.path.abspath(os.path.dirname(__file__))
p = os.path.join("/", *p.split("/")[:-1])
if p not in sys.path:
    sys.path.append(p)

from model.llm import LLM, LLMType, GenerationConfig

sql_model = LLM(LLMType.SQL)


class LLMController(Resource):
    def post(self):
        data = request.get_json()
        text = data["text"]
        return_sequences = (
            int(data["num_return_sequences"]) if "num_return_sequences" in data else 1
        )
        try:
            generation_config = GenerationConfig(
                temperature=1.0,
                max_new_tokens=150,
                length_penalty=1.0,
                use_cache=True,
                num_return_sequences=return_sequences,
            )
            result = sql_model.generate_response(text, generation_config)
        except Exception as e:
            abort(400, str(e))
        return result, 200


app = Flask(__name__)
api = Api(app)

# qa_model = LLMController(LLMType.QA)

api.add_resource(LLMController, "/sql")
# api.add_resource(LLMController, "/qa")

if __name__ == "__main__":
    app.run(debug=True)
