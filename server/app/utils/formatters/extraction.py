from urllib.parse import urlparse
import json

def extract_handle(url: str) -> str:
    """
    Return the slug after `/collections/` and before any next `/`, `?`, or `#`.
    e.g. https://site.com/collections/my-collection?sort=best
         -> "my-collection"
    """
    print(url)
    if not url:
        return ""

    try:
        path = urlparse(url).path or ""
    except Exception:
        path = url or ""

    marker = "/collections/"
    idx = path.find(marker)
    if idx == -1:
        return ""

    remainder = path[idx + len(marker):]  # e.g. "my-collection/extra"
    # Cut at first '/', '?', or '#'
    for sep in ("/", "?", "#"):
        cut = remainder.find(sep)
        if cut != -1:
            remainder = remainder[:cut]

    return remainder.strip("/")

def extract_slug(url: str) -> str:
    """
    Extract the last clean path segment from any URL.
    Handles:
        - query params
        - hash fragments
        - trailing slashes
        - URLs without scheme
        - naked domain URLs
    """
    if not url or not isinstance(url, str):
        return ""

    # Ensure URL has a scheme so urlparse behaves correctly
    if "://" not in url:
        url = "https://" + url

    parsed = urlparse(url)
    path = parsed.path or ""

    # Split into segments, ignore empties
    segments = [seg for seg in path.split("/") if seg]

    if not segments:
        return ""

    return segments[-1]