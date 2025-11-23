# server/app/services/rest_api/interpret_page/upload_pages.py

from server.app.utils.clients.router import resolve_formatter

def handle_upload(payload: dict) -> dict:
    client_id = payload.get("client_id") or "client"
    results = payload.get("results") or {}

    # Support two shapes: same as convert_csv()
    if isinstance(results, dict) and isinstance(results.get("pages"), list):
        pages = results["pages"]
    elif isinstance(results, list):
        pages = results
    else:
        pages = []

    output = []
    success_count = 0
    fail_count = 0

    for page in pages:
        content_type = page.get("content_type")
        page_number = page.get("pageNumber")

        mod = resolve_formatter(client_id, content_type, strict=False)
        if not mod:
            output.append({
                "pageNumber": page_number,
                "status": "failed",
                "error": f"No formatter found for {content_type}"
            })
            fail_count += 1
            continue

        upload_fn = getattr(mod, "upload_page", None)

        if not callable(upload_fn):
            output.append({
                "pageNumber": page_number,
                "status": "failed",
                "error": f"upload_page() not implemented for {content_type}"
            })
            fail_count += 1
            continue

        try:
            status = upload_fn(page)
            if status == True or status == "ok":
                output.append({
                    "pageNumber": page_number,
                    "status": "success"
                })
                success_count += 1
            else:
                output.append({
                    "pageNumber": page_number,
                    "status": "failed",
                    "error": str(status)
                })
                fail_count += 1

        except Exception as e:
            output.append({
                "pageNumber": page_number,
                "status": "failed",
                "error": str(e)
            })
            fail_count += 1

    return {
        "client_id": client_id,
        "uploaded": success_count,
        "failed": fail_count,
        "details": output,
    }
