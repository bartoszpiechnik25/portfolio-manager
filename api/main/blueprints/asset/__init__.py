from api.main.database import ASSET_TYPE_MAPPING, AssetTypes, ETFReplicationMethods
from api.main import db
from flask import Blueprint, render_template, redirect, url_for, flash
from api.main.blueprints.forms import AddAssetForm
from api.main.asset_scraper.scrapers import ASSET_TYPE_TO_SCRAPER_CLASS, ScraperConfig
from flask_marshmallow.sqla import SQLAlchemyAutoSchema
from sqlalchemy import select
from flask_login import login_required

asset = Blueprint("asset", __name__, url_prefix="/asset")


@asset.route("/add", methods=["GET", "POST"])
@login_required
def add_asset():
    form = AddAssetForm()
    if form.is_submitted():
        form.validate_on_submit()
        # flask-form returns from drop down list string
        # so its necessary to convert it to int to create AssetTypes enum instance.
        asset_type = AssetTypes(int(form.data["asset_type"]))
        try:
            asset_scraper = ASSET_TYPE_TO_SCRAPER_CLASS[asset_type].check_if_exists(
                ScraperConfig(asset_type), isin=form.data["isin"], query=form.data["ticker"]
            )
        except ValueError:
            isin, ticker = form.data["isin"], form.data["ticker"]
            flash(
                f"{asset_type.name} with ISIN: {isin}, ticker: {ticker}" + " does not exists!",
                "error",
            )
            form.isin.data = None
            form.ticker.data = None
            return render_template("add_asset.html", form=form)

        # asset_class = ASSET_TYPE_MAPPING[asset_type]["class"]
        asset_schema: SQLAlchemyAutoSchema = ASSET_TYPE_MAPPING[asset_type]["schema"]()

        asset_details = asset_scraper.scrape()
        replication = asset_details.pop("replication")
        asset_details["replication_method_id"] = db.session.scalar(
            select(ETFReplicationMethods.replication_method_id).where(
                ETFReplicationMethods.replication_method == replication
            )
        )

        if asset_details["replication_method_id"] is None:
            flash(f"Replication method {replication} does not exist in the database!", "error")
            return render_template("add_asset.html", form=form)

        new_asset = asset_schema.load(asset_details, transient=True)
        db.session.add(new_asset)
        db.session.commit()
        return redirect(url_for("index.profile"))

    return render_template("add_asset.html", form=form)
