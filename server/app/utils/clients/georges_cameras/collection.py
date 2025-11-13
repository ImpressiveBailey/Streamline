# server/app/utils/clients/georges_cameras/collection_page.py
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json

def _extract_handle(url: str) -> str:
    """
    Return the slug after `/collections/` and before any next `/`, `?`, or `#`.
    e.g. https://site.com/collections/my-collection?sort=best
         -> "my-collection"
    """
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



MANIFEST = {
  "version": "1.0",
  "fields": [
    {
      "label": "Meta Title",
      "path": "data.metaTitle",             # Data Key
      "type": "text",
      "upload": {"metafield": "seo.title"}  # Upload Key
    },
    {
      "label": "Meta Description",
      "path": "data.metaDescription",
      "type": "text",
      "upload": {"metafield": "seo.description"}
    },
    {
      "label": "Page Heading",
      "path": "data.pageHeading",
      "type": "text",
      "upload": {"metafield": "title"}
    },
    {
      "label": "Top Content",
      "path": "data.topContentHtml",
      "type": "html",
      "upload": {"metafield": "body_html"}
    },
    {
      "label": "Bottom Content",
      "path": "data.bottomContentHtml",
      "type": "html",
      "upload": {"metafield": "custom.bottom_description"}
    },
    {
      "label": "FAQ",
      "path": "data.faq",
      "type": "faq",
      "upload": {
        "mode": "metaobject_list",
        "metaobject_type": "faq_item",
        "metafield": "custom.faqs",
        "mapping": {
          "question": {"type": "text", "path": "q"},
          "answer":   {"type": "html", "path": "a"}
        }
      }
    }
  ]
}



def format_page(page: dict) -> dict:
    """
    Input page dict has keys like:
      - pageBody (HTML)
      - pageHeading, metaTitle, metaDescription, pageUrl, pageNumber, etc.
    Return any structure you want your pipeline to use next.
    """
    html = page.get("pageBody") or ""
    soup = BeautifulSoup(html, "html.parser")

    h1 = soup.find("h1")
    top_html = ""
    bottom_html = ""
    faqs = []

    if h1:
        # -------- Top: content after H1 until the first H2/H3 --------
        top_chunks = []
        for sib in h1.next_siblings:
            nm = getattr(sib, "name", None)
            if nm in ("h2", "h3"):
                break
            top_chunks.append(str(sib))
        top_html = "".join(top_chunks).strip()

        # -------- Locate FAQ header (H2/H3 starting with 'FAQ'...) --------
        faq_header = soup.find(
            lambda t: t.name in ("h2", "h3") and t.get_text(strip=True).lower().startswith(
                ("faq", "faqs", "frequently asked")
            )
        )

        # -------- Extract FAQs (questions as H3 under the FAQ header) --------
        if faq_header:
            items = []
            for el in faq_header.next_siblings:
                nm = getattr(el, "name", None)
                # End FAQ section at next H2 (start of next major section)
                if nm == "h2":
                    break
                if nm == "h3":
                    q = el.get_text(" ", strip=True)
                    ans_chunks = []
                    for sib in el.next_siblings:
                        nm2 = getattr(sib, "name", None)
                        if nm2 in ("h3", "h2"):
                            break
                        ans_chunks.append(str(sib))
                    items.append({"q": q, "a": "".join(ans_chunks).strip()})
            faqs = items

        # -------- Bottom: all content after first H2/H3 EXCLUDING the FAQ block --------
        # Build bottom by walking siblings after H1 again, skipping the FAQ region.
        collect = False
        in_faq_block = False
        bottom_chunks = []

        # We’ll use identity checks to know when we hit faq_header.
        for sib in h1.next_siblings:
            nm = getattr(sib, "name", None)

            # Start collecting at the first H2/H3 after H1
            if not collect and nm in ("h2", "h3"):
                collect = True

            if not collect:
                continue

            # If we have a FAQ header, skip everything from it (inclusive)
            # until the next H2 (start of next major section).
            if faq_header and sib is faq_header:
                in_faq_block = True
                continue

            if in_faq_block:
                # End of FAQ block when we hit the next H2
                if nm == "h2":
                    in_faq_block = False
                    # include this H2 (the next section) in bottom
                    bottom_chunks.append(str(sib))
                # otherwise keep skipping
                continue

            # Normal bottom collection (non-FAQ region)
            bottom_chunks.append(str(sib))

        bottom_html = "".join(bottom_chunks).strip()

    return (
        {
            # General
            "pageUrl": page.get("pageUrl"),
            "handle": _extract_handle(page.get("pageUrl")),
            "pageNumber": page.get("pageNumber"),

            # Meta
            "pageHeading": page.get("pageHeading"),
            "metaTitle": page.get("metaTitle"),
            "metaDescription": page.get("metaDescription"),

            # Content
            "topContentHtml": top_html,
            "bottomContentHtml": bottom_html,
            "faq": faqs,
        },
        MANIFEST,
    )

def format_csv(page: dict):
    def _extract_handle_from_url(page_url: str) -> str:
        """
        Handle = slug after /collections/ and before the next / or ? in the URL.
        Fallback: last non-empty segment of the path.
        """
        if not page_url:
            return ""

        path = urlparse(page_url).path or ""
        parts = [p for p in path.split("/") if p]

        # Look for "collections" segment
        try:
            idx = parts.index("collections")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        except ValueError:
            # No /collections/, just return last segment if present
            if parts:
                return parts[-1]

        return ""

    data = page.get("data") or {}
    page_url = data.get("pageUrl") or ""

    handle = _extract_handle_from_url(page_url)
    faqs = data.get("faq") or []

    # IMPORTANT: keys here are the **exact** CSV column headers you wanted.
    row = {
        "Handle": handle,                                     # derived from URL
        "Command": "MERGE",                                   
        "Published": "TRUE",                                  
        "Title": data.get("pageHeading", "") or "",
        "SEO Title": data.get("metaTitle", "") or "",
        "SEO Description": data.get("metaDescription", "") or "",
        "body_html": data.get("topContentHtml", "") or "",
        "Bottom Content": data.get("bottomContentHtml", "") or "",
        # FAQs as JSON array of {q, a}
        "FAQs": json.dumps(faqs, ensure_ascii=False),
    }

    # Single row for this page
    return [row]



def upload_page():
  status = ""
  return status