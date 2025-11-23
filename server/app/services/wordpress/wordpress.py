# ================= IMPORTS ==================
import base64
import requests

from server.app.services.wordpress.media.crud import delete_media_, delete_medias_, get_media_, replace_media_, upload_media_from_bytes_
from server.app.services.wordpress.meta.meta_content import get_existing_meta_, update_meta_yoast_
from server.app.services.wordpress.meta.author import find_author_id_
from server.app.services.wordpress.cpt.crud import create_cpt_

import logging
# ================= FUNCTIONS ==================

# Check Post Type Endpoint
# https://client_name/wp-json/wp/v2/types

class WordpressHelper:

    def __init__(self, creds):

        self.app_user = creds.get('KEY').strip()
        self.app_pass = creds.get('SECRET').strip()
        self.domain = creds.get('URL').strip()
        if not self.domain.endswith("/"):
            self.domain += "/"

        self.url = f"{self.domain}wp-json/wp/v2"

        creds_str = f"{self.app_user}:{self.app_pass}"
        token = base64.b64encode(creds_str.encode())

        self.header = {
            "Authorization": "Basic " + token.decode("utf-8"),
            # Pretend to be curl (or a browser)
            "User-Agent": "curl/8.4.0",
            "Accept": "application/json",
        }

    # =================================
    # =========== TESTING =============
    # =================================
    def test_connection(self):
        endpoint = f"{self.url}/users/me"
        try:
            response = requests.get(endpoint, headers=self.header)
            if response.status_code == 200:
                # print("Connection to WordPress API successful.")
                return True
            else:
                logging.error(f"Connection failed: {response.status_code} - {response.text}")
                return False
        except requests.RequestException as e:
            logging.error(f"An error occurred while testing the connection: {e}")
            return False

    def testEndpoint(self, endpoint: str):
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.url}/{endpoint}"

        try:
            response = requests.get(url, headers=self.header)
            print(f"Status Code: {response.status_code}")
            try:
                return response.json()
            except ValueError:
                print("Response is not valid JSON:")
                return None
        except requests.RequestException as e:
            print(f"An error occurred while testing endpoint: {e}")
            return None
        
    # =================================
    # =========== MEDIA ===============
    # =================================

    def upload_media_from_bytes( self, img_bytes: bytes, filename: str, mime: str = "image/png", title: str | None = None, alt_text: str | None = None) -> int:
        return upload_media_from_bytes_(self, img_bytes, filename, mime, title, alt_text)
    
    # def delete_media(self, id):
    #     return delete_media_(self, id)
        
    # def delete_all_media(self):
    #     return delete_medias_(self)

    # def get_media_by_id(self, media_id):
    #     return get_media_(self, media_id)

    # def replace_media(self, media_id, file_path):
    #     return replace_media_(self, media_id, file_path)
            
    # =================================
    # ============= META ==============
    # =================================
    def get_existing_meta(self, rest_base: str, post_id: int):
        return get_existing_meta_(self, rest_base, post_id)
    
    def update_meta_yoast(self, rest_base: str, post_id: int, meta_description: str | None, meta_title: str | None):
        return update_meta_yoast_(self, rest_base, post_id, meta_description, meta_title)

    def find_author_id(self, name: str):
        return find_author_id_(self, name)
    
    # =================================
    # ============= CPT's =============
    # =================================
    
    def create_cpt(self, rest_base: str, payload: dict) -> dict:
        return create_cpt_(self, rest_base, payload)
    
# ================= MAIN ==================
if __name__ == "__main__":
    wp_helper = WordpressHelper()
