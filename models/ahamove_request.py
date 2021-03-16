# -*- coding: utf-8 -*-

import logging
import requests

_logger = logging.getLogger(__name__)

DEFAULT_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJhaGEiLCJ0eXAiOiJ1c2VyIiwiY2lkIjoiODQ4Mzg0Mzk0ODMiLCJzdGF0dXMiOiJPTkxJTkUiLCJlb2MiOm51bGwsIm5vYyI6IlwiUGhhbSBUaGkgTmdvYyBNYWlcIiIsImN0eSI6IkhBTiIsImFjY291bnRfc3RhdHVzIjoiQUNUSVZBVEVEIiwiZXhwIjoxNjA5MjExNDUzLCJwYXJ0bmVyIjoiYXJyb3doaXRlY2gifQ.wDMPf78V7xH3x74T1nRmnWME5Cquf5KsMXJLbLIpWKo'

class AhamoveRequest():
    def __init__(self, prod_environment, is_auth=True, api_token=DEFAULT_TOKEN):
        # Product and Testing url
        self.endurl = 'https://api.ahamove.com/'
        if not prod_environment:
            self.endurl = 'https://apistg.ahamove.com/'

        # Basic detail require
        self.api_token = api_token
        self.is_auth = is_auth

    def do_request(self, uri, params, headers, type='POST'):
        _logger.debug("Uri: %s - Type: %s - Headers: %s - Params: %s !",
                      uri, type, headers, params)
        if self.is_auth:
            params['token'] = self.api_token
        if type.upper() in 'GET':
            res = requests.get(self.endurl + uri, params=params, headers=headers)
            # _logger.debug("Response: %s", res.text)
        elif type.upper() in 'POST':
            res = requests.post(self.endurl+uri, params=params, headers=headers)
            _logger.debug("Response: %s", res.text)
        return res

