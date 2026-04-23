from tests._harness.simulator import Simulator, SimulatorHandle


class FakeHost:
    """Minimal fake host for simulator unit tests."""
    def __init__(self, name):
        self.name = name
        self.received_packets = []
        self.timer_fires = 0

    def recv_from_app(self, payload): pass
    def recv_from_network(self, packet): self.received_packets.append(packet)
    def on_timer_expire(self): self.timer_fires += 1
    def close(self): pass

    window_base = next_seq = bytes_acked = bytes_delivered = 0
    sack_blocks = []
    state = "LISTEN"
    retransmit_count = {}
    app_recv_buffer = []


def test_simulator_routes_packet_from_a_to_b():
    sim = Simulator()
    a = FakeHost("A")
    b = FakeHost("B")
    sim.attach(a, b)
    sim.handle_for("A").send_packet(b"hello")
    sim.run_pending()
    assert b.received_packets == [b"hello"]


def test_simulator_tick_fires_expired_timer():
    sim = Simulator()
    a = FakeHost("A")
    b = FakeHost("B")
    sim.attach(a, b)
    sim.handle_for("A").start_timer(1.0)
    sim.tick(2.0)
    assert a.timer_fires == 1
