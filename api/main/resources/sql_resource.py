from flask_restful import marshal_with
from flask import abort
from api.main.model.llm import GenerationConfig
from api.main.common.util import response_blueprint
from api.main.resources.controller import LLMController


class SQLController(LLMController):
    @marshal_with(response_blueprint)
    def post(self):
        data = self.parser.parse_args()
        try:
            generation_config = GenerationConfig(**data)
            prompt = SQLController.create_prompt(data["sql_table"], data["question"])
            result = self.model.generate_response(prompt, generation_config)
        except Exception as e:
            abort(400, str(e))
        result["code"] = 200
        return result

    def create_prompt(table: str, question: str) -> str:
        """
        Create the prompt for the model.

        Args:
            table (str): SQL table.
            question (str): Question.

        Returns:
            str: Prompt for the model.
        """
        table = table.strip()
        question = question.strip()
        start = "Given the SQL code.\n"
        end = f"Generate the SQL code to answer the following question.\n{question}"
        return f"{start}{table}\n{end}\nAnswer:"
