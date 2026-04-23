from dataclasses import dataclass, field
from enum import Enum

from .framing import (
    PacketType, ParsedPacket, MalformedPacket,
    build_syn, build_syn_ack, build_ack, build_data, build_fin, build_fin_ack,
    parse, is_corrupt,
)
from .timers import RetransmitTimer


class State(Enum):
    LISTEN = "LISTEN"
    SYN_SENT = "SYN_SENT"
    SYN_RECEIVED = "SYN_RECEIVED"
    ESTABLISHED = "ESTABLISHED"
    FIN_WAIT = "FIN_WAIT"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"


@dataclass
class _UnackedSegment:
    seq: int
    data: bytes


class TCPConnection:
    MAX_HANDSHAKE_RETRIES = 8

    def __init__(self, sim_handle, role: str, isn: int,
                 timer_interval: float, window_size: int):
        self.sim = sim_handle
        self.role = role
        self.isn = isn
        self.window_size = window_size
        self.timer = RetransmitTimer(sim_handle, timer_interval)

        self._state = State.LISTEN
        self._next_seq = isn
        self._window_base = isn
        self._bytes_acked = 0
        self._peer_ack_num = 0
        self._peer_isn: int | None = None

        self._unacked: list[_UnackedSegment] = []
        self._app_send_queue: list[bytes] = []
        self._out_of_order: dict[int, bytes] = {}
        self._sack_blocks: list[tuple[int, int]] = []

        self._app_recv_buffer: list[bytes] = []
        self._retransmit_count: dict[int, int] = {}

    # --- read-only properties for the harness ---

    @property
    def window_base(self) -> int: return self._window_base
    @property
    def next_seq(self) -> int: return self._next_seq
    @property
    def bytes_acked(self) -> int: return self._bytes_acked
    @property
    def bytes_delivered(self) -> int: return sum(len(p) for p in self._app_recv_buffer)
    @property
    def sack_blocks(self) -> list[tuple[int, int]]: return list(self._sack_blocks)
    @property
    def state(self) -> str: return self._state.value
    @property
    def retransmit_count(self) -> dict[int, int]: return dict(self._retransmit_count)
    @property
    def app_recv_buffer(self) -> list[bytes]: return list(self._app_recv_buffer)

    # --- public methods called by the harness ---

    def recv_from_app(self, payload: bytes) -> None:
        """Called by the harness to pass application data down to be sent.

        Special case: if the connection is in LISTEN state and *payload* is
        ``b""``, treat this as a signal to initiate the handshake (call
        ``_send_syn``).

        For all other calls, append *payload* to ``_app_send_queue`` and then
        call ``_try_send_from_queue`` to transmit as many segments as the
        window allows.
        """
        pass

    def recv_from_network(self, packet: bytes) -> None:
        """Called by the harness when a raw packet arrives from the network.

        Steps:
        1. Discard the packet silently if ``is_corrupt`` returns True.
        2. Try to ``parse`` the packet; discard silently on ``MalformedPacket``.
        3. Dispatch the parsed packet to ``_handle``.
        """
        pass

    def on_timer_expire(self) -> None:
        """Called by the harness when the retransmit timer fires.

        Delegate to ``_retransmit_oldest``.
        """
        pass

    def close(self) -> None:
        """Initiate an orderly shutdown by sending a FIN.

        Delegate to ``_send_fin``.
        """
        pass

    # --- internal methods (stub — implement these) ---

    def _send_syn(self) -> None:
        """Build and send a SYN packet, transition to SYN_SENT, start the timer."""
        pass

    def _handle(self, parsed: ParsedPacket) -> None:
        """State-machine dispatch: handle one parsed, non-corrupt packet.

        States and transitions to implement:

        LISTEN + SYN received:
            Record peer ISN, send SYN-ACK, transition to SYN_RECEIVED,
            start timer.

        SYN_SENT + SYN-ACK received:
            Validate ack_num == isn+1.  Record peer ISN, advance _next_seq and
            _window_base to isn+1, send ACK, transition to ESTABLISHED, stop
            timer.

        SYN_RECEIVED + ACK received:
            Validate ack_num == isn+1.  Advance _next_seq and _window_base,
            transition to ESTABLISHED, stop timer.

        ESTABLISHED + DATA received:
            In-order: append to _app_recv_buffer, advance _peer_ack_num, drain
            out-of-order buffer, send ACK.
            Out-of-order: store in _out_of_order, rebuild SACK blocks, send ACK.
            Duplicate: send ACK with current cumulative ack number.

        ESTABLISHED + ACK received:
            Advance _window_base and _bytes_acked for the newly acknowledged
            range.  Remove retired segments from _unacked.  Restart or stop
            timer.  Prune _unacked using SACK blocks from the ACK.  Call
            _try_send_from_queue.

        FIN received (any state that can receive it):
            Send FIN-ACK.  If FIN_WAIT, transition to CLOSED and stop timer.
            Otherwise transition to CLOSING.

        FIN-ACK received:
            If FIN_WAIT or CLOSING, transition to CLOSED and stop timer.
        """
        pass

    def _try_send_from_queue(self) -> None:
        """Drain _app_send_queue, sending segments while _can_send_more() is True.

        For each segment popped:
        - Create an _UnackedSegment and append to _unacked.
        - Build and send a DATA packet.
        - Advance _next_seq by len(payload).
        - Start the timer when the first unacked segment is enqueued.
        """
        pass

    def _can_send_more(self) -> bool:
        """Return True if the number of bytes in-flight is less than window_size.

        In-flight bytes = _next_seq - _window_base.
        """
        pass

    def _retransmit_oldest(self) -> None:
        """Retransmit based on current state.

        SYN_SENT: retransmit SYN (up to MAX_HANDSHAKE_RETRIES).
        SYN_RECEIVED: retransmit SYN-ACK (up to MAX_HANDSHAKE_RETRIES).
        FIN_WAIT: retransmit FIN.
        ESTABLISHED with unacked segments: retransmit the oldest unacked
            segment and increment its retransmit count.
        """
        pass

    def _send_fin(self) -> None:
        """Build and send a FIN packet, transition to FIN_WAIT, start the timer."""
        pass

    def _drain_out_of_order(self) -> None:
        """Move contiguous segments from _out_of_order into _app_recv_buffer.

        While there is an entry in _out_of_order whose key equals _peer_ack_num:
        - Pop it, append its payload to _app_recv_buffer.
        - Advance _peer_ack_num by len(payload).
        After the loop, call _rebuild_sack_blocks.
        """
        pass

    def _rebuild_sack_blocks(self) -> None:
        """Rebuild _sack_blocks from the current contents of _out_of_order.

        Sort the out-of-order sequence numbers and merge contiguous ranges into
        (start, end) tuples.  Store at most 3 blocks in _sack_blocks.
        Set _sack_blocks to [] if _out_of_order is empty.
        """
        pass
