from api.main.database import (
    ETF,
    ETFSchema,
    Stock,
    StocksSchema,
    ASSET_TYPE_MAPPING,
    TYPE_TO_TICKER_MAPPING,
)
from api.main import db
from flask import abort, request
from flask_restful import Resource
from sqlalchemy import select
from typing import Union


def map_str_to_math_operator(operator: str, attr_name: str, val2: Union[int, float]):
    column = getattr(ETF, attr_name)
    mapper = {
        "eq": column == val2,
        "ne": column != val2,
        "lt": column < val2,
        "le": column <= val2,
        "gt": column > val2,
        "ge": column >= val2,
    }
    if operator not in mapper:
        abort(400, f"Incorrect operator: {operator}!")
    return mapper[operator]


class Asset(Resource):
    def get(self, investment_type: str):
        if investment_type not in ASSET_TYPE_MAPPING:
            abort(400, f"Type '{investment_type}' not supported!")

        args = request.args
        if not len(args):
            abort(400, "No arguments provided!")
        if "ticker" in args:
            attr = args["ticker"]
            if len(attr) > 5:
                abort(400, "Ticker must be less than 6 characters long!")
        elif "isin" in args:
            attr = args["isin"]
            if len(attr) != 12:
                abort(400, "ISIN must be 12 characters long!")
        elif "isin" in args and "ticker" in args:
            abort(400, "Provide only one argument! Either 'isin' or 'ticker'!")
        else:
            abort(400, f"Provide one of the following arguments: {', '.join(args.keys())}!")

        asset = find_financial_assets(attr, investment_type)

        return ASSET_TYPE_MAPPING[investment_type]["schema"]().dump(asset), 200

    def post(self, investment_type: str):
        if investment_type not in ASSET_TYPE_MAPPING:
            abort(400, f"Type '{investment_type}' not supported!")

        schema: Union[ETFSchema, StocksSchema] = ASSET_TYPE_MAPPING[investment_type]["schema"]()
        request_data = ASSET_TYPE_MAPPING[investment_type]["parser"]().parse_args()

        new_asset = schema.load(request_data, transient=True)
        db.session.add(new_asset)
        db.session.commit()
        return schema.dump(new_asset), 201


class Assets(Resource):
    def get(self, investment_type: str):
        if investment_type not in ASSET_TYPE_MAPPING:
            abort(400, f"Type '{investment_type}' not supported!")

        cls: Union[ETF, Stock] = ASSET_TYPE_MAPPING[investment_type]["class"]
        schema: Union[ETFSchema, StocksSchema] = ASSET_TYPE_MAPPING[investment_type]["schema"]()

        assets = db.session.scalars(select(cls)).all()
        if assets is None:
            abort(404, f"{cls.__name__} not found!")
        return [schema.dump(asset) for asset in assets], 200


def find_financial_assets(identifier: str, type: str) -> Union[ETF, Stock, None]:
    attr_name = (
        TYPE_TO_TICKER_MAPPING[type]
        if len(identifier) <= 5
        else abort(400, "Invalid identifier!")
        if len(identifier) > 12
        else "isin"
    )
    cls = ASSET_TYPE_MAPPING[type]["class"]

    security = db.session.scalars(
        select(cls).where(getattr(cls, attr_name) == identifier)
    ).one_or_none()

    if security is None:
        abort(404, f"{cls.__name__} with {attr_name.split('_')[-1]} '{identifier}' not found!")
    return security
