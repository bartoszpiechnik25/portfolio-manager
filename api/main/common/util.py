from flask_restful import reqparse, fields

response_blueprint = {
    "code": fields.Integer,
    "generated_sequence": fields.List(fields.String),
    "tokenizer_warning": fields.String,
}


def create_sql_parser() -> reqparse.RequestParser:
    sql_parser = reqparse.RequestParser()
    sql_parser.add_argument("sql_table", type=str, required=True, help="Code generating SQL table.")
    sql_parser.add_argument(
        "question", type=str, required=True, help="Question regarding the SQL table."
    )
    sql_parser.add_argument(
        "num_return_sequences",
        type=int,
        required=False,
        default=1,
        help="Number of sequences to return. (To work properly do_sample=True!)",
    )
    sql_parser.add_argument(
        "temperature",
        type=float,
        required=False,
        default=1.0,
        help="Temperature for sampling logits. (Works only with do_sample=True)",
    )
    sql_parser.add_argument(
        "top_k", type=int, required=False, default=50, help="Top k probabilities to sample from."
    )
    sql_parser.add_argument(
        "do_sample",
        type=bool,
        required=False,
        default=False,
        help="Multinomial sampling from logits.",
    )
    sql_parser.add_argument(
        "max_new_tokens",
        type=int,
        required=False,
        default=200,
        help="Maximum number of tokens to generate.",
    )
    return sql_parser


def create_summary_request_parser() -> reqparse.RequestParser:
    summary_request_parser = reqparse.RequestParser()
    summary_request_parser.add_argument("text", type=str, required=True, help="Text to summarize.")
    summary_request_parser.add_argument(
        "num_return_sequences",
        type=int,
        required=False,
        default=1,
        help="Number of sequences to return. (To work properly do_sample=True!)",
    )
    summary_request_parser.add_argument(
        "temperature",
        type=float,
        required=False,
        default=1.0,
        help="Temperature for sampling logits. (Works only with do_sample=True)",
    )
    summary_request_parser.add_argument(
        "top_k", type=int, required=False, default=50, help="Top k probabilities to sample from."
    )
    summary_request_parser.add_argument(
        "do_sample",
        type=bool,
        required=False,
        default=False,
        help="Multinomial sampling from logits.",
    )
    summary_request_parser.add_argument(
        "max_new_tokens",
        type=int,
        required=False,
        default=512,
        help="Maximum number of tokens to generate.",
    )
    return summary_request_parser


def create_user_parser() -> reqparse.RequestParser:
    user_parser = reqparse.RequestParser()
    user_parser.add_argument("username", type=str, required=True, help="Username.")
    user_parser.add_argument("email", type=str, required=True, help="Email.")
    user_parser.add_argument("password", type=str, required=True, help="Password.")
    user_parser.add_argument("name", type=str, required=False, help="Name.")
    user_parser.add_argument("surname", type=str, required=False, help="Surname.")
    return user_parser


def create_etf_parser() -> reqparse.RequestParser:
    etf_parser = reqparse.RequestParser()
    etf_parser.add_argument("etf_ticker", type=str, required=True, help="ETF ticker.")
    etf_parser.add_argument("name", type=str, required=True, help="ETF name.")
    etf_parser.add_argument("currency_code", type=str, required=True, help="ETF currency code.")
    etf_parser.add_argument("google_ticker", type=str, required=True, help="ETF google ticker.")
    etf_parser.add_argument("isin", type=str, required=True, help="ETF ISIN.")
    etf_parser.add_argument("ter", type=float, required=True, help="ETF TER.")
    etf_parser.add_argument(
        "distribution",
        type=str,
        required=True,
        help="ETF distribution.(Accumulating | Distributing)",
    )
    etf_parser.add_argument(
        "replication_method",
        type=str,
        required=True,
        help="ETF replication method.(Physical | Synthetic | Physical(Sampling))",
    )
    etf_parser.add_argument("fund_size", type=float, required=False, help="ETF fund size.")
    etf_parser.add_argument("holdings", type=int, required=False, help="ETF holdings.")
    etf_parser.add_argument(
        "top_holdings", type=list, required=False, help="ETF top holdings.", location="json"
    )

    return etf_parser


