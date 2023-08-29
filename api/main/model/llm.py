import sys
import os
import enum
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from peft import PeftConfig


p = os.path.abspath(os.path.dirname(__file__))
if p not in sys.path:
    sys.path.append(os.path.join("/", *p.split("/")[:-1]))

from config import Config


class LLMType(enum.Enum):
    QA = 1
    SQL = 2
    SUMMARY = 3


mapping = {
    LLMType.QA: Config.QA_MODEL_PATH,
    LLMType.SQL: Config.SQL_MODEL_PATH,
    LLMType.SUMMARY: Config.SUMMARY_MODEL_PATH,
}


class LLM:
    def __init__(self, config: Config, task_type: LLMType):
        self.lora_config = PeftConfig.from_pretrained(mapping[task_type])
        self.model = T5ForConditionalGeneration.from_pretrained(
            self.lora_config.base_model_name_or_path, device="auto", torch_dtype=torch.blfloat16
        )

    def process_input(self, input_text: str, tokenizer: T5Tokenizer):
        return self.lora_config.tokenizer(input_text, return_tensors="pt")
