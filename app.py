"""Monitor GetTax SOAP Requests


"""
import logging
import signal
import time
from monitor.manager import Manager
from monitor.endpoint import GetTaxSoapEndpoint


class SignalCatcher(object):
    shutdown = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.terminate)
        signal.signal(signal.SIGTERM, self.terminate)

    def terminate(self, signum, frame):
        self.shutdown = True


if __name__ == "__main__":
    catcher = SignalCatcher()
    logging.basicConfig(format='%(levelname)s:%(message)s',
                        level=logging.DEBUG)
    logging.info("Started")
    ep = GetTaxSoapEndpoint()
    manager = Manager(ep)
    while True:
        time.sleep(10)
        logging.debug(f'catcher shutdown: {catcher.shutdown}')
        if catcher.shutdown:
            logging.info("Shutting down...")
            manager.should_die = True
            break
