from bs4 import BeautifulSoup
from typing import Dict, Any
from requests import get
from api.main.asset_scraper import AssetScraper, ScraperConfig
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ETFScraper(AssetScraper):
    def __init__(self, isin: str, ticker: str, config: ScraperConfig, arguments) -> None:
        self.config = config
        self.arguments = arguments
        self.isin = isin
        self.ticker = ticker
        self._create_soup()

    @classmethod
    def check_if_exists(cls, config: ScraperConfig, **url_kwargs) -> "ETFScraper":
        print(config.URLS["details_url"].format(**url_kwargs))
        response = get(config.URLS["details_url"].format(**url_kwargs), allow_redirects=False)
        if response.status_code == 302:
            raise ValueError(f"Could not find ETF with {url_kwargs}")
        return cls(
            isin=url_kwargs["isin"].upper(),
            ticker=url_kwargs["query"].upper(),
            config=config,
            arguments=url_kwargs,
        )

    def _create_soup(self):
        opt = webdriver.ChromeOptions()
        opt.add_argument("--disable-gpu")
        opt.add_argument("--disable-extensions")
        opt.add_argument("--disable-infobars")
        opt.add_argument("--start-maximized")
        opt.add_argument("--disable-notifications")
        opt.add_argument("--headless")
        opt.add_argument("--no-sandbox")
        opt.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=opt)
        url = self.config.URLS["details_url"].format(**self.arguments)
        driver.get(url)
        wait = WebDriverWait(driver, 3)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "etf-data-table")))
        self.soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

    def _find_top_holdings(self):
        holdings = {}
        for tag in self.soup.find_all("div", {"class": "columns-2"}):
            company = tag.select("table.table.mb-0 tbody tr a span")
            companies = [row.get_text(strip=True) for row in company]
            if not len(companies):
                continue
            percentage = tag.select("table.table tbody tr div.right.ws span")
            percentages = [p.get_text(strip=True) for p in percentage]
            holdings = {k: v for k, v in zip(companies, percentages)}
        return holdings

    def _find_etf_details(self):
        details = {}
        table = self.soup.find("table", {"class": "table etf-data-table"})
        for tr in table.select("table tbody tr"):
            td_elements = tr.find_all("td")
            data = td_elements[0].get_text(strip=True).lower().replace(" ", "_")
            value = td_elements[1].get_text(strip=True)
            details[data] = value

        etf_profile_body_data = {}
        for div in self.soup.find_all("div", {"class": "d-flex d-flex-column"}):
            data = div.get_text("|", strip=True).split("|")[:2]
            etf_profile_body_data[data[0].strip().lower().replace(" ", "_")] = data[1]

        size_data = details["fund_size"].split(" ")[:2]
        dist_freq = details["distribution_frequency"]
        name = self.soup.find("h1", id="etf-title").get_text(strip=True)
        details_to_db = {
            "fund_size": int(float(size_data[1].replace(",", ".")) * 1e9),
            # "fund_size_currency": size_data[0],
            "fund_currency": details["fund_currency"],
            "fund_provider": details["fund_provider"],
            "distribution_policy": details["distribution_policy"],
            "distribution_frequency": dist_freq if dist_freq != "-" else None,
            "ter": float(details["total_expense_ratio"].split(" ")[0].replace("%", "")) * 1e-2,
            "volatility_1yr": float(details["volatility_1_year_(in_eur)"].replace("%", "")),
            "etf_ticker": self.ticker,
            "isin": self.isin,
            "name": name,
            "holdings": int(etf_profile_body_data["holdings"])
            if "holdings" in etf_profile_body_data
            else None,
            "replication": details["replication"],
        }

        return details_to_db

    def scrape(self) -> Dict[str, Any]:
        etf_details = self._find_etf_details()
        etf_details["top_holdings"] = self._find_top_holdings()
        return etf_details


# if __name__ == "__main__":
# response = get(
#     "https://www.justetf.com/en/etf-profile.html?query=xdwt&query=&groupField=index&from=search&isin=IE00BM67HT60"
# )
# soup = BeautifulSoup(response.content, "html.parser")
# print(soup.prettify())
# for c in soup.find_all("div", class_="d-flex d-flex-column", recursive=True):
# print(c.get_text("|", strip=True), end="\n\n")
# print(c)
