from flask_restful import Resource, reqparse
from abc import ABC, abstractmethod
from api.main.model.llm import LLM


class LLMController(Resource, ABC):
    def __init__(self, **kwargs) -> None:
        self.model: LLM = kwargs["model"]
        self.parser: reqparse.RequestParser = kwargs["parser"]

    @abstractmethod
    def post(self):
        pass

    @staticmethod
    @abstractmethod
    def create_prompt() -> str:
        pass
