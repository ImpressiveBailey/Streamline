# server/app/utils/clients/georges_cameras/collection_page.py
from bs4 import BeautifulSoup

MANIFEST = {
  "version": "1.0",
  "fields": [
    {
      "label": "Handle",
      "path": "data.handle",                      # Data Key
      "type": "link",
      "upload": {"metafield": "handle"}           # Upload Key
    },
    {
      "label": "Meta Title",
      "path": "data.metaTitle",
      "type": "text",
      "upload": {"metafield": "seo.title"}
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
    
    return (
        {
            # General
            "pageUrl": '',
            "handle": '',
            "pageNumber": '',

            # Meta
            "pageHeading": '',
            "metaTitle": '',
            "metaDescription": '',

            # Content
            "topContentHtml": '',
            "bottomContentHtml": '',
            "faq": '',
        },
        MANIFEST,
    )

def convert_page_to_csv():
  csv = ""
  return csv



def upload_page():
  status = ""
  return status