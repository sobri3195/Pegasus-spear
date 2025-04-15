#!/usr/bin/env python3

import random
import string
import hashlib
from functools import wraps
import datetime
import os
import shutil
import tempfile

from flask import Flask, request
from flask_script import Manager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from models import db
from models import Agent
from models import Command
from webui import webui
from api import api
from config import config

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
app.config.from_object(config['prod' if os.getenv('FLASK_ENV') == 'production' else 'dev'])
app.register_blueprint(webui)
app.register_blueprint(api, url_prefix="/api")

# Initialize rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

db.init_app(app)
manager = Manager(app)

@app.after_request
def security_headers(response):
    response.headers["Server"] = "Pegasus-Spear"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

@manager.command
def initdb():
    """Initialize the database."""
    db.drop_all()
    db.create_all()
    db.session.commit()
    print("Database initialized successfully for Pegasus-Spear")

if __name__ == '__main__':
    if os.getenv('FLASK_ENV') == 'production':
        app.run(ssl_context='adhoc')  # Force HTTPS in production
    else:
        manager.run()
