from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

class GoogleServiceHelper:
    def __init__(self, service_account_file: str, scopes=SCOPES):
        self.creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )
        self.services = {}

    def get_service(self, api_name: str, version: str):
        """
        Return a service client for a specific Google API.
        Caches the client for reuse.
        """
        key = f"{api_name}_{version}"
        if key not in self.services:
            self.services[key] = build(api_name, version, credentials=self.creds)
        return self.services[key]

    def get_doc(self, doc_id: str) -> dict:
        """
        Fetches a Google Doc by ID and returns its JSON structure.
        """
        docs_service = self.get_service('docs', 'v1')
        doc = docs_service.documents().get(documentId=doc_id).execute()
        return doc