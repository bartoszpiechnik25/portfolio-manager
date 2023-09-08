from flask_restful import reqparse, fields

response_blueprint = {
    "status_code": fields.Integer,
    "generated_sequence": fields.List(fields.String),
    "tokenizer_warning": fields.String,
}


def create_sql_parser() -> reqparse.RequestParser:
    sql_parser = reqparse.RequestParser(bundle_errors=True)
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


def create_summary_request_parser():
    summary_request_parser = reqparse.RequestParser(bundle_errors=True)
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
