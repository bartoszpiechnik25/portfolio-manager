from bs4 import BeautifulSoup
from requests import get
from api.main.asset_scraper import AssetScraper, ScraperConfig
from typing import Tuple
import re


class ETFScraper(AssetScraper):
    def __init__(self, isin: str, config: ScraperConfig, arguments) -> None:
        self.config = config
        self.arguments = arguments
        self.isin = isin

    @classmethod
    def check_if_exists(cls, config: ScraperConfig, **kwargs) -> "ETFScraper":
        print(config.URLS["details_url"].format(**kwargs))
        response = get(config.URLS["details_url"].format(**kwargs), allow_redirects=False)
        if response.status_code == 302:
            raise ValueError(f"Could not find ETF with {kwargs}")
        return cls(isin=kwargs["isin"].upper(), config=config, arguments=kwargs)

    def scrape(self):
        response = get(
            self.config.URLS["details_url"].format(**self.arguments), allow_redirects=True
        )
        print(response.cookies)
        soup = BeautifulSoup(response.text, "html.parser")
        basic_info = {}

        basic_info["name"] = soup.find("h1", id="etf-title").get_text()
        basic_info["isin"] = self.isin
        basic_info["currency"] = soup.find(string="Fund currency").find_next("td").get_text()

        for content in soup.find_all("div", class_="d-flex d-flex-column"):
            vals: Tuple[str, str] = content.get_text("|", strip=True).split("|")[:2]
            basic_info[vals[0].strip().lower().replace(" ", "_")] = vals[1]

        basic_info["ter"] = float(re.match(r"\d+\.{1}\d+", basic_info["ter"]).group())
        basic_info["holdings"] = int(basic_info["holdings"])
        basic_info["fund_size"] = int(float(basic_info["fund_size"].replace(",", ".")) * 1e6)
        print(basic_info)

        # for content in soup.find_all('tbody'):
        #     print(content.get_text("|", strip=True), end='\n\n')


# if __name__ == "__main__":
# response = get(
#     "https://www.justetf.com/en/etf-profile.html?query=xdwt&query=&groupField=index&from=search&isin=IE00BM67HT60"
# )
# soup = BeautifulSoup(response.content, "html.parser")
# print(soup.prettify())
# for c in soup.find_all("div", class_="d-flex d-flex-column", recursive=True):
# print(c.get_text("|", strip=True), end="\n\n")
# print(c)
