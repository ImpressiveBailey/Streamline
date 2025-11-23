from flask import Blueprint, request, jsonify, Response
import logging
import re

from server.app.services.rest_api.upload_page.upload_pages import handle_upload


routes = Blueprint("upload", __name__)
log = logging.getLogger(__name__)

@routes.route("/", methods=["POST"])
def upload_pages():
    """
    Handles uploading formatted pages to a client's site.

    Expected same payload shape as /csv and /review:
    {
        "client_id": "GEORGES_CAMERAS",
        "results": { "pages": [ {...}, {...} ] }
    }

    Returns a JSON summary:
    {
        "client_id": "GEORGES_CAMERAS",
        "uploaded": 5,
        "failed": 1,
        "details": [
            { "pageNumber": 1, "status": "success" },
            { "pageNumber": 2, "status": "failed", "error": "…" }
        ]
    }
    """

    payload = request.get_json(silent=True) or {}
    summary = handle_upload(payload)

    return jsonify(summary), 200