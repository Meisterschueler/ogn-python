from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

from ogn_python.navigation import nav

# Initialize Flask
app = Flask(__name__)
app.config.from_object('config.default')

# Bootstrap
bootstrap = Bootstrap(app)

# Sqlalchemy
db = SQLAlchemy(app)

# Navigation
nav.init_app(app)
