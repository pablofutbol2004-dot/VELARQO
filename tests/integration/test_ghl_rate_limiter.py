from integrations.ghl.rate_limiter import RateLimiter


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def test_does_not_sleep_under_the_limit():
    clock = FakeClock()
    sleeps = []
    limiter = RateLimiter(max_requests=5, window_seconds=10, clock=clock, sleep=sleeps.append)

    for _ in range(5):
        limiter.acquire()
        clock.advance(0.1)

    assert sleeps == []


def test_sleeps_when_burst_limit_hit_within_window():
    clock = FakeClock()
    sleeps = []

    def fake_sleep(seconds):
        sleeps.append(seconds)
        clock.advance(seconds)

    limiter = RateLimiter(max_requests=3, window_seconds=10, clock=clock, sleep=fake_sleep)

    for _ in range(3):
        limiter.acquire()

    limiter.acquire()

    assert len(sleeps) == 1
    assert sleeps[0] == 10.0


def test_old_requests_expire_out_of_window():
    clock = FakeClock()
    sleeps = []
    limiter = RateLimiter(max_requests=2, window_seconds=10, clock=clock, sleep=sleeps.append)

    limiter.acquire()
    limiter.acquire()
    clock.advance(11)
    limiter.acquire()

    assert sleeps == []
