from server.app.utils.formatters.parsing import html_to_richtext, slugify
import json


def format_faqs(faqs, collection_handle):
        # --- Build FAQ handles & FAQ metaobject rows ---
    faq_refs = []          # for the collection metafield (list.metaobject_reference)
    faq_rows = []          # metaobject CSV rows

    for faq in faqs:
        question = (faq.get("q") or "").strip()
        answer_html = faq.get("a") or ""
        if not question:
            continue

        # faq handle: collection-handle-faq-question-slug
        faq_slug = slugify(question)
        faq_handle = f"{collection_handle}-faq-{faq_slug}"
        faq_ref = f"faq.{faq_handle}"
        faq_refs.append(faq_ref)

        # rich_text answer
        answer_rich = html_to_richtext(answer_html)
        answer_rich_json = json.dumps(answer_rich, ensure_ascii=False)

        # Two rows per FAQ metaobject, per your example:
        # Row 1: question
        faq_rows.append({
            "Handle": faq_handle,
            "Command": "MERGE",
            "Display Name": question,
            "Status": "Active",
            "Definition: Handle": "faq",
            "Definition: Name": "FAQ",
            "Top Row": "TRUE",
            "Row #": 1,
            "Field": "question",
            "Value": question,
        })
        # Row 2: answer (rich_text_field JSON)
        faq_rows.append({
            "Handle": faq_handle,
            "Command": "MERGE",
            "Display Name": question,
            "Status": "Active",
            "Definition: Handle": "faq",
            "Definition: Name": "FAQ",
            "Top Row": "",
            "Row #": 2,
            "Field": "answer",
            "Value": answer_rich_json,
        })

    return faq_rows, faq_refs