from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    from config import config
    app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        import database.models  # ensure all models are registered before create_all
        db.create_all()
