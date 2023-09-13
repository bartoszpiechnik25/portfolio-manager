import uuid
from api.main.flask_app import db, ma
from typing import List, Dict

FIELDS = [
    "username",
    "password",
    "email",
    "name",
    "surname",
]


class Users(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True, default=None)
    surname = db.Column(db.String(255), nullable=True, default=None)
    etfs = db.relationship("UsersETFs", back_populates="user")
    stocks = db.relationship("UsersStocks", back_populates="user")

    def __repr__(self) -> str:
        return "User(id={}, username={}, password={}, email={}, name={}, surname={})".format(
            self.user_id, self.username, self.password, self.email, self.name, self.surname
        )

    def serialize(self):
        return {
            "user_id": str(self.user_id),
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "name": self.name,
            "surname": self.surname,
        }

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


class Investment(db.Model):
    __tablename__ = "investments"
    investment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    volume = db.Column(db.Numeric(9, 2), nullable=False)
    price = db.Column(db.Numeric(9, 2), nullable=False)
    date = db.Column(db.Date, nullable=False)
    users_etfs = db.relationship("UsersETFs", back_populates="investment")
    users_stocks = db.relationship("UsersStocks", back_populates="investment")


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
    users_etfs = db.relationship("UsersETFs", back_populates="etf")


class UsersETFs(db.Model):
    __tablename__ = "users_etfs"
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.user_id"), primary_key=True)
    etf_ticker = db.Column(db.String(5), db.ForeignKey("etfs.etf_ticker"), primary_key=True)
    investment_id = db.Column(
        db.Integer, db.ForeignKey("investments.investment_id"), primary_key=True
    )
    user = db.relationship("Users", back_populates="etfs")
    etf = db.relationship("ETF", back_populates="users_etfs")
    investment = db.relationship("Investment", back_populates="users_etfs")


class Stock(db.Model):
    __tablename__ = "stocks"
    stock_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    currency_code = db.Column(db.String, db.ForeignKey("currencies.currency_code"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    google_ticker = db.Column(db.String(20), nullable=False)
    isin = db.Column(db.String(12), nullable=False)
    dividend_yield = db.Column(db.Numeric(2, 2), nullable=False)
    users_stocks = db.relationship("UsersStocks", back_populates="stock")


class UsersStocks(db.Model):
    __tablename__ = "users_stocks"
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey("users.user_id"), primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey("stocks.stock_id"), primary_key=True)
    investment_id = db.Column(
        db.Integer, db.ForeignKey("investments.investment_id"), primary_key=True
    )
    user = db.relationship("Users", back_populates="stocks")
    stock = db.relationship("Stock", back_populates="users_stocks")
    investment = db.relationship("Investment", back_populates="users_stocks")


class ETFSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ETF
        include_fk = True

    ter = ma.Float(places=2)
    fund_size = ma.Float(places=2, allow_none=True)
