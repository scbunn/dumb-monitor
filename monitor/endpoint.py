"""Request Endpoints.

"""
import logging
import datetime
import requests
import time


class GetTaxSoapEndpoint(object):
    """GetTax SOAP Endpoint."""

    def __init__(self):
        self.url = 'https://www.google.com'
        self.payload = {}
        self.logger = logging.getLogger(__name__)

    def request(self):
        timestamp = time.time() * 1000
        start = datetime.datetime.now(datetime.timezone.utc)
        try:
            response = requests.request('GET', self.url, **self.payload)
        except requests.exceptions.RequestException as ex:
            pass

        end = datetime.datetime.now(datetime.timezone.utc)
        return [
            {
                'metric': 'dumb.monitor.GetTax.SOAP.elapsed',
                'value': (end - start).total_seconds() * 1000.0,
                'timestamp': timestamp,
            },
            {
                'metric': 'dumb.monitor.GetTax.SOAP.TTFB',
                'value': sum((r.elapsed for r in response.history),
                             response.elapsed).total_seconds() * 1000.0,
                'timestamp': timestamp,
            }
        ]
