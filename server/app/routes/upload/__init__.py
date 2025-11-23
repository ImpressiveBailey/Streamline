# server/app/routes/gdoc/__init__.py

from .upload_routes import routes
# Set url_prefix here
def register_upload_routes(app):
    app.register_blueprint(routes, url_prefix='/upload')

