from api.main.database import ETF, ETFSchema
from api.main.flask_app import db
from api.main.common.util import create_etf_parser
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


class ETFResource(Resource):
    def __init__(self) -> None:
        self.schema = ETFSchema()
        self.parser = create_etf_parser()

    def get(self):
        args = request.args
        if not len(args):
            abort(400, "No arguments provided!")
        if "ticker" in args or "isin" in args:
            abort(400, "Use /api/v1/etf/(isin|ticker) to search for specific ETFs")
        print(request.args.to_dict())

    def post(self):
        request_data = self.parser.parse_args()
        new_etf = self.schema.load(request_data, transient=True)
        db.session.add(new_etf)
        db.session.commit()
        return self.schema.dump(new_etf), 201


class ETFsResource(Resource):
    def get(self):
        etfs = db.session.execute(select(ETF)).all()
        print(request.args)
        if etfs is None:
            abort(404, "ETFs not found!")
        return [ETFSchema().dump(etf[0]) for etf in etfs], 200


class ETFIdentifierRouteResource(Resource):
    def get(self, identifier: str):
        etf = self.find_etf(identifier)
        return ETFSchema().dump(etf[0]), 200

    def delete(self, identifier: str):
        etf = self.find_etf(identifier)
        db.session.delete(etf[0])
        db.session.commit()
        return "", 204

    def find_etf(self, identifier: str) -> Union[ETF, None]:
        self.attr_name = (
            "etf_ticker"
            if len(identifier) <= 5
            else abort(400, "Invalid identifier!")
            if len(identifier) > 12
            else "isin"
        )
        etf = db.session.execute(
            select(ETF).where(getattr(ETF, self.attr_name) == identifier)
        ).one_or_none()
        if etf is None:
            abort(404, f"ETF with {self.attr_name.split('_')[-1]} '{identifier}' not found!")
        return etf
