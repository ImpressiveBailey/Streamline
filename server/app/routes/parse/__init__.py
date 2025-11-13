# server/app/routes/gdoc/__init__.py

from .parse_routes import routes
# Set url_prefix here
def register_parse_routes(app):
    app.register_blueprint(routes, url_prefix='/parse')

