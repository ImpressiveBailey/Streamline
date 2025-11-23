# server/app/utils/clients/georges_cameras/collection_page.py
from bs4 import BeautifulSoup
import os
from server.app.utils.formatters.extraction import extract_handle, extract_slug
from server.config.ConfigHelper import ConfigHelper
from server.app.utils.debugging.console_logging import log_error, log_info
from server.app.services.wordpress.wordpress import WordpressHelper
from server.app.services.open_ai.open_ai import OpenAIHelper

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


def upload_page(page: dict):
    # UPLOAD CREDS: {'URL': 'xxx', 'WP_KEY': 'xxx', 'WP_SECRET': 'xxx'}
    log_info("Starting Page Upload...")
    raw_creds = ConfigHelper.get_client_env("CRYPTO_MARKET_NEWS")
    creds = {"KEY": raw_creds.get("WP_KEY"), "SECRET": raw_creds.get("WP_SECRET"), "URL": raw_creds.get("URL")}
    endpoint = "learn"
    gpt = OpenAIHelper()


    try:
        log_info("Formatting Data...")
        data = page['data']
        wp = WordpressHelper(creds)
        # 3) Smoke test: can we hit the API root?
        if not wp.test_connection():
            return "Failed WordPress API connection"
        
        page_url = page.get("pageUrl") or ""
        slug = ""
        if page_url:
            try:
                slug = extract_slug(page_url) or ""
            except Exception:
                slug = ""

        payload = {
          "title": data.get('pageHeading'),
          "slug": slug,
          "status": "draft",
          "content": data.get('body_content'),
          "meta_title": data.get('metaTitle'),
          "meta_description": data.get('metaDescription'),
        }

        log_info("Finding Author...")
        author_name = data.get("author") or None
        author_id = wp.find_author_id(author_name)
        if author_id:
            payload["author"] = author_id

        log_info("Generating Image...")
        heading = data.get('pageHeading')
        img_prompt = (
              "Generate a featured blog image for my crypto market news site. The image should be:"
              "- 1:1."
              "- Futuristic"
              "- Contain no words"
              f"- Be relevent to the title: {heading}"
              "- Use https://cryptomarketnews.com.au/wp-content/uploads/2025/11/Crpyto-Market-News-1-3.webp as an example"
          )
        img = gpt.generate_image(prompt=img_prompt, model="dall-e-3", size="1024x1024")

        if img and img.get("bytes"):
            try:
                filename = f"{slug}.png"
                log_info("Uploading Image...")
                media_id = wp.upload_media_from_bytes(
                    img_bytes=img["bytes"],
                    filename=filename,
                    mime=img.get("mime", "image/png"),
                    title=heading or slug,
                    alt_text=heading or slug,
                )

                # Attach as featured image
                payload["featured_media"] = media_id
            except Exception as me:
                log_error(me)

        # 6) Finally create the CPT entry
        log_info("Uploading Page...")
        wp.create_cpt(endpoint, payload)
        
        return True

    except Exception as e:
        # This will be shown in the upload summary’s "error" field
        return f"Upload error: {e}"
    
    



    # return True for success
    # return failure_message for fail
    # wp.upload_custom_post_type("endpoint", payload)               # create
    # wp.upload_custom_post_type("endpoint", payload, post_id)      # update ID 123


    # ENDPOINT = learn
    # post_id = 123