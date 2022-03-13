"""App configuration."""
import os
from os import environ, path
import redis

#from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
#load_dotenv(path.join(basedir, '.env'))


class Config:
    """Set Flask configuration vars from .env file."""

    # General Config
    SYSTEM_TYPE = environ.get('NODE_ENV')
    SECRET_KEY = os.urandom(64)
    FLASK_APP = environ.get('FLASK_APP')
    FLASK_ENV = environ.get('FLASK_ENV')

    # DBNames
    WEBCNO_REPORT = 'webcno_reports'

    #DOWNLOAD FOLDER
    WEBCNO_DOWNLOAD_FOLDER = "/nitrou/WEBCNO/TEMP"
    DOWNLOAD_ADDR = "https://webcno.turkcell.com.tr/files"

    # Flask-Session
    SESSION_TYPE = environ.get('SESSION_TYPE')

    # Flask-Assets
    LESS_BIN = environ.get('LESS_BIN')
    ASSETS_DEBUG = environ.get('ASSETS_DEBUG')
    LESS_RUN_IN_DEBUG = environ.get('LESS_RUN_IN_DEBUG')

    # Static Assets
    STATIC_FOLDER = environ.get('STATIC_FOLDER')
    TEMPLATES_FOLDER = environ.get('TEMPLATES_FOLDER')
    COMPRESSOR_DEBUG = environ.get('COMPRESSOR_DEBUG')

    # Flask-SQLAlchemy
    SQLALCHEMY_DATABASE_URI = environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = environ.get('SQLALCHEMY_TRACK_MODIFICATIONS')