import datetime
import logging

log = logging.getLogger()

class Timer:
    """
    Time a procedure.
    """
    def __enter__(self):
        self.start = datetime.datetime.now()
        return self

    def __exit__(self, *args):
        self.interval = datetime.datetime.now() - self.start
        s = self.interval.seconds
        self.hours, remainder = divmod(s, 3600)
        self.minutes, self.seconds = divmod(remainder, 60)
        log.info("Run time: {0} hours, {1} minutes and {2} seconds".format(self.hours, self.minutes, s))