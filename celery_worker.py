#!/usr/bin/env python
import os
from app import celery, create_app
from app.collect.celery import *

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
app.app_context().push()
