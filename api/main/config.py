from dataclasses import dataclass
import os
import enum
import dotenv
from typing import Dict

env = dotenv.dotenv_values(".env")

api_dir = os.path.abspath(os.path.dirname(__file__))


@dataclass
class EndpointsConfig:
    """
    Configuration for conveninent access to the models.

    Args:
        SQL_MODEL_PATH (str): Path to the SQL model.
        QA_MODEL_PATH (str): Path to the QA model.
        SUMMARY_MODEL_PATH (str): Path to the summary model.
        QA_ENDPOINT (str, optional): Endpoint for QA. Defaults to "/api/v1/qa".
        TEX2SQL_ENDPOINT (str, optional): Endpoint for text2sql. Defaults to "/api/v1/text2sql".
        SUMMARY_ENDPOINT (str, optional): Endpoint for summary. Defaults to "/api/v1/summary".
    """

    SQL_MODEL_PATH: str
    QA_MODEL_PATH: str
    SUMMARY_MODEL_PATH: str
    USERS_ENDPOINT: str = "/api/v1/users"
    USER_ENDPOINT: str = "/api/v1/user"
    ASSET_ENDPOINT: str = "/api/v1/asset"
    ASSETS_ENDPOINT: str = "/api/v1/assets"
    INVESTMENTS_ENDPOINT: str = "/api/v1/invested"
    INVEST_ENDPOINT: str = "/api/v1/invest"
    QA_ENDPOINT: str = "/api/v1/qa"
    TEX2SQL_ENDPOINT: str = "/api/v1/text2sql"
    SUMMARY_ENDPOINT: str = "/api/v1/summary"


class Config:
    SECRET_KEY = env["SECRET_KEY"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BUNDLE_ERRORS = True
    DB_ONLY = True

    @staticmethod
    def init_app(app):
        pass


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = env["TEST_DATABASE_URI"]
    DB_ONLY = False


class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = env["DATABASE_URI"]


class LLMType(enum.Enum):
    QA = 1
    SQL = 2
    SUMMARY = 3


p_dir = os.path.dirname(api_dir).replace("/api", "")


def get_model_path(llm_type: str, project_dir: str) -> str:
    llm_type_to_path = {
        LLMType.QA: "flan_t5/models/lora_flan-t5-large_finance-alpaca/",
        LLMType.SQL: "flan_t5/models/lora_flan-t5-large_Llama-2-SQL-Dataset/",
        LLMType.SUMMARY: "flan_t5/models/lora_flan-t5-large_cnn_dailymail/",
    }
    llm_type_to_hub = {
        LLMType.QA: "barti25/lora_flan-t5-large_finance_alpaca",
        LLMType.SQL: "barti25/lora_flan-t5-large_Llama-2-SQL-Dataset",
        LLMType.SUMMARY: "barti25/lora_flan-t5-large_cnn_dailymail",
    }
    path = os.path.join(project_dir, llm_type_to_path[llm_type])
    return llm_type_to_hub[llm_type] if not os.path.isdir(path) else path


ENDPOINTS_CONFIG = EndpointsConfig(
    SQL_MODEL_PATH=get_model_path(LLMType.SQL, p_dir),
    QA_MODEL_PATH=get_model_path(LLMType.QA, p_dir),
    SUMMARY_MODEL_PATH=get_model_path(LLMType.SUMMARY, p_dir),
)

CONFIG: Dict[str, Config] = {
    "test": TestConfig,
    "dev": DevConfig,
}


mapping = {
    LLMType.QA: ENDPOINTS_CONFIG.QA_MODEL_PATH,
    LLMType.SQL: ENDPOINTS_CONFIG.SQL_MODEL_PATH,
    LLMType.SUMMARY: ENDPOINTS_CONFIG.SUMMARY_MODEL_PATH,
}
