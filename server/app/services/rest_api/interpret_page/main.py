import re
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse, parse_qs, unquote

PAGE_MARKER_RE = re.compile(r"^\s*Page\s+(\d+)\s*$", re.I)

def _t(el: Optional[Tag]) -> str:
    return (el.get_text(" ", strip=True) if el else "").strip()

def _unwrap_google_redirect(href: Optional[str]) -> Optional[str]:
    if not href:
        return None
    try:
        u = urlparse(href)
        if u.netloc.endswith("google.com") and u.path.startswith("/url"):
            q = parse_qs(u.query).get("q", [""])[0]
            return unquote(q) or href
        return href
    except Exception:
        return href

def _is_page_title_marker(el: Tag) -> bool:
    txt = _t(el)
    if not PAGE_MARKER_RE.match(txt):
        return False
    classes = " ".join(el.get("class", [])).lower()
    return "title" in classes  # strict Google Docs "Title" style

def _find_page_markers(soup: BeautifulSoup) -> List[Tag]:
    # Prefer elements with class containing 'title'
    candidates = soup.find_all(True, class_=lambda c: c and "title" in " ".join(c).lower())
    markers = [el for el in candidates if PAGE_MARKER_RE.match(_t(el))]
    if markers:
        return markers
    # Fallback: any element matching "Page N"
    return [el for el in soup.find_all(True) if PAGE_MARKER_RE.match(_t(el))]

def _parse_globals(soup: BeautifulSoup) -> Dict[str, Any]:
    out = {"clientName": None, "clientUrl": None, "numberOfPages": None}

    name_node = soup.find(string=re.compile(r"^\s*Client Name\s*:", re.I))
    if name_node:
        # Extract the full line's text and strip the label
        line_txt = name_node.parent.get_text(" ", strip=True) if getattr(name_node, "parent", None) else str(name_node)
        out["clientName"] = re.sub(r"^\s*Client Name\s*:\s*", "", line_txt, flags=re.I).strip()

    url_node = soup.find(string=re.compile(r"^\s*Client URL\s*:?", re.I))
    if url_node:
        container = getattr(url_node, "parent", None) or soup
        a = getattr(container, "find_next", lambda *args, **kw: None)("a")
        if a and a.get("href"):
            out["clientUrl"] = _unwrap_google_redirect(a.get("href"))
        else:
            m = re.search(r"Client URL\s*:?\s*(\S+)", container.get_text(" ", strip=True), re.I)
            if m:
                out["clientUrl"] = m.group(1).strip()

    num_node = soup.find(string=re.compile(r"^\s*Number of Pages\s*:", re.I))
    if num_node:
        # Prefer the parent line (contains the number in a sibling <span>)
        container = getattr(num_node, "parent", None) or soup
        line_txt = container.get_text(" ", strip=True)
        m = re.search(r"Number of Pages\s*:\s*(\d+)", line_txt, re.I)
        if not m:
            # fallback: next text node with digits
            nxt = soup.find(string=re.compile(r"^\s*\d+\s*$"))
            if nxt:
                m = re.search(r"(\d+)", nxt)
        if m:
            try:
                out["numberOfPages"] = int(m.group(1))
            except ValueError:
                pass

    return out

def _extract_meta_and_find_h1(marker: Tag) -> Tuple[Dict[str, Optional[str]], Optional[Tag]]:
    """
    Collects Page URL / Meta title / Meta description after the 'Page N' Title,
    and returns the first content H1 (start of page content).
    Stops at the next 'Page N' Title or the first content H1.
    """
    page_url = meta_title = meta_desc = author = None
    content_h1: Optional[Tag] = None

    for el in marker.next_elements:
        if not isinstance(el, Tag):
            continue

        # next page title marker ends this page's meta scan
        if _is_page_title_marker(el) and el is not marker:
            break

        txt = _t(el)

        # first real H1 marks content start and ends meta scan
        if el.name == "h1" and not PAGE_MARKER_RE.match(txt):
            content_h1 = el
            break

        if page_url is None:
            m = re.match(r"^\s*Page URL\s*:\s*(\S+)", txt, re.I)
            if m:
                page_url = m.group(1).strip()
            else:
                a = el.find("a") if el.name != "a" else el
                if a and a.get("href") and re.search(r"Page URL\s*:", el.get_text(" ", strip=True), re.I):
                    page_url = _unwrap_google_redirect(a.get("href"))
            if page_url:
                continue

        if meta_title is None:
            m = re.match(r"^\s*Meta title\s*:\s*(.+)$", txt, re.I)
            if m:
                meta_title = m.group(1).strip()
                continue

        if meta_desc is None:
            m = re.match(r"^\s*Meta description\s*:\s*(.+)$", txt, re.I)
            if m:
                meta_desc = m.group(1).strip()
                continue

        if author is None:
            m = re.match(r"^\s*Author\s*:\s*(.+)$", txt, re.I)
            if m:
                author = m.group(1).strip()
                continue


    return {"pageUrl": page_url, "metaTitle": meta_title, "metaDescription": meta_desc, "author": author}, content_h1

