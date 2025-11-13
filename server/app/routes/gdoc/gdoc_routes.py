from flask import Blueprint, request, jsonify
import logging
from server.app.services.google.GoogleServiceHelper import GoogleServiceHelper
from server.app.utils.formatters.parsing import extract_doc_id
from server.app.services.rest_api.interpret_page.main import interpret_page

routes = Blueprint("gdoc", __name__)
log = logging.getLogger(__name__)

# Reuse a single helper instance (cheap + avoids rebuilding clients repeatedly)
google_helper = GoogleServiceHelper()

@routes.route("/", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "service": "gdoc",
        "service_account_configured": google_helper.is_configured,
    }), 200

@routes.route("/fetch", methods=["POST"])
def fetch_google_doc():
    """
    Body: {
      "url": "https://docs.google.com/document/d/<id>/edit"   // or "doc_id"
      "format": "html" | "text"                                // optional; default "html"
    }
    """
    payload = request.get_json(silent=True) or {}
    url = (payload.get("url") or "").strip()
    doc_id = (payload.get("doc_id") or "").strip()
    fmt = (payload.get("format") or "html").lower()

    if not doc_id:
        if not url:
            return jsonify({"error": "Provide 'url' or 'doc_id'"}), 400
        try:
            doc_id = extract_doc_id(url)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    if fmt == "text":
        content, source = google_helper.fetch_doc_text(doc_id)
    else:
        content, source = google_helper.fetch_doc_html(doc_id)
        content = interpret_page(content)

    if content is None:
        return jsonify({
            "error": "Unable to fetch document. Share with the service account or make it viewable by link.",
            "docId": doc_id
        }), 403

    return jsonify({"docId": doc_id, "source": source, "format": fmt, "content": content}), 200


