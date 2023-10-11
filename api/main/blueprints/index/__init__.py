from flask import Blueprint, render_template
from flask_login import current_user, login_required
from api.main.asset_scraper.scrapers import ETFScraper
from api.main.asset_scraper import AssetTypes, ScraperConfig
from api.main.database import ETFSchema, ETFReplicationMethods
from sqlalchemy import select
from api.main import db


index = Blueprint("index", __name__, url_prefix="/")


@index.route("/", methods=["GET"])
def index_page():
    user_name = None
    etf_scraper = ETFScraper.check_if_exists(
        ScraperConfig(AssetTypes.ETF), query="spxs", isin="IE00B3YCGJ38"
    )
    data = etf_scraper.scrape()
    replication_method = data.pop("replication")
    data["replication_method_id"] = db.session.scalar(
        select(ETFReplicationMethods.replication_method_id).where(
            ETFReplicationMethods.replication_method == replication_method
        )
    )
    etf = ETFSchema().load(data, transient=True)
    db.session.add(etf)
    db.session.commit()
    print(ETFSchema().dump(etf))

    if current_user.is_authenticated:
        user_name = current_user.username
    return render_template("index.html", user_name=user_name), 200


@index.route("/profile", methods=["GET"])
@login_required
def profile():
    if not current_user.confirmed:
        return render_template("unconfirmed.html")
    return render_template("profile.html", user=current_user), 200
