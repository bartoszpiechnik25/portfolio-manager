from api.main.flask_app import create_app, db_init

app, api = create_app(db_only=True)
db_init(app, api)
