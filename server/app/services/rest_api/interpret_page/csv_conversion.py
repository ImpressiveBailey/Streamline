import csv
import io

from server.app.utils.clients.router import resolve_formatter


def convert_csv(payload: dict):
    """
    Orchestrator:
      - Reads payload from the frontend (formattedDoc)
      - For each page, finds its formatter module
      - Calls module.format_csv(page) to get row(s)
      - Stitches everything into one or more CSVs.

    New behaviour:
      - If a formatter returns {"collection": [...], "faq": [...]}
        we treat "collection" as the main pages CSV
        and "faq" as a separate FAQ CSV (for metaobjects).
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

    # Main collection/page rows
    all_rows = []
    explicit_headers = None  # allow a formatter to override headers

    # Optional FAQ rows (metaobjects)
    all_faq_rows = []
    explicit_faq_headers = None

    def _normalise_to_list_dict(rows):
        """Helper to ensure we always get list[dict]."""
        if not rows:
            return []
        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list):
            return []
        return [r for r in rows if isinstance(r, dict)]

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
        if not page_rows:
            continue

        # Handle (rows, headers) shape
        if isinstance(page_rows, tuple) and len(page_rows) == 2:
            rows, headers = page_rows
            # Assume these headers apply to the "main" stream
            if headers:
                explicit_headers = list(headers)
            page_rows = rows

        # If formatter returns a dict with sub-keys like {"collection": [...], "faq": [...]}
        if isinstance(page_rows, dict) and (
            "collection" in page_rows or "faq" in page_rows
        ):
            # Collection/main rows
            collection_part = _normalise_to_list_dict(page_rows.get("collection", []))
            if collection_part:
                all_rows.extend(collection_part)

            # FAQ rows (metaobjects)
            faq_part = _normalise_to_list_dict(page_rows.get("faq", []))
            if faq_part:
                all_faq_rows.extend(faq_part)

            # Skip the generic handling below for this page
            continue

        # Legacy / simple behaviour: treat page_rows as the only stream
        normalised = _normalise_to_list_dict(page_rows)
        if not normalised:
            continue
        all_rows.extend(normalised)

    # If absolutely nothing found
    if not all_rows and not all_faq_rows:
        return {
            "pages": {
                "csv": "",
                "filename": f"{client_id}_pages.csv",
            }
        }

    # Helper to build CSV text from rows + headers
    def _build_csv(rows, explicit_hdrs, default_filename_suffix):
        if not rows:
            return {
                "csv": "",
                "filename": f"{client_id}_{default_filename_suffix}.csv",
            }

        # Determine headers:
        # - if any formatter returned explicit headers, use that
        # - else union of all keys in order of first appearance
        if explicit_hdrs:
            headers = list(explicit_hdrs)
        else:
            headers = []
            for row in rows:
                for k in row.keys():
                    if k not in headers:
                        headers.append(k)

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})

        csv_text = buf.getvalue()
        buf.close()

        return {
            "csv": csv_text,
            "filename": f"{client_id}_{default_filename_suffix}.csv",
        }

    # Build main/pages CSV
    pages_csv = _build_csv(all_rows, explicit_headers, "pages")

    # Build FAQ CSV if any FAQ rows exist
    result = {"pages": pages_csv}
    if all_faq_rows:
        faq_csv = _build_csv(all_faq_rows, explicit_faq_headers, "faq")
        result["faq"] = faq_csv

    return result
