from dataclasses import dataclass
import os
import enum
import dotenv
from typing import Dict

api_dir = os.path.abspath(os.path.dirname(__file__))
dotenv.load_dotenv()


@dataclass
class EndpointsConfig:
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
    REGISTER_ENDPOINT: str = "/auth/register"
    LOGIN_ENDPOINT: str = "/auth/login"


@dataclass
class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY") or "very_secret_key"
    MAIL_SERVER = os.environ.get("MAIL_SERVER") or "smtp.gmail.com"
    MAIL_PORT = os.environ.get("MAIL_PORT") or 465
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME") or ""
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD") or ""
    FLASK_MAIL_SENDER = "FlaskyPortfolioManager@no-reply.com"

    BUNDLE_ERRORS = True
    DB_ONLY = True

    @staticmethod
    def init_app(app):
        pass


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:siema@localhost:5432/portfolio_manager_test"
    DB_ONLY = False


class DevConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:siema@localhost:5432/portfolio_manager"


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
