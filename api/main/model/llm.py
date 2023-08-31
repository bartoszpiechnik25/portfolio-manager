import torch
from transformers import T5ForConditionalGeneration, AutoTokenizer, GenerationConfig, BatchEncoding
from peft import PeftConfig, PeftModel
from typing import List, Union, Dict
from api.main.config import LLMType, mapping


class LLM:
    """
    Language model wrapper for the LORA models.

    Args:
        task_type (LLMType): Type of the task.

    Attributes:
        lora_config (PeftConfig): Configuration for the LORA model.
        model (PeftModel): LORA model.
        tokenizer (AutoTokenizer): Tokenizer for the LORA model.
    """

    def __init__(self, task_type: LLMType) -> None:
        self.lora_config = PeftConfig.from_pretrained(mapping[task_type])
        self.model = T5ForConditionalGeneration.from_pretrained(
            self.lora_config.base_model_name_or_path, device_map="auto", torch_dtype=torch.bfloat16
        )
        self.model = PeftModel.from_pretrained(self.model, mapping[task_type], is_trainable=False)
        self.tokenizer = AutoTokenizer.from_pretrained(self.lora_config.base_model_name_or_path)
        self.model.eval()

    def process_input(self, input_text: str, return_tensors: str = "pt") -> BatchEncoding:
        """
        Process the input text to be fed to the model.

        Args:
            input_text (str): Input text to process.
            return_tensors (str, optional): Type of tensors to return. Defaults to "pt".

        Returns:
            BatchEncoding: Processed input text.
        """
        tokenized_input = self.tokenizer(
            input_text,
            return_tensors=return_tensors,
            padding="max_length",
            truncation=True,
            max_length=self.tokenizer.model_max_length,
            return_length=True,
            verbose=False,
        )
        if tokenized_input["length"][0] > self.tokenizer.model_max_length:
            tokenized_input["tokenizer_warning"] = (
                f"Input text longer than {self.tokenizer.model_max_length} "
                + "tokens output might be inaccurate due to truncation."
            )
        return tokenized_input

    def generate_response(
        self, text: str, generation_config: GenerationConfig
    ) -> Dict[str, Union[str, List[str]]]:
        """
        Generate the response from the model.

        Args:
            text (str): Input text.
            generation_config (GenerationConfig): Configuration for the generation.

        Returns:
            Dict[str, Union[str, List[str]]]: Generated text and warning if any.
        """
        input = self.process_input(text)
        generated_ids = self.model.generate(
            input_ids=input["input_ids"].to(self.model.device), generation_config=generation_config
        )
        response = {
            "generated_text": self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True),
            "tokenizer_warning": input.get("tokenizer_warning", None),
        }
        return response

    @staticmethod
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


if __name__ == "__main__":
    model = LLM(LLMType.SQL)
    print(mapping)
    config = GenerationConfig(
        temperature=1.0, max_new_tokens=150, length_penalty=1.0, use_cache=True
    )
    text = """Given the SQL code.
CREATE TABLE department (creation VARCHAR, department_id VARCHAR);
CREATE TABLE management (department_id VARCHAR, head_id VARCHAR);
CREATE TABLE head (head_id VARCHAR, born_state VARCHAR)

Generate the SQL code to answer the following question.
What are the distinct creation years of the departments
managed by a secretary born in state 'Alabama'?
Answer:
"""
    print(model.generate_response(text, config))
