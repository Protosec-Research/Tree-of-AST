import logging

class ToaLogger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(logging.StreamHandler())

    def log(self, message):
        self.logger.debug(message)