import re

_DOC_ID_RE = re.compile(r"/document/d/([a-zA-Z0-9-_]+)")

def extract_doc_id(url: str) -> str:
    m = _DOC_ID_RE.search(url)
    if not m:
        raise ValueError("Could not extract document ID from the provided URL.")
    return m.group(1)
