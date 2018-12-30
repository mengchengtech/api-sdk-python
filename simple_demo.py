import time
import requests
import json
import logging
import sys
import threading
import mc_api

baseUrl = 'https://api.mctech.vip'
accessId = 'xxxx'
secretKey = 'xxxx'
project_api_url = '/org-api/projects?start=0&limit=2'

client = mc_api.open_api_client(baseUrl, accessId, secretKey)
json = client.get(project_api_url).json()
print(len(json))