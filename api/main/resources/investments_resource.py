from api.main.database import (
    InvestedETFs,
    InvestedETFsSchema,
    InvestedStocks,
    InvestedStocksSchema,
    Investments,
    InvestmentsSchema,
)
from api.main import db
from sqlalchemy import select, insert
from flask import abort, request
from flask_restful import Resource
from api.main.database import Users
from typing import Dict, Any
from api.main.common.util import create_invest_etf_parser, create_invest_stock_parser
from api.main.resources.asset_resource import find_financial_assets, TYPE_TO_TICKER_MAPPING


MAPPINGS: Dict[str, Dict[str, Any]] = {
    "etfs": {
        "schema": InvestedETFsSchema,
        "class": InvestedETFs,
        "parser": create_invest_etf_parser,
    },
    "stocks": {
        "schema": InvestedStocksSchema,
        "class": InvestedStocks,
        "parser": create_invest_stock_parser,
    },
    "all": {"class": Investments, "schema": InvestmentsSchema},
}


class UserInvestedAssets(Resource):
    def get(self, username: str):
        user = db.session.scalars(select(Users).where(Users.username == username)).one_or_none()

        if user is None:
            abort(400, f"User '{username}' not found in the database!")

        args = request.args.to_dict()
        investment_type = args["type"] if "type" in args else "all"

        if investment_type in MAPPINGS:
            cls = MAPPINGS[investment_type]["class"]
            investments = db.session.scalars(select(cls).where(cls.username == username)).all()
        else:
            abort(400, f"Type '{args['type']}' not supported!")

        if not len(investments):
            abort(
                404,
                f"User '{username}' did not invest in any"
                + f" {investment_type.upper() if investment_type != 'all' else 'securities'}!",
            )

        return [MAPPINGS[investment.type].dump(investment) for investment in investments], 200


class Invest(Resource):
    def post(self, username: str, investment_type: str):
        user = db.session.execute(select(Users).where(Users.username == username)).first()
        if not user:
            abort(400, f"User '{username}' not found in the database!")

        if investment_type not in MAPPINGS:
            abort(400, f"Type '{investment_type}' not supported!")

        args = MAPPINGS[investment_type]["parser"]().parse_args()
        args["username"] = username

        asset = find_financial_assets(
            args[TYPE_TO_TICKER_MAPPING[investment_type]], investment_type
        )

        if not asset:
            abort(400, f"Security '{args[TYPE_TO_TICKER_MAPPING[investment_type]]}' not found!")

        cls = MAPPINGS[investment_type]["class"]
        inserted = db.session.scalars(insert(cls).returning(cls), [args]).first()
        result = MAPPINGS[investment_type]["schema"]().dump(inserted)

        db.session.commit()
        return result, 200
