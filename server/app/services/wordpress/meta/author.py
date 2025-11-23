import requests
import logging

def find_author_id_(self, name: str):
    """
    Best-effort: find WP user ID by searching the users endpoint.
    Returns user ID int or None.
    """
    if not name:
        return None

    try:
        resp = requests.get(
            f"{self.url}/users",
            headers=self.header,
            params={"search": name},
            timeout=20,
        )
    except requests.RequestException as e:
        logging.error(f"Error searching users for author '{name}': {e}")
        return None

    if resp.status_code != 200:
        logging.error(
            f"User search failed for '{name}': {resp.status_code} - {resp.text[:200]}"
        )
        return None

    try:
        users = resp.json()
    except ValueError:
        logging.error(f"User search returned non-JSON for '{name}'")
        return None

    if not users:
        return None

    # naive: first match
    return users[0].get("id")
