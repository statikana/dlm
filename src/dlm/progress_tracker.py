import time

from test.test_reprlib import r


UP = "\033[F"
CLEAR_LINE = "\33[2K\r"


class ProgressTracker:
    def __init__(self, start: int, end: int):
        self.start = start
        self.current = start
        self.end = end

    def update(self, value: int):
        self.current = value

    @property
    def p(self) -> float:
        return (
            max(0, min(1, (self.current - self.start) / (self.end - self.start)))
            if self.end != self.start
            else 1
        )

    def __repr__(self) -> str:
        length = 20
        p = self.p
        l = round(length * self.p)
        return (
            f"|"
            + l * "="
            + (length - l) * " "
            + "|"
            + f" [{round(p*100, 2)}%] [{self.current-self.start}/{self.end-self.start}]"
        )

    @property
    def done(self) -> bool:
        return self.current >= self.end


class MultiTracker:
    def __init__(self, *trackers: ProgressTracker):
        self.trackers = list(trackers)
        self.n = len(self.trackers)

    @property
    def done(self) -> bool:
        return all(t.done for t in self.trackers)

    def __repr__(self) -> str:
        return "\n".join(map(str, self.trackers))

    def update_line(self, n: int, value: int):
        self.trackers[n].update(value)
        print(UP * (self.n - n), end="")
        print(CLEAR_LINE, end="")
        for t in self.trackers[n:]:
            print(t)
