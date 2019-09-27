import time

MIN_SAMPLE_PERIOD = 5
MAX_SAMPLE_POINTS = 10

class Statistic:
    def __init__(self):
        self.data = list()
        self.expires = time.time() + MIN_SAMPLE_PERIOD
        self.accumulator = 0

    def record(self, amount):
        self.accumulator += amount
        self.check()

    def check(self):
        now = time.time()
        if now >= self.expires:
            point = (self.accumulator, int(now))
            self.data.append(point)
            self.data = self.data[-MAX_SAMPLE_POINTS:]
            self.expires = now + MIN_SAMPLE_PERIOD
            self.accumulator = 0

    def __str__(self):
        self.check()
        points = ["%x,%x" % x for x in self.data]
        return " ".join(points)

class StatisticCollection:
    pass
