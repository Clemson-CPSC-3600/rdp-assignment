from dataclasses import dataclass, field
from .host_protocol import TCPConnectionProtocol


@dataclass
class _PendingPacket:
    from_host: str
    to_host: str
    data: bytes
    deliver_at: float


@dataclass
class _Timer:
    host: str
    fires_at: float


class SimulatorHandle:
    """What a host sees of the simulator."""

    def __init__(self, sim: "Simulator", host_name: str):
        self._sim = sim
        self._host = host_name

    def send_packet(self, packet: bytes) -> None:
        self._sim._enqueue_packet(self._host, packet)

    def start_timer(self, interval: float) -> None:
        self._sim._start_timer(self._host, interval)

    def stop_timer(self) -> None:
        self._sim._stop_timer(self._host)


class Simulator:
    """Event-driven harness. Runs scripted events and routes packets."""

    def __init__(self):
        self.clock: float = 0.0
        self._hosts: dict[str, TCPConnectionProtocol] = {}
        self._pending: list[_PendingPacket] = []
        self._timers: dict[str, _Timer] = {}
        self._traps: list[dict] = []
        self._packet_log: list[dict] = []

    def attach(self, host_a, host_b) -> None:
        self._hosts["A"] = host_a
        self._hosts["B"] = host_b

    def handle_for(self, host_name: str) -> SimulatorHandle:
        return SimulatorHandle(self, host_name)

    def _enqueue_packet(self, from_host: str, packet: bytes) -> None:
        to_host = "B" if from_host == "A" else "A"
        for i, trap in enumerate(self._traps):
            if self._trap_matches(trap, from_host, packet):
                self._traps.pop(i)
                self._packet_log.append({
                    "from": from_host, "to": to_host,
                    "action": trap["type"], "t": self.clock,
                })
                if trap["type"] == "drop_next":
                    return
                elif trap["type"] == "corrupt_next":
                    packet = self._corrupt(packet)
                break
        self._pending.append(_PendingPacket(
            from_host=from_host, to_host=to_host,
            data=packet, deliver_at=self.clock,
        ))

    def _trap_matches(self, trap: dict, from_host: str, packet: bytes) -> bool:
        match = trap.get("match", {})
        if match.get("host") and match["host"] != from_host:
            return False
        from src.rdp.framing import parse, MalformedPacket
        try:
            parsed = parse(packet)
        except MalformedPacket:
            return False
        if match.get("pkt_type"):
            if parsed.type.name != match["pkt_type"]:
                return False
        if match.get("seq") is not None:
            if parsed.seq_num != match["seq"]:
                return False
        return True

    def _corrupt(self, packet: bytes) -> bytes:
        mutable = bytearray(packet)
        mutable[-1] ^= 0b0000_0001
        return bytes(mutable)

    def arm_trap(self, trap: dict) -> None:
        self._traps.append(trap)

    def _start_timer(self, host: str, interval: float) -> None:
        self._timers[host] = _Timer(host=host, fires_at=self.clock + interval)

    def _stop_timer(self, host: str) -> None:
        self._timers.pop(host, None)

    def run_pending(self) -> None:
        """Deliver all pending packets and fire any timer expiries at current clock."""
        while self._pending or self._any_timer_expired():
            if self._pending:
                pkt = self._pending.pop(0)
                self._hosts[pkt.to_host].recv_from_network(pkt.data)
            for name, timer in list(self._timers.items()):
                if timer.fires_at <= self.clock:
                    del self._timers[name]
                    self._hosts[name].on_timer_expire()

    def _any_timer_expired(self) -> bool:
        return any(t.fires_at <= self.clock for t in self._timers.values())

    def tick(self, to_time: float) -> None:
        """Advance clock to `to_time`, firing timer expiries and delivering packets."""
        self.clock = to_time
        self.run_pending()
