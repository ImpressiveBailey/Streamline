# server/app/routes/gdoc/__init__.py

from .gdoc_routes import routes
# Set url_prefix here
def register_gdoc_routes(app):
    app.register_blueprint(routes, url_prefix='/gdoc')

