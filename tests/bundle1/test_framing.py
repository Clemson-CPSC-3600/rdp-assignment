import pytest
from src.rdp.framing import (
    compute_checksum, is_corrupt,
    build_syn, build_syn_ack, build_ack, parse, ParsedPacket, PacketType,
    build_data, build_fin, build_fin_ack, MalformedPacket
)


@pytest.mark.bundle(1)
@pytest.mark.points(2)
def test_checksum_empty_bytes():
    assert compute_checksum(b"") == 0xFFFF


@pytest.mark.bundle(1)
@pytest.mark.points(2)
def test_checksum_single_zero_word():
    # 0x0000 sums to 0, one's complement is 0xFFFF
    assert compute_checksum(b"\x00\x00") == 0xFFFF


@pytest.mark.bundle(1)
@pytest.mark.points(2)
def test_checksum_known_vector():
    # Hand-verified: bytes 0x01, 0x02, 0x03, 0x04
    # Words: 0x0102, 0x0304. Sum: 0x0406. Complement: 0xFBF9.
    assert compute_checksum(b"\x01\x02\x03\x04") == 0xFBF9


@pytest.mark.bundle(1)
@pytest.mark.points(2)
def test_checksum_odd_length_pads_with_zero():
    # Bytes 0x01, 0x02, 0x03 → words 0x0102, 0x0300 (pad).
    # Sum: 0x0402. Complement: 0xFBFD.
    assert compute_checksum(b"\x01\x02\x03") == 0xFBFD


@pytest.mark.bundle(1)
@pytest.mark.points(2)
def test_is_corrupt_clean_packet_returns_false():
    # A packet whose embedded checksum matches a recomputation is clean.
    payload = bytearray(b"\x01\x00\x00\x04")  # byte0=flag, [1,2]=checksum, byte3=data
    checksum_bytes = bytearray(payload); checksum_bytes[1:3] = b"\x00\x00"
    cs = compute_checksum(bytes(checksum_bytes))
    payload[1] = (cs >> 8) & 0xFF
    payload[2] = cs & 0xFF
    assert is_corrupt(bytes(payload)) is False


@pytest.mark.bundle(1)
@pytest.mark.points(2)
def test_is_corrupt_flipped_bit_returns_true():
    payload = bytearray(b"\x01\x00\x00\x04")
    checksum_bytes = bytearray(payload); checksum_bytes[1:3] = b"\x00\x00"
    cs = compute_checksum(bytes(checksum_bytes))
    payload[1] = (cs >> 8) & 0xFF
    payload[2] = cs & 0xFF
    # Flip one bit in data.
    payload[3] ^= 0b0000_0001
    assert is_corrupt(bytes(payload)) is True


@pytest.mark.bundle(1)
@pytest.mark.points(3)
def test_syn_round_trip():
    packet = build_syn(isn=1000, window_size=4096)
    parsed = parse(packet)
    assert parsed.type == PacketType.SYN
    assert parsed.seq_num == 1000
    assert parsed.window_size == 4096
    assert parsed.sack_blocks == []
    assert parsed.payload == b""


@pytest.mark.bundle(1)
@pytest.mark.points(3)
def test_syn_ack_round_trip():
    packet = build_syn_ack(isn=5000, ack_num=1001, window_size=4096)
    parsed = parse(packet)
    assert parsed.type == PacketType.SYN_ACK
    assert parsed.seq_num == 5000
    assert parsed.ack_num == 1001


@pytest.mark.bundle(1)
@pytest.mark.points(3)
def test_ack_round_trip_no_sack():
    packet = build_ack(ack_num=2000, sack_blocks=[])
    parsed = parse(packet)
    assert parsed.type == PacketType.ACK
    assert parsed.ack_num == 2000
    assert parsed.sack_blocks == []


@pytest.mark.bundle(1)
@pytest.mark.points(3)
def test_syn_packet_checksum_valid():
    packet = build_syn(isn=1000, window_size=4096)
    assert is_corrupt(packet) is False


@pytest.mark.bundle(1)
@pytest.mark.points(3)
def test_data_round_trip():
    packet = build_data(seq=1000, payload=b"hello world")
    parsed = parse(packet)
    assert parsed.type == PacketType.DATA
    assert parsed.seq_num == 1000
    assert parsed.payload == b"hello world"


@pytest.mark.bundle(1)
@pytest.mark.points(3)
def test_fin_round_trip():
    packet = build_fin(seq=5000)
    parsed = parse(packet)
    assert parsed.type == PacketType.FIN
    assert parsed.seq_num == 5000


@pytest.mark.bundle(1)
@pytest.mark.points(3)
def test_fin_ack_round_trip():
    packet = build_fin_ack(ack_num=5001)
    parsed = parse(packet)
    assert parsed.type == PacketType.FIN_ACK
    assert parsed.ack_num == 5001


@pytest.mark.bundle(1)
@pytest.mark.points(3)
def test_data_empty_payload_round_trip():
    packet = build_data(seq=1000, payload=b"")
    parsed = parse(packet)
    assert parsed.payload == b""


@pytest.mark.bundle(1)
@pytest.mark.points(2)
def test_ack_one_sack_block():
    packet = build_ack(ack_num=1000, sack_blocks=[(1100, 1200)])
    parsed = parse(packet)
    assert parsed.sack_blocks == [(1100, 1200)]


@pytest.mark.bundle(1)
@pytest.mark.points(2)
def test_ack_three_sack_blocks():
    blocks = [(1100, 1200), (1300, 1400), (1500, 1600)]
    packet = build_ack(ack_num=1000, sack_blocks=blocks)
    parsed = parse(packet)
    assert parsed.sack_blocks == blocks


@pytest.mark.bundle(1)
@pytest.mark.points(2)
def test_sack_over_three_blocks_raises():
    with pytest.raises(ValueError):
        build_ack(ack_num=1000, sack_blocks=[(1, 2), (3, 4), (5, 6), (7, 8)])


@pytest.mark.bundle(1)
@pytest.mark.points(2)
def test_parse_truncated_header_raises():
    with pytest.raises(MalformedPacket):
        parse(b"\x00\x00\x00")  # too short for 14-byte header


@pytest.mark.bundle(1)
@pytest.mark.points(2)
def test_parse_truncated_payload_raises():
    packet = build_data(seq=1000, payload=b"hello")
    truncated = packet[:-2]  # remove last 2 bytes of payload
    with pytest.raises(MalformedPacket):
        parse(truncated)
