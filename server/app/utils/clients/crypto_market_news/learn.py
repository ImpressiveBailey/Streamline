# server/app/utils/clients/georges_cameras/collection_page.py
from bs4 import BeautifulSoup
from server.app.utils.formatters.extraction import extract_handle, extract_slug

MANIFEST = {
  "version": "1.0",
  "fields": [
    {
      "label": "Title",
      "path": "data.pageHeading",
      "type": "text",
      "upload": {"metafield": "title"}
    },
    {
      "label": "Meta Title",
      "path": "data.metaTitle",
      "type": "text",
      "upload": {"metafield": "meta_title"}
    },
    {
      "label": "Meta Description",
      "path": "data.metaDescription",
      "type": "text",
      "upload": {"metafield": "meta_description"}
    },
    {
      "label": "Body",
      "path": "data.body_content",
      "type": "html",
      "upload": {"metafield": "body_content"}
    }
  ]
}



def format_page(page: dict) -> dict:
    """
    Input page dict has keys like:
      - pageBody (HTML)
      - pageHeading, metaTitle, metaDescription, pageUrl, pageNumber, etc.
    """

    html = page.get("pageBody") or ""
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    body_content = ""

    if h1:
        chunks = []
        # everything after the H1, in order
        for sib in h1.next_siblings:
            chunks.append(str(sib))
        body_content = "".join(chunks).strip()
    else:
        # fallback if no H1 – use full body
        body_content = str(soup) if soup else html

    return (
        {
            # General
            "pageUrl": page.get("pageUrl"),
            "author": page.get("author"),
            "pageNumber": page.get("pageNumber"),

            # Meta
            "pageHeading": page.get("pageHeading"),
            "metaTitle": page.get("metaTitle"),
            "metaDescription": page.get("metaDescription"),

            # Content
            "body_content": body_content,
        },
        MANIFEST,
    )


def format_csv(page: dict):
    """
    Build one or more CSV rows for this page.

    `page` is expected to be the formatted page object from /parse/pages:
      {
        "pageNumber": ...,
        "pageUrl": ...,
        "data": {...},
        "manifest": {...},
        ...
      }

    We return a list of row dicts whose keys match MANIFEST upload.metafield
    values: slug, title, meta_title, meta_description, body_content.
    """
    # Support being called with either the full page object or just the data dict
    data = {}
    if isinstance(page, dict):
        if isinstance(page.get("data"), dict):
            data = page["data"]
        else:
            # fallback: treat page itself as data
            data = page
    else:
        data = {}
    url = data.get('pageUrl')

    row = {
        "handle": extract_slug(url),
        "author": data.get("author") or "",
        "title": data.get("pageHeading") or "",
        "meta_title": data.get("metaTitle") or "",
        "meta_description": data.get("metaDescription") or "",
        "body_content": data.get("body_content") or "",
    }

    # Return as a list so callers can extend with multiple rows per page if needed
    return [row]