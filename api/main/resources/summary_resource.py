from api.main.resources.controller import LLMController
from api.main.common.util import response_blueprint
from flask_restful import marshal_with
from flask import abort
from api.main.model.llm import GenerationConfig


class SummaryController(LLMController):
    @marshal_with(response_blueprint)
    def post(self):
        data = self.parser.parse_args()
        try:
            generation_config = GenerationConfig(**data)
            prompt = SummaryController.create_prompt(data["text"])
            result = self.model.generate_response(prompt, generation_config)
        except Exception as e:
            abort(400, str(e))
        result["status_code"] = 200
        return result

    def create_prompt(text: str) -> str:
        """
        Create the prompt for the model.

        Args:
            text (str): Text.

        Returns:
            str: Prompt for the model.
        """
        text = text.strip().strip("\n")
        start = "Summarize the following text.\n"
        return f"{start}{text}\nSummary:"
