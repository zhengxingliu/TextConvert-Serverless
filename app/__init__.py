from flask import Flask, session
from datetime import timedelta

app = Flask(__name__)

from app import login, textnote, homepage, attachment, textract, translate, transcribe

# set session timeout, user login expires after 1 day
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

app.config['SECRET_KEY'] = 'bf7\xf3MP\xe1\x00}\xaf\xffk5\xeb\xb7\xe7o\xda\x05\x10\xcb\x0b\xff\x03'

# restrict file size to 20 Mb
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024
