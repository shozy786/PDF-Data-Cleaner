import json
import re
from google.cloud import vision,storage
from google.oauth2 import service_account


gcs_destination_uri = 'gs://dark-foundry-340620-tmp/'
mime_type = 'application/pdf'
LOGIN_FILE = 'dark-foundry-340620-ebf4ab8b7ad2.json'
TMP_BUCKET_NAME = 'dark-foundry-340620-tmp'

# Service Account
service_account_info = json.loads(open(LOGIN_FILE,'r').read())
credentials = service_account.Credentials.from_service_account_info(service_account_info)
# Vision Client
client = vision.ImageAnnotatorClient(credentials=credentials)
feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

CITYNAMES = []

def sendToVision(gcs_source_uri):
    global CITYNAMES
    gcs_source = vision.GcsSource(uri=gcs_source_uri)
    input_config = vision.InputConfig(gcs_source=gcs_source, mime_type=mime_type)

    gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
    output_config = vision.OutputConfig(gcs_destination=gcs_destination)

    async_request = vision.AsyncAnnotateFileRequest(
        features=[feature], input_config=input_config,
        output_config=output_config)

    operation = client.async_batch_annotate_files(
        requests=[async_request])
    print(operation.result())

    # Once the request has completed and the output has been
    # written to GCS, we can list all the output files.
    storage_client = storage.Client(credentials = credentials)

    
    bucket = storage_client.get_bucket(TMP_BUCKET_NAME)

    # List objects with the given prefix, filtering out folders.
    blob_list = bucket.list_blobs()
    fileData = []
    for blob in blob_list:
        json_string = blob.download_as_string()
        response = json.loads(json_string)
        for res in response['responses']:
            annotation = res['fullTextAnnotation']
            fileData += annotation['text'].split('\n')
        blob.delete()

    for i in fileData:
        res = re.findall('(\w.+\w\s\d\d\d\d\d)',i)
        if len(res) > 0:
            CITYNAMES += [res[0]]
    
        