from api.main.flask_app import db, ma
from typing import List, Dict
from sqlalchemy.ext.hybrid import hybrid_property

FIELDS = [
    "username",
    "password",
    "email",
    "name",
    "surname",
]


class Users(db.Model):
    __tablename__ = "users"
    username = db.Column(db.String(40), primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=True, default=None)
    surname = db.Column(db.String(255), nullable=True, default=None)
    investment = db.relationship("Investments", back_populates="user_fk")

    def __repr__(self) -> str:
        return "User(id={}, username={}, password={}, email={}, name={}, surname={})".format(
            self.user_id, self.username, self.password, self.email, self.name, self.surname
        )

    @staticmethod
    def required_fields_in_request_body(args: dict) -> bool:
        fields = ["username", "email", "password"]
        return all(field in args for field in fields)

    @staticmethod
    def valid_field_in_request_body(args: Dict[str, str], fields: List[str] = FIELDS) -> bool:
        return all(arg in fields for arg in args)


class Currency(db.Model):
    __tablename__ = "currencies"
    currency_code = db.Column(db.String(3), nullable=False, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    etf = db.relationship("ETF", back_populates="currency")
    stock = db.relationship("Stock", back_populates="currency")


class Investments(db.Model):
    __tablename__ = "investments"
    investment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(40), db.ForeignKey("users.username"))
    volume = db.Column(db.Numeric(9, 2), nullable=False)
    open_price = db.Column(db.Numeric(9, 2), nullable=False)
    open_datetime = db.Column(
        db.TIMESTAMP(timezone=False), nullable=False, server_default=db.func.now()
    )
    close_datetime = db.Column(db.TIMESTAMP(timezone=False), nullable=True)
    close_price = db.Column(db.Numeric(9, 2), nullable=True)
    last_known_price = db.Column(db.Numeric(9, 2), nullable=True)

    user_fk = db.relationship("Users", back_populates="investment")

    @hybrid_property
    def profit(self):
        if self.last_known_market_value is None:
            return None
        return self.last_known_market_value - self.open_price

    @hybrid_property
    def duration(self):
        if self.close_datetime is None:
            return None
        return self.close_datetime - self.open_datetime

    @hybrid_property
    def market_value(self):
        if self.close_price is None:
            return None
        return self.close_price * self.volume

    __mapper_arg__ = {"polymorphic_identity": "investment", "polymorphic on": volume}


class ETF(db.Model):
    __tablename__ = "etfs"
    etf_ticker = db.Column(db.String(5), nullable=False, unique=True, primary_key=True)
    currency_code = db.Column(db.String, db.ForeignKey("currencies.currency_code"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    google_ticker = db.Column(db.String(20), nullable=False)
    isin = db.Column(db.String(12), nullable=False)
    ter = db.Column(db.Numeric(2, 2), nullable=False)
    distribution = db.Column(
        db.Enum("Accumulating", "Distributing", name="distribution"), nullable=False
    )
    replication_method = db.Column(
        db.Enum("Physical", "Synthetic", "Physical(Sampling)", name="replication_method"),
        nullable=False,
    )
    fund_size = db.Column(db.Numeric(20, 2), nullable=True)
    holdings = db.Column(db.Integer, nullable=True)
    top_holdings = db.Column(db.JSON, nullable=True)
    currency = db.relationship("Currency", back_populates="etf")
    user_etfs = db.relationship("InvestedETFs", back_populates="etf_fk")


class Stock(db.Model):
    __tablename__ = "stocks"
    stock_ticker = db.Column(db.String(5), nullable=False, primary_key=True)
    currency_code = db.Column(db.String, db.ForeignKey("currencies.currency_code"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    google_ticker = db.Column(db.String(20), nullable=False)
    isin = db.Column(db.String(12), nullable=False)
    dividend_yield = db.Column(db.Numeric(2, 2), nullable=False)
    currency = db.relationship("Currency", back_populates="stock")
    user_stocks = db.relationship("InvestedStocks", back_populates="stock_fk")


class InvestedStocks(Investments):
    __tablename__ = "invested_stocks"
    investment_id = db.Column(
        db.Integer, db.ForeignKey("investments.investment_id"), primary_key=True
    )
    stock_ticker = db.Column(db.String(5), db.ForeignKey("stocks.stock_ticker"))
    stock_fk = db.relationship("Stock", back_populates="user_stocks")

    __mapper_arg__ = {
        "polymorphic_identity": "invested_stocks",
    }


class InvestedETFs(Investments):
    __tablename__ = "invested_etfs"

    investment_id = db.Column(
        db.Integer, db.ForeignKey("investments.investment_id"), primary_key=True
    )

    etf_ticker = db.Column(db.String(5), db.ForeignKey("etfs.etf_ticker"))
    etf_fk = db.relationship("ETF", back_populates="user_etfs")

    __mapper_arg__ = {"polymorphic_identity": "invested_etfs"}


class ETFSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ETF
        include_fk = True

    ter = ma.Float(places=2)
    fund_size = ma.Float(places=2, allow_none=True)


class UsersSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Users
        include_fk = True

    password = ma.String(load_only=True)
