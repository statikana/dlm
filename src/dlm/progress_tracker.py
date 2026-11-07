"""Helpers for tracking progress across a chunked download."""

UP = "\033[F"
CLEAR_LINE = "\33[2K\r"


class ProgressTracker:
    """Track how much of a byte range has been downloaded."""

    def __init__(self, start: int, end: int):
        self.start = start
        self.current = start
        self.end = end

    def update(self, value: int):
        """Set the current position for this download range."""
        self.current = max(self.start, min(value, self.end))

    @property
    def p(self) -> float:
        if self.end == self.start:
            return 1.0
        return max(0.0, min(1.0, (self.current - self.start) / (self.end - self.start)))

    def __repr__(self) -> str:
        length = 20
        progress = self.p
        filled = round(length * progress)
        label = f"[{round(progress * 100, 2)}%] [{self.current - self.start}/{self.end - self.start}]"
        return "|" + ("=" * filled) + ((length - filled) * " ") + f"| {label}"

    @property
    def done(self) -> bool:
        return self.current >= self.end


class MultiTracker:
    """Track multiple progress ranges together."""

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
        for tracker in self.trackers[n:]:
            print(tracker)