def create_stock_parser() -> reqparse.RequestParser:
    parser = reqparse.RequestParser()
    parser.add_argument(
        "stock_ticker", type=str, required=True, help="Stock ticker must be provided!"
    )
    parser.add_argument(
        "name", type=str, required=True, help="Name of the company must be provided!"
    )
    parser.add_argument("currency_code", type=str, required=True, help="Stock currency code")
    parser.add_argument(
        "google_ticker",
        type=str,
        required=True,
        help="Stock google ticker to be used in Google Finance",
    )
    parser.add_argument("isin", type=str, required=True, help="Stock ISIN must be provided")
    parser.add_argument(
        "dividend_yield", type=float, required=True, help="Stock dividend yield must be provided"
    )
    return parser


def create_invest_parser() -> reqparse.RequestParser:
    invest_etf_parser = reqparse.RequestParser()
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
        "last_known_price",
        type=float,
        required=False,
        help="Last known price otherwise None is used",
    )
    return invest_etf_parser


def create_invest_etf_parser() -> reqparse.RequestParser:
    parser = create_invest_parser()
    parser.add_argument("etf_ticker", type=str, required=True, help="ETF ticker is required")
    return parser


def create_invest_stock_parser() -> reqparse.RequestParser:
    parser = create_invest_parser()
    parser.add_argument("stock_ticker", type=str, required=True, help="Stock ticker is required")
    return parser


def create_users():
    return [
        {
            "username": "johndoe",
            "password": "password123",
            "email": "johndoe@example.com",
            "name": "John",
            "surname": "Doe",
        },
        {
            "username": "janedoe",
            "password": "password456",
            "email": "janedoe@example.com",
            "name": "Jane",
            "surname": "Doe",
        },
        {
            "username": "bobsmith",
            "password": "password789",
            "email": "bobsmith@example.com",
            "name": "Bob",
            "surname": "Smith",
        },
        {
            "username": "sarahjones",
            "password": "password123",
            "email": "sarahjones@example.com",
            "name": "Sarah",
            "surname": "Jones",
        },
        {
            "username": "mikebrown",
            "password": "password456",
            "email": "mikebrown@example.com",
            "name": "Mike",
            "surname": "Brown",
        },
    ]


def create_currencies():
    return [
        {"name": "US Dollar", "currency_code": "USD"},
        {"name": "Euro", "currency_code": "EUR"},
        {"name": "British Pound", "currency_code": "GBP"},
        {"name": "Japanese Yen", "currency_code": "JPY"},
        {"name": "Canadian Dollar", "currency_code": "CAD"},
        {"name": "Swiss Franc", "currency_code": "CHF"},
        {"name": "Polish Zloty", "currency_code": "PLN"},
    ]


def create_etfs():
    return [
        {
            "currency_code": "USD",
            "name": "Vanguard Total Stock Market ETF",
            "etf_ticker": "VTI",
            "google_ticker": "NYSEARCA:VTI",
            "isin": "US9229087690",
            "ter": 0.03,
            "distribution_policy": "Accumulating",
            "replication": "Full replication",
            "fund_size": 20000000000,
            "holdings": 3500,
            "top_holdings": [
                {"name": "Apple Inc.", "ticker": "AAPL", "weight": 6.5},
                {"name": "Microsoft Corporation", "ticker": "MSFT", "weight": 5.0},
                {"name": "Amazon.com, Inc.", "ticker": "AMZN", "weight": 4.0},
                {"name": "Facebook, Inc.", "ticker": "FB", "weight": 2.5},
                {"name": "Alphabet Inc.", "ticker": "GOOGL", "weight": 2.0},
            ],
        },
        {
            "currency_code": "EUR",
            "name": "iShares Core MSCI World UCITS ETF",
            "etf_ticker": "IWDA",
            "google_ticker": "AMS:IWDA",
            "isin": "IE00B4L5Y983",
            "ter": 0.20,
            "distribution_policy": "Accumulating",
            "replication": "Sampling",
            "fund_size": 5000000000,
            "holdings": 1600,
            "top_holdings": [
                {"name": "Apple Inc.", "ticker": "AAPL", "weight": 2.5},
                {"name": "Microsoft Corporation", "ticker": "MSFT", "weight": 1.8},
                {"name": "Amazon.com, Inc.", "ticker": "AMZN", "weight": 1.5},
                {"name": "Facebook, Inc.", "ticker": "FB", "weight": 1.2},
                {"name": "Alphabet Inc.", "ticker": "GOOGL", "weight": 1.0},
            ],
        },
        {
            "currency_code": "GBP",
            "name": "Vanguard FTSE 100 UCITS ETF",
            "etf_ticker": "VUKE",
            "google_ticker": "LON:VUKE",
            "isin": "IE00B810Q511",
            "ter": 0.09,
            "distribution_policy": "Distributing",
            "replication": "Full replication",
            "fund_size": 1000000000,
            "holdings": 100,
            "top_holdings": [
                {"name": "HSBC Holdings plc", "ticker": "HSBA", "weight": 6.5},
                {"name": "BP plc", "ticker": "BP", "weight": 5.0},
                {"name": "Royal Dutch Shell plc", "ticker": "RDSB", "weight": 4.0},
                {"name": "AstraZeneca plc", "ticker": "AZN", "weight": 2.5},
                {"name": "Diageo plc", "ticker": "DGE", "weight": 2.0},
            ],
        },
    ]


