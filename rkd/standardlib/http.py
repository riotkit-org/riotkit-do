from typing import List

from requests import get as http_get
from abc import ABC
from argparse import ArgumentParser
from ..api.contract import ExecutionContext, ConfigurableTaskInterface


class HttpWaitAbstractTask(ConfigurableTaskInterface, ABC):
    """
    Waits for a HTTP/HTTPS url to return one of expected HTTP codes
    """

    url: str
    timeout: int
    time_to_wait: int
    expects_codes: list

    def __init__(self):
        self.timeout = 1
        self.time_to_wait = 30
        self.expects_codes = [200]

    @staticmethod
    def get_configurable_attributes() -> List[str]:
        return ['url', 'timeout', 'time_to_wait', 'expects_codes']

    def execute(self, context: ExecutionContext) -> bool:
        time_to_wait = self.time_to_wait

        while time_to_wait > 0:
            time_to_wait = time_to_wait - 1

            try:
                response = http_get(self.url, timeout=self.timeout)

                if response.status_code in self.expects_codes:
                    return True

            except Exception as e:
                self.io().warn('Still not ready, {}, ETA {}s'.format(str(e), time_to_wait*self.timeout))

        return False

    def configure_argparse(self, parser: ArgumentParser):
        pass
