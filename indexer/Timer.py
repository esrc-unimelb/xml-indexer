import datetime
import logging

log = logging.getLogger('TIMER')

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
        log.info("Run time: %s seconds" % s)