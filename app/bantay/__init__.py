from flask import Blueprint

bantay_api = Blueprint("bantay", __name__)

from . import bantay
