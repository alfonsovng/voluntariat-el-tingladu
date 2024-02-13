from os import environ, path

from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, ".env"))

class Config:
    """Set Flask configuration from environment variables."""
    
    FLASK_APP = environ.get("FLASK_APP")
    FLASK_DEBUG = environ.get("FLASK_DEBUG")
    SECRET_KEY = environ.get("SECRET_KEY")

    # plugin_hashid
    HASHID_SALT = environ.get("HASHID_SALT")

    # plugin_gmail
    GMAIL_ACCOUNT = environ.get("GMAIL_ACCOUNT")
    GMAIL_PASSWORD = environ.get("GMAIL_PASSWORD")
    GMAIL_ADMIN_MAILBOXES = environ.get("GMAIL_ADMIN_MAILBOXES").split(',')

    # plugin_tasks
    TASKS_PAUSE = int(environ.get("TASKS_PAUSE"))

    # plugin_excel
    EXCEL_RELATIVE_PATH_FROM_STATIC = environ.get("EXCEL_RELATIVE_PATH_FROM_STATIC")
    EXCEL_TEMPLATE = environ.get("EXCEL_TEMPLATE")

    # plugin_params
    PARAM_EXTERNAL_URL = environ.get("PARAM_EXTERNAL_URL")
    PARAM_INVITATION_TOKEN = environ.get("PARAM_INVITATION_TOKEN")
    PARAM_ALLOW_MODIFICATIONS = environ.get("PARAM_ALLOW_MODIFICATIONS").lower() == "true"
    PARAM_ALLOW_VOLUNTEERS = environ.get("PARAM_ALLOW_VOLUNTEERS").lower() == "true"

    # plugin rewards
    REWARDS_CLASS = environ.get("REWARDS_CLASS")

    # Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = environ.get("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # Static Assets
    STATIC_FOLDER = "static"
    TEMPLATES_FOLDER = "templates"
