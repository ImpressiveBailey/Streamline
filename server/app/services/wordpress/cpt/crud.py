import requests
import logging

def create_cpt_(self, rest_base: str, payload: dict) -> dict:
    if not rest_base:
        raise ValueError("rest_base is required for create_cpt")

    rest_base = rest_base.strip().strip("/")

    meta_title = payload.pop("meta_title", None)
    meta_description = payload.pop("meta_description", None)

    url = f"{self.url}/{rest_base}"

    try:
        resp = requests.post(
            url,
            headers=self.header,
            json=payload,
            timeout=30,
        )
    except requests.RequestException as e:
        raise Exception(f"Request error during creation at {rest_base}: {e}")

    if resp.status_code not in (200, 201):
        raise Exception(
            f"Creation at {rest_base} failed: "
            f"{resp.status_code} - {resp.text[:300]}"
        )

    try:
        page_data = resp.json()
    except ValueError:
        raise Exception(
            f"Creation at {rest_base} succeeded but returned non-JSON body: "
            f"{resp.text[:300]}"
        )

    # Optionally update Yoast meta
    if (meta_title or meta_description) and hasattr(self, "update_meta_yoast"):
        try:
            post_id = page_data.get("id")
            if post_id:
                self.update_meta_yoast(
                    rest_base=rest_base,
                    post_id=post_id,
                    meta_description=meta_description,
                    meta_title=meta_title,
                )
        except Exception as e:
            logging.error(f"Failed to update Yoast meta for CPT {rest_base}: {e}")

    return page_data
