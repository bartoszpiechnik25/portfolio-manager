from dataclasses import dataclass
import os

api_dir = os.path.abspath(os.path.dirname(__file__))


@dataclass
class Config:
    proj_dir: str = os.path.dirname(api_dir).replace("/api", "")
    SQL_MODEL_PATH: str = os.path.join(
        proj_dir, "flan_t5/models/lora_flan-t5-large_Llama-2-SQL-Dataset/"
    )
    QA_MODEL_PATH: str = os.path.join(proj_dir, "flan_t5/models/lora_flan-t5-large_finance-alpaca/")
    SUMMARY_MODEL_PATH: str = ""
