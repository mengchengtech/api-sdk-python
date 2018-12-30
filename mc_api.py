import hmac
import hashlib
import base64
import requests
import logging
import time
from urllib.parse import urljoin
from email import utils

logger = logging.getLogger(__name__)

class open_api_client:
    def __init__(self, baseUrl, accessId, secretKey):
        self._baseUrl = baseUrl
        self._accessId = accessId
        self._secretKey = secretKey
    
    def __sort_url_params(self, url):
        arr = url.split('?')
        if len(arr) == 1:
            return url
        arr2 = arr[1].split('&')
        arr2.sort()
        sorted_url = arr[0] + '?' + arr2[0]
        for i in range(1, len(arr2)):
            sorted_url += '&' + arr2[i]
        return sorted_url

    def get(self, url):
        url = self.__sort_url_params(urljoin(self._baseUrl, url))
        logger.info('getting url: %s' % url)
        headers = {}
        headers['Content-Type'] = 'text/html'
        headers['Date'] = utils.formatdate(time.time(), usegmt=True)
        headers['Host'] = 'api.mctech.vip'
        content = 'GET\n' + headers['Content-Type'] + '\n' + headers['Date'] + '\n' + url
        signature = hmac.new(str.encode(self._secretKey), str.encode(content, encoding = "utf8"), hashlib.sha1).digest()
        signature = bytes.decode(base64.b64encode(signature))
        headers['Authorization'] = 'IWOP ' + self._accessId + ':' + signature
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            msg = 'request fail, status code: %d, response: \n%s' % (response.status_code, response.text)
            raise Exception(msg)
        return response
    
    # TODO: other http verb