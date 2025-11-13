import os
import logging
from typing import Optional, Tuple
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import html

# TEMPLATE + SERVICE ACCOUNT
# googledocfetcher@content-automations-477404.iam.gserviceaccount.com
# https://docs.google.com/document/d/14pFIkIPGpcoEV2DDWESGd7OGIUTT3ls1MF_nJQMV_zU/edit?usp=sharing

log = logging.getLogger(__name__)
_DOCS_SCOPE = ["https://www.googleapis.com/auth/documents.readonly"]

def _default_sa_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))   # e.g., …/server/app/services/google
    root = os.path.normpath(os.path.join(here, "..", "..", ".."))  # -> …/server
    return os.path.join(root, "config", "google_credentials.json")

class GoogleServiceHelper:
    def __init__(self, sa_path: Optional[str] = None):
        env_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.sa_path = sa_path or env_path or _default_sa_path()
        self._docs_client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.sa_path and os.path.exists(self.sa_path))

    def docs_client(self):
        if self._docs_client is not None:
            return self._docs_client
        if not self.is_configured:
            log.info("Google service account not configured or missing file.")
            return None
        creds = service_account.Credentials.from_service_account_file(
            self.sa_path, scopes=_DOCS_SCOPE
        )
        self._docs_client = build("docs", "v1", credentials=creds, cache_discovery=False)
        return self._docs_client

    # ---------- PUBLIC API ----------
    def fetch_doc_text(self, doc_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Legacy: plain text. Keeping for completeness."""
        text = self._try_docs_api_text(doc_id)
        if text:
            return text, "service_account"
        text = self._try_public_export_text(doc_id)
        if text:
            return text, "public"
        return None, None

    def fetch_doc_html(self, doc_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Returns (html, source) where source ∈ {'service_account','public',None}.
        """
        html_str = self._try_docs_api_html(doc_id)
        if html_str:
            return html_str, "service_account"

        html_str = self._try_public_export_html(doc_id)
        if html_str:
            return html_str, "public"

        return None, None

    # ---------- INTERNAL: Docs API renders ----------
    def _try_docs_api_text(self, doc_id: str) -> Optional[str]:
        client = self.docs_client()
        if not client:
            return None
        try:
            doc = client.documents().get(documentId=doc_id).execute()
            return self._flatten_text(doc)
        except HttpError as e:
            log.warning("Docs API error for %s: %s", doc_id, e)
            return None
        except Exception as e:
            log.exception("Unexpected Docs API error for %s: %s", doc_id, e)
            return None

    def _try_docs_api_html(self, doc_id: str) -> Optional[str]:
        client = self.docs_client()
        if not client:
            return None
        try:
            doc = client.documents().get(documentId=doc_id).execute()
            return self._render_html(doc)
        except HttpError as e:
            log.warning("Docs API error for %s: %s", doc_id, e)
            return None
        except Exception as e:
            log.exception("Unexpected Docs API error for %s: %s", doc_id, e)
            return None

    # ---------- INTERNAL: Public export fallbacks ----------
    @staticmethod
    def _try_public_export_text(doc_id: str) -> Optional[str]:
        url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200 and r.text.strip():
                return r.text.strip()
        except requests.RequestException as e:
            log.warning("Public export (txt) failed for %s: %s", doc_id, e)
        return None

    @staticmethod
    def _try_public_export_html(doc_id: str) -> Optional[str]:
        url = f"https://docs.google.com/document/d/{doc_id}/export?format=html"
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200 and r.text.strip():
                return r.text
        except requests.RequestException as e:
            log.warning("Public export (html) failed for %s: %s", doc_id, e)
        return None

    # ---------- RENDERERS ----------
    @staticmethod
    def _flatten_text(doc: dict) -> str:
        chunks = []
        for el in doc.get("body", {}).get("content", []):
            p = el.get("paragraph")
            if not p:
                continue
            for e in p.get("elements", []):
                tr = e.get("textRun")
                if tr and "content" in tr:
                    chunks.append(tr["content"])
        return "".join(chunks).strip()

    def _render_html(self, doc: dict) -> str:
        """
        Minimal-but-meaningful HTML renderer:
        - Headings (HEADING_1..HEADING_6) -> <h1>.. <h6>
        - Normal paragraphs -> <p>
        - Lists -> <ul>/<ol>/<li> (using doc.lists to tell ordered vs bullet)
        - Inline styles: bold, italic, underline, strikethrough, link
        """
        lists_meta = doc.get("lists", {}) or {}
        body = doc.get("body", {}) or {}
        content = body.get("content", []) or []

        html_out = []
        open_list_stack = []  # stack of ('ul'|'ol')
        current_list_id = None

        def close_all_lists():
            nonlocal open_list_stack, html_out, current_list_id
            while open_list_stack:
                tag = open_list_stack.pop()
                html_out.append(f"</{tag}>")
            current_list_id = None

        def ensure_list(list_id: str, nesting_level: int):
            """Open/close <ul>/<ol> tags so that nesting matches the paragraph nesting level."""
            nonlocal open_list_stack, html_out, current_list_id
            list_def = lists_meta.get(list_id, {})
            nesting = list_def.get("listProperties", {}).get("nestingLevels", [])
            # heuristic: presence of glyphType suggests ordered list
            ordered = False
            if nesting and nesting_level < len(nesting):
                ordered = bool(nesting[nesting_level].get("glyphType"))
            # If Docs didn’t specify, default to unordered
            tag = "ol" if ordered else "ul"

            # if we’re switching lists (new list_id), close all prior
            if current_list_id != list_id:
                close_all_lists()
                current_list_id = list_id

            # adjust nesting depth
            depth = len(open_list_stack)
            while depth < (nesting_level + 1):
                html_out.append(f"<{tag}>")
                open_list_stack.append(tag)
                depth += 1
            while depth > (nesting_level + 1):
                last = open_list_stack.pop()
                html_out.append(f"</{last}>")
                depth -= 1

        def render_inline(elements: list) -> str:
            parts = []
            for el in elements or []:
                tr = el.get("textRun")
                if not tr:
                    continue
                text = tr.get("content", "")
                if not text:
                    continue
                tstyle = tr.get("textStyle", {}) or {}
                esc = html.escape(text, quote=False)

                # link
                link = (tstyle.get("link") or {}).get("url")
                # inline formatting
                if tstyle.get("bold"):
                    esc = f"<strong>{esc}</strong>"
                if tstyle.get("italic"):
                    esc = f"<em>{esc}</em>"
                if tstyle.get("underline"):
                    esc = f"<u>{esc}</u>"
                if tstyle.get("strikethrough"):
                    esc = f"<s>{esc}</s>"

                if link:
                    esc = f'<a href="{html.escape(link)}" target="_blank" rel="noopener noreferrer">{esc}</a>'
                parts.append(esc)
            return "".join(parts)

        for block in content:
            para = block.get("paragraph")
            if not para:
                # Ignore tables/images for now (can extend later)
                continue

            pstyle = (para.get("paragraphStyle") or {}).get("namedStyleType", "")
            bullet = para.get("bullet")
            elements = para.get("elements", [])

            if bullet:
                # list item
                list_id = bullet.get("listId")
                nesting_level = int(bullet.get("nestingLevel", 0))
                ensure_list(list_id, nesting_level)
                inner = render_inline(elements).rstrip("\n")
                html_out.append(f"<li>{inner}</li>")
                continue  # don’t close lists yet

            # non-list paragraph → close any open lists
            if open_list_stack:
                close_all_lists()

            # headings vs paragraph
            tag = "p"
            if pstyle.startswith("HEADING_"):
                # map HEADING_1..6 -> h1..h6
                try:
                    level = int(pstyle.split("_")[1])
                    if 1 <= level <= 6:
                        tag = f"h{level}"
                except Exception:
                    tag = "h2"
            inner = render_inline(elements).rstrip("\n")
            # skip empty trailing paragraph the API often gives
            if not inner.strip():
                continue
            html_out.append(f"<{tag}>{inner}</{tag}>")

        # close any lists left open
        if open_list_stack:
            close_all_lists()

        return "".join(html_out)
