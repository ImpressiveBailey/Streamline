from server.app.services.google.GoogleServiceHelper import GoogleServiceHelper

SERVICE_ACCOUNT_FILE = 'service-account.json'
helper = GoogleServiceHelper(SERVICE_ACCOUNT_FILE)

doc_id = 'YOUR_GOOGLE_DOC_ID'
document = helper.get_doc(doc_id)

print(document['title'])
print(document['body']['content'][:5])
