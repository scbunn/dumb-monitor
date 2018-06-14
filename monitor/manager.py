"""Monitor Manager.

The monitor manager is responsible for managing the monitor thread pools and
requests.

Manager lifecycle:
    - Spawn request thread.  The request thread drops a new request on the
      queue every N seconds.
    - Spawn Monitor thread pool.  The monitor thread pool pop an item from the
      queue and makes a request to the `Endpoint`
    - Spawn Reporter Thread.  The reporter threads grabs all the results off the
      results queue and reports them to the data source.

"""
import datetime
import logging
import os
import signalfx
import socket
import time
import threading
import queue
from signalfx.aws import AWS_ID_DIMENSION, get_aws_unique_id

class Manager(object):

    def __init__(self, endpoint, frequency=5, thread_count=5):
        """Initialize a new Monitor Manager.

        Args:
            endpoint(`Endpoint`): An `Endpoint` object capable of calling
                the `request()` method.
            thread_count(int): The number of requester threads to spawn
            frequency(int): The frequency to make a new request

        """
        # don't use get() here because we want exception if missing key
        self.sfx_token = os.environ['SIGNALFX_TOKEN'] # bail if missing

        self.frequency = frequency
        self.thread_count = thread_count
        self.endpoint = endpoint
        self.queue_requests = queue.Queue()
        self.queue_results = queue.Queue()
        self.logger = logging.getLogger(__name__)
        self.hostname = socket.gethostname()
        self.sfx_client = signalfx.SignalFx()
        self.sfx_ingest = self.sfx_client.ingest(self.sfx_token)
        self.dimensions = None
#        self.sfx_ingest.add_dimensions(
#            {AWS_ID_DIMENSION: get_aws_unique_id()})
        self.should_die = False
        self.request_thread = threading.Thread(target=self.add_request, args=())
        self.request_thread.daemon = True
        self.request_thread.start()
        for i in range(thread_count):
            t = threading.Thread(target=self.request, args=())
            t.start()

    @property
    def static_dimensions(self):
        """Property to return a dictionary of static dimensions."""
        dims = {}
        dims['host'] = self.hostname
        if get_aws_unique_id():
            dims['AWS_ID_DIMENSION'] = get_aws_unique_id()
        self.dimensions = dims
        return self.dimensions

    def report(self, guages=[]):
        """Report result of call to SignalFX.

        Report endpoint request results to signalfx.  The signalfx library has
        its own queue/thread manager.

        """
        try:
            if not self.dimensions:
                self.sfx_ingest.add_dimensions(self.static_dimensions)
            self.logger.debug(f'Guages: {guages}')
            self.sfx_ingest.send(gauges=guages)
        finally:
            self.sfx_ingest.stop()

    def request(self):
        """Execute a request to the `Endpoint`.

        Grab an item off the queue and make a request.

        """
        while True:
            if self.should_die:
                self.logger.debug("I should die")
                break
            try:
                endpoint = self.queue_requests.get(timeout=1)
                self.report(endpoint.request())
                self.logger.debug("Got an endpoint")
                self.queue_requests.task_done()
            except queue.Empty:
                self.logger.debug("Nothing in the queue...waiting.")
                continue

    def add_request(self):
        """Add the endpoint to the request queue.

        Add a new endpoint request to the `queue_requests` queue every
        `frequency` seconds.

        """
        while True:
            if self.should_die:
                break
            time.sleep(self.frequency)
            self.queue_requests.put(self.endpoint)
            self.logger.debug("Add endpoint to the queue")
