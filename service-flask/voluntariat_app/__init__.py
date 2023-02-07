from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from .plugin_hashid import HashidManager
from .plugin_tasks import TaskManager
from .plugin_gmail import GmailManager
from .plugin_excel import ExcelManager
from .plugin_params import ParamsManager
from .plugin_usher import UsherManager

db = SQLAlchemy()
login_manager = LoginManager()
params_manager = ParamsManager()
hashid_manager = HashidManager()
task_manager = TaskManager()
gmail_manager = GmailManager()
excel_manager = ExcelManager()
usher_manager = UsherManager()

def create_app():
    """Construct the core app object."""
    app = Flask(__name__, instance_relative_config=False)

    app.url_map.strict_slashes = False #https://stackoverflow.com/a/33285603
    app.config.from_object("config.Config")

    app.logger.info("Voluntariat APP is starting!")

    # Initialize Plugins
    db.init_app(app)
    params_manager.init_app(app)
    login_manager.init_app(app)
    hashid_manager.init_app(app)
    task_manager.init_app(app)
    gmail_manager.init_app(app)
    excel_manager.init_app(app)
    usher_manager.init_app(app, db)

    with app.app_context():
        from . import routes_main, routes_auth, routes_admin, routes_volunteer

        # Register Blueprints
        app.register_blueprint(routes_main.main_bp)
        app.register_blueprint(routes_auth.auth_bp)
        app.register_blueprint(routes_admin.admin_bp)
        app.register_blueprint(routes_volunteer.volunteer_bp)

        # Create Database Models
        db.create_all()

        return app