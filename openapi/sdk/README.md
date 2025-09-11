# api-sdk-python

## python version
tested in python 3.5 / 3.6

## package dependency

```bash
pip3 install httpx
```

## code sample

```python
from kestrel_authentication import GatewayAuthentication

baseUrl = 'https://api.mctech.vip'
accessId = 'your accessId'
secretKey = 'your secretKey'
project_api_url = '/org-api/projects?start=0&limit=2'

client = httpx.Client(auth=GatewayAuthentication(access_id, secret_key))
client.base_url = base_url
json = client.get(project_api_url).json()
print(len(json))
```
