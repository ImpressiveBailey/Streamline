# server/app/routes/__init__.py
from flask import Blueprint

# from .index import index_bp
from .gdoc import register_gdoc_routes

api_bp = Blueprint('api', __name__, url_prefix='/api')

def register_routes(app):
    register_gdoc_routes(api_bp)

    app.register_blueprint(api_bp)