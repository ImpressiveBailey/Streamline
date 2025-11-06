# server/app/__init__.py
import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

# ----- logging -----
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("openai").setLevel(logging.CRITICAL)

def _react_build_path() -> str:
    # Resolve to .../client/build regardless of cwd
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "..", "client", "build"))

def create_app():
    load_dotenv()

    static_dir = _react_build_path()
    app = Flask(__name__, static_folder=static_dir, static_url_path="/")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # safe behind proxy
    CORS(app)

    # --- React index ---
    @app.route("/")
    def home():
        return send_from_directory(app.static_folder, "index.html")

    # --- Serve built assets or fall back to SPA routing ---
    @app.route("/<path:path>")
    def static_proxy(path):
        file_path = os.path.join(app.static_folder, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(app.static_folder, path)
        # Let the client router handle it
        return send_from_directory(app.static_folder, "index.html")

    # --- Register API routes (mounted under /api) ---
    # Import inside factory to avoid circulars / import-time side-effects
    from .routes import register_routes
    register_routes(app)

    # --- 404 fallback to React (useful for direct hits to nested routes) ---
    @app.errorhandler(404)
    def not_found(_e):
        return send_from_directory(app.static_folder, "index.html")

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret')
    return app
