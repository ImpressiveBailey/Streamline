import re
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup, NavigableString

_DOC_ID_RE = re.compile(r"/document/d/([a-zA-Z0-9-_]+)")

def extract_doc_id(url: str) -> str:
    m = _DOC_ID_RE.search(url)
    if not m:
        raise ValueError("Could not extract document ID from the provided URL.")
    return m.group(1)


def html_to_richtext(html: str) -> dict:
    """
    Convert an HTML fragment to Shopify rich_text_field JSON structure:
    {
      "type": "root",
      "children": [...]
    }
    """
    html = html or ""
    soup = BeautifulSoup(html, "html.parser")
    root_children = []

    def parse_inline_children(parent):
        nodes = []
        for child in parent.children:
            if isinstance(child, NavigableString):
                text = str(child)
                if text:
                    nodes.append({"type": "text", "value": text})
            else:
                name = child.name.lower()
                if name == "a":
                    href = child.get("href") or ""
                    link_children = []
                    for c in child.children:
                        if isinstance(c, NavigableString):
                            t = str(c)
                            if t:
                                link_children.append({"type": "text", "value": t})
                        else:
                            t = c.get_text()
                            if t:
                                link_children.append({"type": "text", "value": t})
                    if link_children:
                        nodes.append({
                            "type": "link",
                            "url": href,
                            "title": None,
                            "target": None,
                            "children": link_children,
                        })
                elif name in ("strong", "b", "em", "i", "u", "span", "br"):
                    # Flatten styling/span into plain text
                    t = child.get_text()
                    if t:
                        nodes.append({"type": "text", "value": t})
                else:
                    # Fallback: any other inline-ish tag -> text
                    t = child.get_text()
                    if t:
                        nodes.append({"type": "text", "value": t})
        return nodes

    def parse_block(el):
        name = getattr(el, "name", None)
        if not name:
            # Top-level text node -> wrap in paragraph
            text = str(el).strip()
            if not text:
                return None
            return {
                "type": "paragraph",
                "children": [{"type": "text", "value": text}],
            }

        name = name.lower()

        if name in ("p", "div"):
            children = parse_inline_children(el)
            if not children:
                return None
            return {"type": "paragraph", "children": children}

        if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(name[1])
            children = parse_inline_children(el)
            if not children:
                return None
            return {"type": "heading", "level": level, "children": children}

        if name in ("ul", "ol"):
            list_type = "unordered" if name == "ul" else "ordered"
            items = []
            for li in el.find_all("li", recursive=False):
                li_children = parse_inline_children(li)
                if not li_children:
                    continue
                items.append({"type": "list-item", "children": li_children})
            if not items:
                return None
            return {
                "type": "list",
                "listType": list_type,
                "children": items,
            }

        if name in ("script", "style"):
            return None

        # Fallback: treat unknown blocks as a paragraph
        children = parse_inline_children(el)
        if not children:
            return None
        return {"type": "paragraph", "children": children}

    for el in soup.contents:
        # Skip pure whitespace
        if not getattr(el, "name", None) and not str(el).strip():
            continue
        node = parse_block(el)
        if node:
            root_children.append(node)

    return {"type": "root", "children": root_children}


def slugify(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("&", " and ")
    text = text.replace("’", "").replace("'", "")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")