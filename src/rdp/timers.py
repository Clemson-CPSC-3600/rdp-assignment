from typing import Protocol


class TimerBackend(Protocol):
    def start_timer(self, interval: float) -> None: ...
    def stop_timer(self) -> None: ...


class RetransmitTimer:
    """Thin shim over the simulator's timer API."""

    def __init__(self, backend: TimerBackend, interval: float):
        self.backend = backend
        self.interval = interval
        self.running = False

    def start(self) -> None:
        self.backend.start_timer(self.interval)
        self.running = True

    def stop(self) -> None:
        if self.running:
            self.backend.stop_timer()
            self.running = False

    def restart(self) -> None:
        self.stop()
        self.start()
