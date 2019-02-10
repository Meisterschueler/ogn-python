from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from navigation import nav

app = Flask(__name__)
app.config.from_object('config.default')

bootstrap = Bootstrap(app)

db = SQLAlchemy(app)

nav.init_app(app)
