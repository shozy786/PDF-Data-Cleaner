def extractData():
    from google.cloud import storage,bigquery
    from google.oauth2 import service_account
    import json
    from io import StringIO
    from tabula import read_pdf
    import re
    import pandas as pd
    from datetime import datetime
    import target

    BUCKET = 'dark-foundry-340620-companydata'
    PROCESSED_BUCKET = 'dark-foundry-340620-companydata-processed'
    TABLE_ID = 'dark-foundry-340620.companydata.companies'
    LOGIN_FILE = 'dark-foundry-340620-ebf4ab8b7ad2.json'

    
    LOCAL_FILE = 'data.pdf'
    service_account_info = json.loads(open(LOGIN_FILE,'r').read())
    credentials = service_account.Credentials.from_service_account_info(service_account_info)

    storage_client = storage.Client(credentials = credentials)
    bucket = storage_client.get_bucket(BUCKET)
    processed_bucket = storage_client.get_bucket(PROCESSED_BUCKET)

    client = bigquery.Client(credentials = credentials)



    for blob in bucket.list_blobs():
        gcs_path = "gs://"+"".join([i+'/' for i in blob.id.split('/')[:-1]])
        gcs_path = gcs_path[:-1]
        target.sendToVision(gcs_path)
        

        blobData = blob.download_as_string()
        open(LOCAL_FILE,"wb").write(blobData)
        df = read_pdf(LOCAL_FILE,pages='all')
        cities = target.CITYNAMES
        contactName = []
        title = []
        companyName = []
        phone = []
        address = []
        city = []
        contactType = []
        emailAddress = []
        for d in df:
            if len(d) > 1:
                values = d['Contact Name'][2:].to_list()
                for i in values:
                    if type(i) == float:
                        continue
                    #Splitting
                    fields = i.split('\r')
                    if len(fields) < 3:
                        continue
                    #Extract Phone
                    phoneNumber = re.findall(r"(\(\d\d\d\) \d\d\d-\d\d\d\d)", i)
                    if len(phoneNumber) > 0:
                        phone += phoneNumber
                    else:
                        phone += [ None ]
                    #Extract Email
                    email = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',i)
                    if len(email) > 0:
                        emailAddress += email
                        i = i.replace(email[0], "")
                    else:
                        emailAddress += [None]
                    #Extract City
                    cityExists = False
                    for k in range(len(cities)):
                        if cities[k] in i:
                            cityExists = True
                            city += [cities[k]]
                            i = i.replace(cities[k],"")
                            break
                    if not cityExists:
                        city += [None]
                    fields = i.split('\r')
                    #Extracting Name
                    nameTil = fields[0].find('(')
                    if nameTil != -1:
                        contactName += [fields[0][:nameTil]]
                    else:
                        contactName += [fields[0]]
                    ##############
                    if len(fields) == 3:
                        title += [None]
                        contactType += [fields[1]]
                        isAddress = len(re.findall(r'\d',fields[2])) > 0
                        if isAddress:
                            if len(fields[2]) > 0 and fields[2][0].isalpha():
                                address += [None]
                            else:
                                address += [fields[2]]
                            companyName += [None]
                        else:
                            address += [None]
                            if len(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',fields[2])) > 0:
                                companyName += [None]
                            else:
                                if fields[2][0].isdigit():
                                    companyName += [None]
                                else:
                                    companyName += [fields[2]]
                    elif len(fields) == 4:
                        title += [None]
                        contactType += [fields[1]]
                        if len(re.findall(r'\d.*',fields[2])) > 0:
                            address += [re.findall(r'\d.*',fields[2])[0]]
                        else:
                            if len(fields[2]) > 0 and fields[2][0].isalpha():
                                address += [None]
                            else:
                                address += [fields[2]]
                        if fields[3][0].isdigit():
                            companyName += [None]
                        else:    
                            companyName += [fields[3]]
                    elif len(fields) == 5:
                        if len(re.findall(r'\D*',fields[2])[0]) > 3:
                            title += [re.findall(r'\D*',fields[2])[0]]
                        else:
                            title += [None]
                        contactType += [fields[1]]
                        if len(re.findall(r'\d.*',fields[2])) > 0:
                            address += [re.findall(r'\d.*',fields[2])[0]]
                        else:
                            if len(fields[2]) > 0 and fields[2][0].isalpha():
                                address += [None]
                            else:
                                address += [fields[2]]
                        if len(re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',fields[4])) > 0:
                            companyName += [None]
                        else:
                            if fields[4][0].isdigit():
                                companyName += [None]
                            else:
                                companyName += [fields[4]]
        data = pd.DataFrame({
        "ContactName":contactName,
        "Title":title,
        "CompanyName":companyName,
        "Phone":phone,
        "Address":address,
        "City":city,
        "ContactType":contactType,
        "EmailAddress":emailAddress
        })
        data['createdDate'] = datetime.now()
        data['createdBy'] = blob.name
        job_config = bigquery.LoadJobConfig(autodetect = True)
        job = client.load_table_from_dataframe(data, TABLE_ID, job_config=job_config)
        print(job.result())
        outputFileName = blob.name.replace('.pdf',"-"+str(datetime.now())+'.pdf')
        print("File: " + outputFileName + " saved!!")
        bucket.copy_blob(blob, processed_bucket, outputFileName)
        blob.delete()