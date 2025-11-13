# app/routes/clients.py
from flask import Blueprint, jsonify
from pathlib import Path
import re
import logging

routes = Blueprint("clients", __name__)
log = logging.getLogger(__name__)

# Root where client folders live
CLIENTS_ROOT = Path("app/utils/clients").resolve()

SAFE_NAME_RE = re.compile(r"^[a-z0-9_]+$")

def _prettify(name: str) -> str:
    # 'georges_cameras' -> 'Georges Cameras'
    return name.replace("_", " ").strip().title()

def _safe_client_or_404(client: str) -> Path:
    if not SAFE_NAME_RE.match(client or ""):
        # invalid format
        raise FileNotFoundError("Invalid client")
    base = CLIENTS_ROOT / client
    # prevent path traversal and ensure directory
    if not base.exists() or not base.is_dir() or base.resolve().parent != CLIENTS_ROOT:
        raise FileNotFoundError("Client not found")
    return base.resolve()

@routes.route("/", methods=["GET"])
def list_clients():
    """
    Returns:
    {
      "clients": [
        {"id": "georges_cameras", "label": "Georges Cameras"},
        ...
      ]
    }
    """
    if not CLIENTS_ROOT.exists() or not CLIENTS_ROOT.is_dir():
        log.warning("Clients root does not exist: %s", CLIENTS_ROOT)
        return jsonify({"clients": []}), 200

    clients = []
    for p in sorted(CLIENTS_ROOT.iterdir(), key=lambda x: x.name):
        if p.is_dir() and SAFE_NAME_RE.match(p.name):
            clients.append({"id": p.name, "label": _prettify(p.name)})

    return jsonify({"clients": clients}), 200

@routes.route("/<client>/content-types", methods=["GET"])
def list_content_types_for_client(client: str):
    """
    Returns:
    {
      "client": {"id": "georges_cameras", "label": "Georges Cameras"},
      "contentTypes": [
        {"id": "collection_page", "label": "Collection Page"},
        {"id": "brand_page", "label": "Brand Page"},
        ...
      ]
    }
    """
    try:
        base = _safe_client_or_404(client)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404

    content_types = []
    for f in sorted(base.glob("*.py"), key=lambda x: x.name):
        stem = f.stem
        if stem in {"__init__"} or stem.startswith("_"):
            continue
        if not SAFE_NAME_RE.match(stem):
            continue
        content_types.append({"id": stem, "label": _prettify(stem)})

    return jsonify({
        "client": {"id": client, "label": _prettify(client)},
        "contentTypes": content_types
    }), 200
