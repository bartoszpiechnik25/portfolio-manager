from flask_restful import reqparse, fields

t5_sql_response = {"code": fields.Integer, "generated_text": fields.List(fields.String)}


def create_sql_parser() -> reqparse.RequestParser:
    sql_parser = reqparse.RequestParser()
    sql_parser.add_argument("text", type=str, required=True)
    sql_parser.add_argument("num_return_sequences", type=int, required=False, default=1)
    sql_parser.add_argument("temperature", type=float, required=False, default=1.0)
    sql_parser.add_argument("top_k", type=int, required=False, default=50)
    sql_parser.add_argument("do_sample", type=bool, required=False, default=False)
    sql_parser.add_argument("max_new_tokens", type=int, required=False, default=200)
    return sql_parser