def create_stocks_data():
    return [
        {
            "stock_ticker": "AMZN",
            "currency_code": "USD",
            "name": "Amazon.com, Inc.",
            "google_ticker": "NASDAQ:AMZN",
            "isin": "US0231351067",
            "dividend_yield": 0.00,
        },
        {
            "stock_ticker": "GOOGL",
            "currency_code": "USD",
            "name": "Alphabet Inc.",
            "google_ticker": "NASDAQ:GOOGL",
            "isin": "US02079K3059",
            "dividend_yield": 0.00,
        },
        {
            "stock_ticker": "TSLA",
            "currency_code": "USD",
            "name": "Tesla, Inc.",
            "google_ticker": "NASDAQ:TSLA",
            "isin": "US88160R1014",
            "dividend_yield": 0.00,
        },
        {
            "stock_ticker": "AAPL",
            "currency_code": "USD",
            "name": "Apple Inc.",
            "google_ticker": "NASDAQ:AAPL",
            "isin": "US0378331005",
            "dividend_yield": 0.60,
        },
    ]


def create_etf_investment_data():
    return [
        {
            "username": "johndoe",
            "etf_ticker": "VTI",
            "volume": 100,
            "open_price": 100.0,
            "last_known_price": 110.0,
        },
        {
            "username": "johndoe",
            "etf_ticker": "IWDA",
            "volume": 3,
            "open_price": 85.34,
            "last_known_price": 90.0,
        },
        {
            "username": "janedoe",
            "etf_ticker": "VUKE",
            "volume": 10,
            "open_price": 50.0,
            "last_known_price": 45.0,
        },
        # {
        #     "username": "bobsmith",
        #     "etf_ticker": "VTI",
        #     "volume": 42,
        #     "open_price": 123.45,
        #     "last_known_price": 130.0,
        # },
        {
            "username": "sarahjones",
            "etf_ticker": "IWDA",
            "volume": 1,
            "open_price": 85.34,
            "last_known_price": 80.0,
        },
        {
            "username": "mikebrown",
            "etf_ticker": "VUKE",
            "volume": 100,
            "open_price": 50.0,
            "last_known_price": 55.0,
            "close_price": 90.23,
            "close_datetime": "2024-03-07",
        },
    ]


def create_stock_investments_data():
    return [
        {
            "username": "johndoe",
            "stock_ticker": "AMZN",
            "volume": 10,
            "open_price": 100.0,
            "last_known_price": 110.0,
        },
        {
            "username": "mikebrown",
            "stock_ticker": "GOOGL",
            "volume": 3,
            "open_price": 85.34,
            "last_known_price": 90.0,
        },
        {
            "username": "janedoe",
            "stock_ticker": "TSLA",
            "volume": 14,
            "open_price": 50.0,
        },
    ]
