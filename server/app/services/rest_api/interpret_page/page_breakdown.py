# server/app/services/rest_api/interpret_page/page_breakdown.py
from importlib import import_module
import logging
import re
from server.app.utils.clients.router import resolve_formatter

log = logging.getLogger(__name__)
_SAFE_RE = re.compile(r"^[a-z0-9_]+$")

# simple in-process cache so we don't re-import on every page
_FORMATTER_CACHE = {}  # {(client_id, content_type): callable}

def _get_page_formatter(client_id: str, content_type: str):
    mod = resolve_formatter(client_id, content_type, strict=True)
    fn = getattr(mod, "format_page", None)
    if not callable(fn):
        raise AttributeError(
            f"Formatter module {mod.__name__} missing callable 'format_page(page: dict) -> (data, manifest)'"
        )
    return fn

def breakdown_pages(client_id, pages):
    """
    pages: list of dicts, each containing at least:
      - content_type (str)
      - pageBody, meta fields, etc. (whatever your formatters expect)
    Returns:
      {
        "results": [ { "pageNumber": ..., "content_type": ..., "ok": true, "data": {...} }, ... ],
        "errors":  [ { "pageNumber": ..., "content_type": ..., "error": "..." }, ... ]
      }
    """
    results = []
    errors = []

    for p in (pages or []):
        page_num = p.get("pageNumber")
        ctype = (p.get("content_type") or "").strip()

        if not ctype:
            errors.append({"pageNumber": page_num, "error": "Missing content_type"})
            continue

        try:
            formatter = _get_page_formatter(client_id, ctype)
            data, manifest = formatter(p)  # pass the whole page dict; keep it flexible
            results.append({
                "pageNumber": page_num,
                "content_type": ctype,
                "ok": True,
                "data": data,
                "manifest": manifest
            })
        except Exception as e:
            log.exception("Formatting failed for page %s (%s/%s)", page_num, client_id, ctype)
            errors.append({
                "pageNumber": page_num,
                "content_type": ctype,
                "error": str(e)
            })

    return {"pages": results, "errors": errors}
