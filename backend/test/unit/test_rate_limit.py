from rate_limit import SlidingWindowLimiter


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def limiter(limit=3, window=60):
    clock = FakeClock()
    return SlidingWindowLimiter(limit, window, clock=clock), clock


def test_allows_events_up_to_the_limit():
    # Arrange
    subject, _ = limiter(limit=3)

    # Act
    results = [subject.hit('user-1') for _ in range(3)]

    # Assert: 0 means allowed.
    assert results == [0, 0, 0]


def test_blocks_the_next_event_and_says_how_long_to_wait():
    # Arrange: three events at t=1000, 1010 and 1020 fill a 60-second window.
    subject, clock = limiter(limit=3, window=60)
    for offset in (0, 10, 20):
        clock.now = 1000 + offset
        subject.hit('user-1')
    clock.now = 1030

    # Act
    retry_after = subject.hit('user-1')

    # Assert: the oldest event (t=1000) leaves the window at t=1060, 30 seconds from now.
    assert retry_after == 30


def test_a_blocked_attempt_does_not_use_up_a_slot():
    # Arrange
    subject, clock = limiter(limit=1, window=60)
    subject.hit('user-1')
    clock.now += 30
    subject.hit('user-1')

    # Act: once the first event leaves the window, one slot is free again.
    clock.now += 31
    result = subject.hit('user-1')

    # Assert
    assert result == 0


def test_the_window_slides():
    # Arrange
    subject, clock = limiter(limit=2, window=60)
    subject.hit('user-1')
    subject.hit('user-1')

    # Act
    clock.now += 60
    result = subject.hit('user-1')

    # Assert
    assert result == 0


def test_each_key_has_its_own_budget():
    # Arrange
    subject, _ = limiter(limit=1)
    subject.hit('user-1')

    # Act
    other_user = subject.hit('user-2')

    # Assert
    assert other_user == 0
