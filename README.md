# PDF Data Cleaner
I did this project for a client back when I was still learning GCP, the purpose of this project is to extract tabular data from PDF and then clean it and store it in BigQuery.

## Getting Environment Ready

1. Turn on the following APIs in Google Cloud Console.
- Vision API
- BigQuery API
- Cloud Run API
- Functions API
- Storage API

2. Create 3 Buckets in the GCS as shown in the figure below.
- First one is where the user will upload the pdf files. I named it `dark-foundry-340620-companydata`.
- Second one is where the processed files will be stored. I named it `dark-foundry-340620-companydata-processed`.
- Third one is used to store `Cloud Vision` results temporarily (Must be always empty). I named it `dark-foundry-340620-tmp`.

![image](https://github.com/shozy786/PDF-Data-Cleaner/assets/65444486/205c8a19-bdfd-4d22-98a7-1629badf712f)

3. Create a BigQuery dataset to store results. I named it `companydata`.
4. Create a new service account and give it the role of `Owner` and download its `key`. Keep this key file in your own folder. (At this moment, I know and have learnt that this step was not necessary)

## Making Necessary Code Changes:
5. In extract.py, change the following lines with your own info.
- `BUCKET="your bucket name where user will store pdf files"`
- `PROCESSED_BUCKET="your bucket name where files will be stored after processing"`
- `TABLE_ID="your project name.your bq dataset name.your bq table name"`
- `LOGIN_FILE="The key file that you generated in the previous section” Make sure that it is the same path as extract.py"`

6. In target.py, change the following things.
- `gcs_destination_uri= "name of the temporary bucket to be used by VISION API prefixed with gs://"`
- `LOGIN_FILE= "name of your json key file generated in the previous section"`
- `TMP_BUCKET_NAME= "name of the temporary bucket to be used by VISION API"`

## Deployment
7. Install gcloud CLI on your local pc. Open Command Prompt and navigate to the folder where you made your code changes. Type this command: `gcloud run deploy`. Press return.
8. Login to your google account if prompted. Allow unauthorized access. When deployment is succeeded, you’ll receive a URI that will run the code if it is hit by a get request. 
9. Copy that URL.
10. Go to the main.py in function-source folder and replace URL in it with your own URL that you got from Cloud Run. It should be like `requests.get('your url')`
11. Create a new Cloud Function select Python 3.x runtime. Select Trigger Type: Cloud Storage and Event Type: Finalize/Create.
12. Select Bucket as your bucket where user will store PDF files. Click Save.
13. Copy the code from `function-source/main.py` to the cloud function’s main.py.
14. Copy the code from `function-source/requirements.txt` to cloud function’s requirements.txt.
15. Deploy the function.
Test it by uploading the PDF file in your PDF bucket and refresh the page after a couple of minutes it will be gone and new rows will be added to your BigQuery table.

