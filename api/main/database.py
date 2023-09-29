from api.main import db, ma, bcrypt
from typing import List, Dict
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin
from flask import current_app
from itsdangerous import TimestampSigner, BadSignature, BadTimeSignature

FIELDS = [
    "username",
    "password",
    "email",
    "name",
    "surname",
]


class Users(UserMixin, db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=True, default=None)
    surname = db.Column(db.String(255), nullable=True, default=None)
    confirmed = db.Column(db.Boolean, nullable=False, default=False)
    investment = db.relationship("Investments", back_populates="user_fk")

    def __repr__(self) -> str:
        return "User(id={}, username={}, email={}, name={}, surname={})".format(
            self.user_id, self.username, self.email, self.name, self.surname
        )

    def get_id(self):
        return str(self.user_id)

    def generate_confirmation_token(self):
        s = TimestampSigner(current_app.config["SECRET_KEY"])
        return s.sign(self.get_id()).decode("utf-8")

    def confirm(self, token: str):
        s = TimestampSigner(current_app.config["SECRET_KEY"])
        try:
            data = s.unsign(token, max_age=3600).decode("utf-8")
        except (BadTimeSignature, BadSignature):
            return False
        if data != self.get_id():
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute!")

    @password.setter
    def password(self, paswd):
        self.password_hash = bcrypt.generate_password_hash(paswd).decode("utf-8")

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

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
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"))
    type = db.Column(db.String(40), nullable=False)
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
        if self.close_price:
            return (self.close_price - self.open_price) * self.volume
        elif self.last_known_price and self.close_price is None:
            return (self.last_known_price - self.open_price) * self.volume
        return None

    @hybrid_property
    def duration(self):
        if self.close_datetime is None:
            return None
        return self.close_datetime - self.open_datetime

    @hybrid_property
    def market_value(self):
        if self.last_known_price is None:
            return None
        return self.last_known_price * self.volume

    __mapper_args__ = {"polymorphic_on": "type"}


class ETF(db.Model):
    __tablename__ = "etfs"
    etf_ticker = db.Column(db.String(5), nullable=False, primary_key=True)
    currency_code = db.Column(db.String, db.ForeignKey("currencies.currency_code"), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    google_ticker = db.Column(db.String(20), nullable=False)
    isin = db.Column(db.String(12), nullable=False, unique=True)
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

    stock_ticker = db.Column(db.ForeignKey("stocks.stock_ticker"))
    stock_fk = db.relationship("Stock", back_populates="user_stocks")

    __mapper_args__ = {
        "polymorphic_identity": "stocks",
    }


class InvestedETFs(Investments):
    __tablename__ = "invested_etfs"
    investment_id = db.Column(
        db.Integer, db.ForeignKey("investments.investment_id"), primary_key=True
    )

    etf_ticker = db.Column(db.ForeignKey("etfs.etf_ticker"))
    etf_fk = db.relationship("ETF", back_populates="user_etfs")

    __mapper_args__ = {"polymorphic_identity": "etfs"}


class ETFSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ETF
        load_instance = True
        include_fk = True

    ter = ma.Float(places=2)
    fund_size = ma.Float(places=2, allow_none=True)


class UsersSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Users
        load_instance = True
        include_fk = True
        exclude = ("password_hash", "user_id")


class StocksSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Stock
        load_instance = True

    dividend_yield = ma.Float(places=2)


class InvestmentsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Investments

    investment_id = ma.auto_field(dump_only=True)
    type = ma.Str(load_only=True)
    open_datetime = ma.auto_field(dump_only=True, allow_none=True)
    volume = ma.Float(places=2)
    open_price = ma.Float(places=2)
    close_price = ma.Float(places=2, allow_none=True)
    last_known_price = ma.Float(places=2, allow_none=True)
    market_value = ma.Float(places=2, dump_only=True, allow_none=True)
    profit = ma.Float(places=2, dump_only=True, allow_none=True)
    duration = ma.TimeDelta(precision="hours", dump_only=True, allow_none=True)


class InvestedStocksSchema(InvestmentsSchema):
    class Meta:
        model = InvestedStocks
        include_fk = True


class InvestedETFsSchema(InvestmentsSchema):
    class Meta:
        model = InvestedETFs
        include_fk = True
