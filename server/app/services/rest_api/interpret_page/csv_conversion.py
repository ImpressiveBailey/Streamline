# server/app/services/rest_api/interpret_page/csv_conversion.py
import csv
import io

from server.app.utils.clients.router import resolve_formatter


def convert_csv(payload: dict):
    """
    Orchestrator:
      - Reads payload from the frontend (formattedDoc)
      - For each page, finds its formatter module
      - Calls module.format_csv(page) to get row(s)
      - Stitches everything into a single CSV

    Expected payload (same as /review):
      {
        "client_id": "...",
        "globals": {...},
        "results": {
          "pages": [
             {
               "pageNumber": 1,
               "pageUrl": "...",
               "content_type": "collection_page",
               "data": {...},
               "manifest": {...}
             },
             ...
          ]
        }
      }
    """
    client_id = payload.get("client_id") or "client"
    results = payload.get("results") or {}

    # Support both shapes: { "pages": [...] } or legacy [...]
    if isinstance(results, dict) and isinstance(results.get("pages"), list):
        pages = results["pages"]
    elif isinstance(results, list):
        pages = results
    else:
        pages = []

    all_rows = []
    explicit_headers = None  # allow a formatter to override headers

    for pg in pages:
        content_type = pg.get("content_type")

        # Re-use your existing resolver that /parse/pages uses
        mod = resolve_formatter(client_id, content_type, strict=False) if content_type else None
        if not mod:
            continue

        fmt = getattr(mod, "format_csv", None)
        if not callable(fmt):
            continue

        page_rows = fmt(pg)

        # Normalise return:
        # - dict -> [dict]
        # - list[dict] -> as is
        # - (rows, headers) -> rows plus explicit header list
        if not page_rows:
            continue

        if isinstance(page_rows, tuple) and len(page_rows) == 2:
            rows, headers = page_rows
            if headers:
                explicit_headers = list(headers)
            page_rows = rows

        if isinstance(page_rows, dict):
            page_rows = [page_rows]

        # Ensure list of dicts
        page_rows = [r for r in page_rows if isinstance(r, dict)]
        if not page_rows:
            continue

        all_rows.extend(page_rows)

    # Nothing to export
    if not all_rows:
        return "", f"{client_id}_pages.csv"

    # Determine headers:
    # - if any formatter returned explicit headers, use that
    # - else union of all keys in order of first appearance
    if explicit_headers:
        headers = explicit_headers
    else:
        headers = []
        for row in all_rows:
            for k in row.keys():
                if k not in headers:
                    headers.append(k)

    # Build CSV
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()

    for row in all_rows:
        # Fill missing keys with empty string
        writer.writerow({h: row.get(h, "") for h in headers})

    csv_text = buf.getvalue()
    buf.close()

    filename = f"{client_id}_pages.csv"
    return csv_text, filename