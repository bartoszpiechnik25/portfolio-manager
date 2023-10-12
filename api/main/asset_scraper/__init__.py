from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from api.main import db
from sqlalchemy import select
from api.main.database import Investments
from typing import Dict, Any
from api.main.config import AssetTypes
from flask import current_app


def get_types_from_DB() -> Dict[str, int]:
    """
    Fetches the database to get all investment types.

    Returns:
        Dict[str, int]: Dictionary with type and corresponding integer number.
    """
    types = []
    with current_app.app_context():
        values = db.session.scalars(select(Investments.type).distinct(Investments.type)).all()
    for value in values:
        attr_name = value[:-1].upper()
        types.append(attr_name)
    return types


url_mapper = {
    AssetTypes.ETF: {
        "exists_url": "https://www.justetf.com/en/find-etf.html?query={}",
        "details_url": "https://www.justetf.com/en/etf-profile.html?query={query}&isin={isin}",
    },
    AssetTypes.STOCK: {"todo": "todo"},
}


@dataclass
class ScraperConfig:
    ASSET_TYPE: int
    URLS: Dict[str, str] = field(init=False)

    def __post_init__(self):
        types = get_types_from_DB()
        for t in types:
            if not getattr(AssetTypes, t, None):
                raise AttributeError(
                    f"Asset type {t} not found in AssetTypes enum. Add {t} to the AssetTypes!"
                )
        self.URLS = url_mapper[self.ASSET_TYPE]


class AssetScraper(ABC):
    @classmethod
    @abstractmethod
    def check_if_exists(cls, config: ScraperConfig, **kwargs) -> "AssetScraper":
        pass

    @abstractmethod
    def scrape(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _create_soup(self):
        pass
