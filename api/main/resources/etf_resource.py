from api.main.database import ETF, ETFSchema
from api.main.flask_app import db
from api.main.common.util import create_etf_parser
from flask import abort
from flask_restful import Resource
from sqlalchemy import select, delete


class ETFResource(Resource):
    def __init__(self) -> None:
        self.schema = ETFSchema()
        self.parser = create_etf_parser()

    def get(self, ticker: str):
        etf = db.session.execute(select(ETF).where(ETF.etf_ticker == ticker)).first()
        if etf is None:
            abort(404, f"ETF with ticker '{ticker}' not found!")
        data = self.schema.dump(etf[0])
        return data, 200

    def post(self):
        request_data = self.parser.parse_args()
        new_etf = ETF(**request_data)
        db.session.add(new_etf)
        db.session.commit()
        return self.schema.dump(new_etf), 201

    def delete(self, ticker: str):
        etf = db.session.execute(select(ETF).where(ETF.etf_ticker == ticker)).first()
        if etf is None:
            abort(404, f"ETF with ticker '{ticker}' not found!")
        db.session.execute(delete(ETF).where(ETF.etf_ticker == ticker))
        db.session.commit()
        return "", 204
