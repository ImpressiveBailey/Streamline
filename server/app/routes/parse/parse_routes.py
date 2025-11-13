from flask import Blueprint, request, jsonify, Response
import logging
import re

from server.app.services.rest_api.interpret_page.page_breakdown import breakdown_pages
from server.app.services.rest_api.interpret_page.csv_conversion import convert_csv

routes = Blueprint("parse", __name__)
log = logging.getLogger(__name__)

_SAFE_ID_RE = re.compile(r"^[a-z0-9_]+$")

def _err(msg, code=400):
    return jsonify({"error": msg}), code

@routes.route("/pages", methods=["POST"])
def parse_pages():
    """
    Expected body:
    {
      "client_id": "georges_cameras",
      "globals": {...},                       # ignored here (optional)
      "pages": [ { ... , "content_type": "...", "pageBody": "<h1>..</h1>" }, ... ]
    }
    """
    try:
        payload = request.get_json(silent=True) or {}
        client_id = (payload.get("client_id") or "").strip()
        globals = (payload.get("globals") or {})
        pages = payload.get("pages")

        # Basic validation
        if not client_id:
            return _err("Missing 'client_id'")
        if not _SAFE_ID_RE.match(client_id):
            return _err("Invalid 'client_id' (only a–z, 0–9, and underscore allowed)")

        if not isinstance(pages, list) or not pages:
            return _err("Provide non-empty 'pages' array")

        page_errors = []
        for i, p in enumerate(pages, start=1):
            if not isinstance(p, dict):
                page_errors.append(f"pages[{i}]: must be an object")
                continue
            if "content_type" not in p or not str(p["content_type"]).strip():
                page_errors.append(f"pages[{i}]: missing 'content_type'")
            if "pageBody" not in p:
                page_errors.append(f"pages[{i}]: missing 'pageBody'")
            # Optional but nice sanity checks
            if "pageNumber" in p and not isinstance(p["pageNumber"], (int,)):
                page_errors.append(f"pages[{i}]: 'pageNumber' must be int if provided")

        if page_errors:
            return jsonify({"error": "Invalid pages", "details": page_errors}), 400

        # Hand off to breakdown_pages (only needs client_id & pages)
        results = breakdown_pages(client_id=client_id, pages=pages)

        # Return whatever breakdown returns (wrap with client_id for context)
        return jsonify({"client_id": client_id, "globals": globals, "results": results.get('pages', []), "errors": results.get('errors', [])}), 200

    except Exception as e:
        log.exception("parse_pages error")
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500


@routes.route("/csv", methods=["POST"])
def convert_json_to_csv():
    payload = request.get_json(silent=True) or {}
    csv_text, filename = convert_csv(payload)
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )