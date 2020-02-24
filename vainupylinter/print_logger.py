"""Redirect prints from pylint to logger

Compatible with python 2.7
"""
from contextlib import contextmanager
import logging
import sys

class PrintLogger:
    """Helper class"""
    def __init__(self, name="pylint", log_level="INFO"):
        """Init logger class"""
        self.logger = logging.getLogger(name)
        self.name = self.logger.name
        self.level = getattr(logging, log_level)

    def write(self, msg):
        """For redirecting prints that write to sys.stdout"""
        if msg and not msg.isspace():
            self.logger.log(self.level, msg)

    def flush(self):
        """Need when this is used"""
        pass


@contextmanager
def redirect_stdout(target):
    """Python 2.7 does not have contextlib.redirect_stdout method"""
    original = sys.stdout
    sys.stdout = target
    yield
    sys.stdout = original
