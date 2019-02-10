from ogn import app
from ogn import db

from ogn.model import *

@app.route('/')
def index():
    return "WTF"

@app.route('/test')
def test():
    return db.session.query(Device).first().address