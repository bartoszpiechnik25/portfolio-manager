from flask_restful import Resource, reqparse
from abc import ABC, abstractmethod
from api.main.model.llm import LLM
from typing import Dict, Union


class LLMController(Resource, ABC):
    def __init__(self, **kwargs) -> None:
        self.model: LLM = kwargs["model"]
        self.parser: reqparse.RequestParser = kwargs["parser"]

    @abstractmethod
    def post(self):
        raise NotImplementedError("Subclass must implement post method!")

    @staticmethod
    @abstractmethod
    def create_prompt(text: Union[str, Dict[str, str]]) -> str:
        raise NotImplementedError("Subclass must implement create_prompt method!")
