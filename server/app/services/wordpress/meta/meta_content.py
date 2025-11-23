import requests
import logging

def get_existing_meta_(self, rest_base: str, post_id: int) -> dict:
    """
    Fetch existing post meta for a CPT or core type.

    rest_base: 'learn', 'pages', 'posts', etc.
    """
    rest_base = rest_base.strip().strip("/")
    endpoint = f"{self.url}/{rest_base}/{post_id}"

    try:
        response = requests.get(endpoint, headers=self.header, timeout=20)
    except requests.RequestException as e:
        logging.error(f"Error fetching existing meta from {endpoint}: {e}")
        return {}

    if response.status_code != 200:
        logging.error(
            f"get_existing_meta failed {response.status_code} - {response.text[:200]}"
        )
        return {}

    try:
        existing_data = response.json()
    except ValueError:
        logging.error(f"get_existing_meta: non-JSON response from {endpoint}")
        return {}

    existing_meta = existing_data.get("meta") or {}
    if not isinstance(existing_meta, dict):
        # Make sure we always return a mapping
        existing_meta = {}

    return existing_meta


def update_meta_yoast_(self, rest_base: str, post_id: int,
                       meta_description: str | None,
                       meta_title: str | None) -> bool:
    """
    Update Yoast meta for a CPT or core type.

    rest_base: 'learn', 'pages', 'posts', etc.
    """
    rest_base = rest_base.strip().strip("/")
    endpoint = f"{self.url}/{rest_base}/{post_id}"

    existing_meta = self.get_existing_meta(rest_base, post_id)

    # Start with a copy to avoid mutating original
    updated_meta = dict(existing_meta)

    # Only overwrite fields if we actually have values
    if meta_title:
        updated_meta["_yoast_wpseo_title"] = meta_title
    if meta_description:
        updated_meta["_yoast_wpseo_metadesc"] = meta_description

    # If we still have no meta keys and no new values, do nothing
    if not updated_meta:
        logging.info(f"No Yoast meta to update for {rest_base}/{post_id}")
        return True

    update_payload = {"meta": updated_meta}

    try:
        update_response = requests.post(  # PUT also works; POST is okay for update here
            endpoint,
            json=update_payload,
            headers=self.header,
            timeout=20,
        )
    except requests.RequestException as e:
        logging.error(f"Meta update request error for {endpoint}: {e}")
        return False

    if update_response.status_code == 200:
        return True
    else:
        logging.error(
            f"Meta update failed: {update_response.status_code} "
            f"- {update_response.text[:200]}"
        )
        return False
