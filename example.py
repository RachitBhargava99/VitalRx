import requests, json

apikey = 'UwWvECxjK1uFHPrXqIduyVD2dGdjwtkYupnli1FHyHeg'

url = "https://iam.bluemix.net/oidc/token"
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = "apikey=" + apikey + "&grant_type=urn:ibm:params:oauth:grant-type:apikey"
IBM_cloud_IAM_uid = "bx"
IBM_cloud_IAM_pwd = "bx"
response = requests.post(url, headers=headers, data=data, auth=(IBM_cloud_IAM_uid, IBM_cloud_IAM_pwd))
iam_token = response.json()["access_token"]

# print(iam_token)

header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + iam_token,
          'ML-Instance-ID': 'cd608862-dcef-451a-87f0-1ba3aec60ebc'}

payload_scoring = {"input_data": [{"fields": ["gender", "Age", "Non-Invasive BP Systolic",
                                              "Non-Invasive BP Diastolic", "Temperature (F)",
                                              "O2 Saturation", "Heart Rate", "Respiratory Rate",
                                              "Pain Score"], "values": [["Male", 20,
                                                                         120, 80,
                                                                         98.7, 93,
                                                                         72, 16,
                                                                         None]]}]}

response_scoring = json.loads(requests.get(
    'https://us-south.ml.cloud.ibm.com/v4/deployments',
    headers=header).text)

print(response_scoring)


