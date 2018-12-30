# api-sdk-python

## python version
tested in python 3.5 / 3.6

## package dependency

```
pip install requests
```

## code sample
```
import mc_api

baseUrl = 'https://api.mctech.vip'
accessId = 'your accessId'
secretKey = 'your secretKey'
project_api_url = '/org-api/projects?start=0&limit=2'

client = mc_api.open_api_client(baseUrl, accessId, secretKey)
json = client.get(project_api_url).json()
print(len(json))
```