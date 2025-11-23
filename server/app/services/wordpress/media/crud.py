
# ================= IMPORTS ==================
import requests
import os
from concurrent.futures import ThreadPoolExecutor

# ================= FUNCTIONS ==================
def delete_media_(self, id):
    # integration
    endpoint = f"{self.url}/media/{id}?force=true"
    try:
        response = requests.delete(endpoint, headers=self.header)
        if response.status_code in [200, 204]:
            print(f"Media ID {id} successfully deleted.")
            return response.json()
        else:
            print(f"Failed to delete Media ID {id}: {response.status_code} - {response.text}")
            return {"error": response.text}
    except requests.RequestException as e:
        print(f"An error occurred while deleting Media ID {id}: {e}")
        return {"error": str(e)}
    
def delete_medias_(self):
    per_page = 100
    page = 1
    total_deleted = 0

    while True:
        endpoint = f"{self.url}/media"
        params = {"per_page": per_page, "page": page}

        try:
            response = requests.get(endpoint, headers=self.header, params=params)
            if response.status_code in [200, 204]:
                media_items = response.json()
                if not media_items:
                    break

                print(f"\nProcessing page {page} with {len(media_items)} items")
                media_ids = [media['id'] for media in media_items]

                # Concurrent deletion of media items
                with ThreadPoolExecutor(max_workers=10) as executor:
                    results = list(executor.map(self.delete_media, media_ids))
                    total_deleted += sum(1 for result in results if result)

                page += 1
            else:
                print(f"Failed to fetch media page {page}: {response.status_code}")
                break

        except requests.RequestException as e:
            print(f"Error on page {page}: {e}")
            break

    print(f"\nTotal media items deleted: {total_deleted}")

def get_media_(self, media_id):
    """Retrieve media details by ID."""
    endpoint = f"{self.url}/media/{media_id}"
    try:
        response = requests.get(endpoint, headers=self.header)
        if response.status_code in [200, 204]:
            return response.json()
        else:
            print(f"Failed to fetch media ID {media_id}: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        print(f"Error fetching media ID {media_id}: {e}")
        return None

def replace_media_(self, media_id, file_path):
    filename = os.path.basename(file_path)
    endpoint = f"{self.url}/media/{media_id}"

    headers = self.header.copy()
    headers["Content-Disposition"] = f'attachment; filename="{filename}"'

    with open(file_path, "rb") as file:
        files = {"file": (filename, file, "image/jpeg")}  # Change MIME type if needed
        response = requests.post(endpoint, headers=headers, files=files)

    if response.status_code in [200, 204]:
        media_data = response.json()
        print(f"Media ID {media_id} updated successfully: {media_data.get('source_url')}")
        return media_data
    else:
        print(f"Update failed for Media ID {media_id}: {response.status_code} - {response.text}")
        return None


def upload_media_from_bytes_(
        self,
        img_bytes: bytes,
        filename: str,
        mime: str = "image/png",
        title: str | None = None,
        alt_text: str | None = None,
    ) -> int:
        """
        Upload an image to WordPress media library from raw bytes.
        Returns the media ID on success, or raises on failure.
        """
        endpoint = f"{self.url}/media"

        headers = self.header.copy()
        # Do NOT set Content-Type manually; requests will handle multipart boundary.

        data = {}
        if title:
            data["title"] = title
        if alt_text:
            data["alt_text"] = alt_text

        files = {
            "file": (filename, img_bytes, mime),
        }

        try:
            resp = requests.post(
                endpoint,
                headers=headers,
                files=files,
                data=data,
                timeout=60,
            )
        except requests.RequestException as e:
            raise Exception(f"Media upload request error: {e}")

        if resp.status_code not in (200, 201):
            raise Exception(
                f"Media upload failed: {resp.status_code} - {resp.text[:300]}"
            )

        try:
            media_data = resp.json()
        except ValueError:
            raise Exception(
                f"Media upload succeeded but returned non-JSON body: {resp.text[:300]}"
            )

        media_id = media_data.get("id")
        if not media_id:
            raise Exception(f"Media upload response missing 'id': {media_data}")

        return media_id