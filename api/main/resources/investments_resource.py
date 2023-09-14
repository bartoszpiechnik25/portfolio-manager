from api.main.database import InvestedETFs, InvestedETFsSchema
from api.main.flask_app import db
from sqlalchemy import insert, select
from flask_restful import Resource, reqparse

invest_etf_parser = reqparse.RequestParser()
invest_etf_parser.add_argument("etf_ticker", type=str, required=True, help="ETF ticker is required")
invest_etf_parser.add_argument("username", type=str, required=True, help="Username is required")
invest_etf_parser.add_argument("volume", type=float, required=True, help="Volume is required")
invest_etf_parser.add_argument(
    "open_price", type=float, required=True, help="Open price is required"
)
invest_etf_parser.add_argument(
    "open_datetime", type=str, required=False, help="Open datetime otherwise now() is used"
)
invest_etf_parser.add_argument(
    "close_datetime", type=str, required=False, help="Close datetime otherwise None is used"
)
invest_etf_parser.add_argument(
    "close_price", type=float, required=False, help="Close price otherwise None is used"
)
invest_etf_parser.add_argument(
    "last_known_price", type=float, required=False, help="Last known price otherwise None is used"
)


class UserInvestedETFsResource(Resource):
    def get(self):
        etf = db.session.execute(select(InvestedETFs)).all()
        sch = InvestedETFsSchema()
        return [sch.dump(e[0]) for e in etf], 200

    def post(self):
        args = invest_etf_parser.parse_args()
        db.session.execute(insert(InvestedETFs), [args])
        db.session.commit()
        return args, 201
