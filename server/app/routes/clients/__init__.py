# server/app/routes/gdoc/__init__.py

from .client_routes import routes
# Set url_prefix here
def register_client_routes(app):
    app.register_blueprint(routes, url_prefix='/clients')

