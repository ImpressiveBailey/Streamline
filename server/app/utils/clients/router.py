# server/app/utils/clients/router.py
from importlib import import_module

# Cache of (client_id, content_type) -> module
_FORMATTER_CACHE = {}


def _safe(segment: str, name: str):
    """
    Very small safety check so we don't let arbitrary import paths in.
    Adjust if you already have a global version of this.
    """
    if not segment or not isinstance(segment, str):
        raise ValueError(f"{name} must be a non-empty string")

    # Allow letters, digits, underscore only
    import re
    if not re.match(r"^[A-Za-z0-9_]+$", segment):
        raise ValueError(f"{name} contains invalid characters: {segment!r}")


def resolve_formatter(client_id: str, content_type: str, strict: bool = True):
    """
    Return the *module* for a given client_id + content_type.

    Looks for:
        server.app.utils.clients.{client_id}.{content_type}

    - If strict=True (default), it raises if the module or formatters are missing.
    - If strict=False, it returns None when the module can't be imported.

    Typical usage:
        mod = resolve_formatter("georges_cameras", "collection_page")
        format_page_fn = getattr(mod, "format_page", None)
        format_csv_fn = getattr(mod, "format_csv", None)
    """
    key = (client_id, content_type)
    if key in _FORMATTER_CACHE:
        return _FORMATTER_CACHE[key]

    _safe(client_id, "client_id")
    _safe(content_type, "content_type")

    module_path = f"server.app.utils.clients.{client_id}.{content_type}"

    try:
        mod = import_module(module_path)
    except ModuleNotFoundError as e:
        if strict:
            raise FileNotFoundError(f"Formatter module not found: {module_path}") from e
        return None

    _FORMATTER_CACHE[key] = mod
    return mod
