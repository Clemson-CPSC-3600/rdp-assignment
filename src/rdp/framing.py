"""RDP wire-format framing helpers.

See docs/protocol/wire-format.md for the full packet layout specification.
Every function below has a docstring describing the expected behaviour.
Read that document and the docstrings before implementing.
"""

import struct
from dataclasses import dataclass, field
from enum import IntFlag


# ---------------------------------------------------------------------------
# Packet types
# ---------------------------------------------------------------------------

class PacketType(IntFlag):
    SYN = 0b0001
    ACK = 0b0010
    FIN = 0b0100
    DATA = 0b1000

    SYN_ACK = SYN | ACK
    DATA_ACK = DATA | ACK
    FIN_ACK = FIN | ACK


# ---------------------------------------------------------------------------
# Parsed packet dataclass
# ---------------------------------------------------------------------------

@dataclass
class ParsedPacket:
    type: PacketType
    seq_num: int
    ack_num: int
    window_size: int
    sack_blocks: list[tuple[int, int]] = field(default_factory=list)
    payload: bytes = b""


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class MalformedPacket(Exception):
    pass


# ---------------------------------------------------------------------------
# Wire-format constants
# ---------------------------------------------------------------------------

HEADER_FMT = "!BHIIHB"
HEADER_SIZE = struct.calcsize(HEADER_FMT)  # 14 bytes

SACK_FMT = "!II"
SACK_SIZE = struct.calcsize(SACK_FMT)      # 8 bytes per block

PAYLOAD_LEN_FMT = "!H"
PAYLOAD_LEN_SIZE = 2

CHECKSUM_OFFSET = 1   # byte index where the 16-bit checksum lives in the header
CHECKSUM_SIZE = 2


# ---------------------------------------------------------------------------
# Checksum
# ---------------------------------------------------------------------------

def compute_checksum(data: bytes) -> int:
    """Compute the RFC 1071 Internet checksum over *data*.

    Steps:
    1. If *data* has an odd length, pad it with a zero byte on the right.
    2. Sum all 16-bit big-endian words, folding carry bits back in after each
       addition so the running total stays 16-bit (one-complement addition).
    3. Return the bitwise NOT of the final sum, masked to 16 bits.

    Returns a 16-bit unsigned integer (0–65535).
    """
    pass


def is_corrupt(packet: bytes) -> bool:
    """Return True if the packet's embedded checksum is invalid.

    How to verify:
    1. If *packet* is too short to contain a checksum, return True immediately.
    2. Extract the embedded 16-bit checksum from bytes
       ``packet[CHECKSUM_OFFSET : CHECKSUM_OFFSET + CHECKSUM_SIZE]``.
    3. Build a zeroed copy of *packet* with those two bytes replaced by
       ``\\x00\\x00``.
    4. Run ``compute_checksum`` over the zeroed copy and compare with the
       embedded value.  Return True if they differ.
    """
    pass


# ---------------------------------------------------------------------------
# Internal packet builder
# ---------------------------------------------------------------------------

def _pack(ptype: PacketType, seq: int, ack: int, window: int,
          sack_blocks: list[tuple[int, int]], payload: bytes) -> bytes:
    """Assemble a complete wire-format packet and embed the checksum.

    Layout (see wire-format.md):
      [flags:1][checksum:2][seq:4][ack:4][window:2][sack_count:1]
      [sack_block_0:8]...[sack_block_N:8]   (0–3 blocks)
      [payload_len:2][payload:payload_len]

    Steps:
    1. Raise ``ValueError`` if ``len(sack_blocks) > 3``.
    2. Pack the fixed header using ``HEADER_FMT`` with checksum = 0.
    3. Append each SACK block packed with ``SACK_FMT``.
    4. Append the payload length (``PAYLOAD_LEN_FMT``) and then the payload.
    5. Compute the checksum over the whole byte string (checksum field is 0).
    6. Splice the checksum into bytes 1–2 and return the final bytes.
    """
    pass


# ---------------------------------------------------------------------------
# Public packet builders
# ---------------------------------------------------------------------------

def build_syn(isn: int, window_size: int) -> bytes:
    """Build a SYN packet.

    A SYN packet is used to initiate a connection.  It carries the sender's
    Initial Sequence Number (*isn*) and advertised *window_size*.  The ACK
    number and SACK blocks are unused (zero / empty) and the payload is empty.
    """
    pass


def build_syn_ack(isn: int, ack_num: int, window_size: int) -> bytes:
    """Build a SYN-ACK packet.

    Sent by the passive side in response to a SYN.  Carries the responder's
    own ISN, acknowledges the peer's SYN (``ack_num = peer_isn + 1``), and
    advertises the local *window_size*.  Payload is empty.
    """
    pass


def build_ack(ack_num: int, sack_blocks: list[tuple[int, int]]) -> bytes:
    """Build a pure ACK packet (no data).

    Used to acknowledge received data.  The sequence number field is zero.
    *sack_blocks* carries up to 3 ``(start, end)`` byte-range pairs for
    selective acknowledgement; pass an empty list if there are no out-of-order
    segments to report.  Window is zero.  Payload is empty.
    """
    pass


def build_data(seq: int, payload: bytes) -> bytes:
    """Build a DATA packet carrying *payload*.

    *seq* is the sequence number of the first byte in *payload*.  ACK, window,
    and SACK fields are all zero / empty (this is a pure data segment).
    """
    pass


def build_fin(seq: int) -> bytes:
    """Build a FIN packet to signal the end of the data stream.

    *seq* is the next sequence number (after all data sent so far).  ACK,
    window, SACK, and payload fields are all zero / empty.
    """
    pass


def build_fin_ack(ack_num: int) -> bytes:
    """Build a FIN-ACK packet in response to a received FIN.

    ``ack_num`` should be ``fin_seq + 1`` (acknowledging the FIN's sequence
    number).  Sequence number, window, SACK blocks, and payload are all zero /
    empty.
    """
    pass


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse(packet: bytes) -> ParsedPacket:
    """Parse a raw wire-format packet into a :class:`ParsedPacket`.

    Raises :class:`MalformedPacket` if:
    - *packet* is shorter than ``HEADER_SIZE``.
    - ``sack_count`` in the header exceeds 3.
    - The packet is truncated inside the SACK block region.
    - The packet is truncated before or inside the payload length field.
    - The actual payload is shorter than the declared ``payload_len``.

    Does **not** verify the checksum — call :func:`is_corrupt` first.

    Steps:
    1. Unpack the fixed header with ``HEADER_FMT``.
    2. Read ``sack_count`` SACK blocks (each ``SACK_SIZE`` bytes).
    3. Read the 2-byte payload length, then slice *payload_len* bytes.
    4. Return a populated :class:`ParsedPacket`.
    """
    pass
