import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# database
db = SQLAlchemy()
DEFAULT_DB_PATH = "instance/database.db"

# creates flask application
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-fallback')
    # DATABASE_PATH lets production point at a persistent volume (e.g. /data/database.db)
    db_path = os.path.abspath(os.environ.get('DATABASE_PATH', DEFAULT_DB_PATH))
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # cache static assets for 1 year
    db.init_app(app) # initializes database with app

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Party

    with app.app_context():
        db.create_all() # creates database for the app
        from .seed import seed_cocktails_if_empty
        seed_cocktails_if_empty() # fills cocktail table on a fresh database

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app