def _top_body_child(node: Tag) -> Tag:
    """Ascend until the direct child of <body> (or the highest available)."""
    cur = node
    while cur.parent and cur.parent.name != "body":
        cur = cur.parent
    return cur

def _collect_page_body_html(soup: BeautifulSoup, start_h1: Tag, next_marker: Optional[Tag]) -> str:
    """
    Return HTML from the H1 (inclusive) up to—but not including—the next page Title marker.
    Works even when markers/content are wrapped in different container DIVs.
    """
    body = soup.body or soup
    body_children: List[Tag] = [ch for ch in body.children if isinstance(ch, Tag)]

    start_node = _top_body_child(start_h1)
    try:
        start_idx = body_children.index(start_node)
    except ValueError:
        start_idx = None

    end_node = _top_body_child(next_marker) if next_marker else None
    end_idx = None
    if end_node is not None:
        try:
            end_idx = body_children.index(end_node)
        except ValueError:
            end_idx = None

    # Preferred path: slice by body children indices (most robust / no duplication)
    if start_idx is not None:
        slice_nodes = body_children[start_idx:(end_idx if end_idx is not None else len(body_children))]
        return "".join(str(n) for n in slice_nodes).strip()

    # Fallback: walk forward from the start_h1 collecting until we hit next_marker
    collected = [str(start_h1)]
    for el in start_h1.next_elements:
        if isinstance(el, Tag) and next_marker is not None and el is next_marker:
            break
        # Only capture top-level tags to avoid duplicates
        if isinstance(el, Tag) and el.parent == body:
            collected.append(str(el))
    return "".join(collected).strip()

def interpret_page(google_doc_html: str) -> Dict[str, Any]:
    """
    Output:
    {
      "globals": {...},
      "pages": [
        {
          "pageNumber": int,
          "titleMarker": "Page N",
          "pageUrl": str|None,
          "metaTitle": str|None,
          "metaDescription": str|None,
          "pageHeading": str|None,
          "pageBody": "<h1>...</h1> ... (HTML)"
        }, ...
      ]
    }
    """
    soup = BeautifulSoup(google_doc_html, "html.parser")

    globals_blk = _parse_globals(soup)
    markers = _find_page_markers(soup)

    pages: List[Dict[str, Any]] = []
    for idx, marker in enumerate(markers):
        m = PAGE_MARKER_RE.match(_t(marker))
        page_number = int(m.group(1)) if m else (idx + 1)

        meta, content_h1 = _extract_meta_and_find_h1(marker)

        page_heading = _t(content_h1) if content_h1 else None
        next_marker = markers[idx + 1] if idx + 1 < len(markers) else None
        page_body = _collect_page_body_html(soup, content_h1, next_marker) if content_h1 else ""

        pages.append({
            "pageNumber": page_number,
            "titleMarker": _t(marker),
            "pageUrl": meta["pageUrl"],
            "metaTitle": meta["metaTitle"],
            "author": meta["author"],
            "metaDescription": meta["metaDescription"],
            "pageHeading": page_heading,
            "pageBody": page_body
        })

    expected = globals_blk.get("numberOfPages")
    if isinstance(expected, int) and expected > 0 and len(pages) > expected:
        pages = pages[:expected]

    return {"globals": globals_blk, "pages": pages}



