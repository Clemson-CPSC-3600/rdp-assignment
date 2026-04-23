# RDP Wire Format Specification

This document defines the byte-level packet structure for the Reliable Datagram Protocol (RDP). All multi-byte values use network byte order (big-endian). No padding is inserted between fields.

## Packet Structure

Every RDP packet consists of:

1. **Fixed Header** (14 bytes)
2. **SACK Blocks** (0–3 blocks, 8 bytes each)
3. **Payload Length** (2 bytes)
4. **Payload** (0–1024 bytes)

### Fixed Header

The fixed header is always 14 bytes and contains control information and flow-control data.

| Offset | Size | Field        | Type     | Description                                                    |
|--------|------|--------------|----------|----------------------------------------------------------------|
| 0      | 1    | flags        | uint8    | Packet type flags (SYN, ACK, FIN, DATA). See [Flags Byte](#flags-byte). |
| 1      | 2    | checksum     | uint16   | Internet checksum over entire packet (RFC 1071). See [Checksum](#checksum). |
| 3      | 4    | seq_num      | uint32   | Sequence number for this packet's data or synchronization.     |
| 7      | 4    | ack_num      | uint32   | Acknowledgment number; highest seq_num received and accepted.  |
| 11     | 2    | window_size  | uint16   | Receiver's advertised window size (bytes). Used for flow control. |
| 13     | 1    | sack_count   | uint8    | Number of SACK blocks that follow (0–3).                       |

**Total fixed header size: 14 bytes**

### SACK Blocks

Following the fixed header, zero to three selective acknowledgment (SACK) blocks may appear. Each SACK block is 8 bytes and describes a contiguous range of sequence numbers the receiver has successfully received but has not yet acknowledged.

| Offset (relative to this block) | Size | Field | Type   | Description |
|---------------------------------|------|-------|--------|-------------|
| 0                               | 4    | start | uint32 | Start of acknowledged sequence range (inclusive). |
| 4                               | 4    | end   | uint32 | End of acknowledged sequence range (exclusive). |

Each SACK block occupies 8 bytes. If `sack_count` is *n*, then *n* SACK blocks occupy *8n* bytes immediately after the fixed header.

**Example:** If `sack_count` is 2, two SACK blocks occupy bytes 14–29 (2 × 8 = 16 bytes).

### Payload Length

After all SACK blocks, a 2-byte field specifies the length of the payload data that follows.

| Offset | Size | Field        | Type   | Description |
|--------|------|--------------|--------|-------------|
| 14 + (sack_count × 8) | 2 | payload_len | uint16 | Length of the payload in bytes (0–1024). |

### Payload

The payload data follows immediately after the payload length field and has a length of `payload_len` bytes.

| Offset | Size | Description |
|--------|------|-------------|
| 16 + (sack_count × 8) | payload_len | Actual payload bytes. |

## Flags Byte

The flags field is a bitmask where each bit represents a packet control flag.

| Bit | Hex Value | Name | Meaning |
|-----|-----------|------|---------|
| 0   | 0x01      | SYN  | Synchronization / connection initiation |
| 1   | 0x02      | ACK  | Acknowledgment of received data |
| 2   | 0x04      | FIN  | Finish / connection termination |
| 3   | 0x08      | DATA | Data payload present |

### Packet Types

Packets are identified by combinations of flags. The following are the standard packet types:

| Packet Type | Flags (binary) | Flags (hex) | Description |
|-------------|----------------|-------------|-------------|
| SYN         | 0b0001         | 0x01        | Connection initiation; opens a new connection. |
| SYN+ACK     | 0b0011         | 0x03        | Connection acknowledgment; replies to SYN. |
| ACK         | 0b0010         | 0x02        | Pure acknowledgment; no data payload. |
| DATA        | 0b1010         | 0x0A        | Data with piggyback ACK. Every DATA packet carries an implicit ACK. |
| FIN         | 0b0100         | 0x04        | Finish packet; initiates graceful close. |
| FIN+ACK     | 0b0110         | 0x06        | Finish acknowledgment; replies to FIN. |

**Note:** The DATA flag (bit 3, value 0x08) is always accompanied by the ACK flag (bit 1, value 0x02) in payload-carrying packets, forming the value 0x0A = 0b1010.

## Checksum

The checksum field protects the entire packet against transmission errors using the Internet checksum algorithm defined in RFC 1071.

### Computation Steps

1. **Set checksum field to zero** in a copy of the entire packet.
2. **Sum all 16-bit words** in network byte order (big-endian). Treat the packet as a sequence of big-endian 16-bit unsigned integers.
3. **Add carries back in** (one's-complement sum): if the sum exceeds 16 bits, add the carry bits back to the lower 16 bits.
4. **Take the one's complement** (bitwise NOT) of the result: `checksum = ~(sum & 0xFFFF)`.
5. **Write the checksum** back into the checksum field of the original packet.

### Verification

To verify a received packet:

1. **Save the received checksum** from the packet.
2. **Set the packet's checksum field to zero**.
3. **Compute the checksum** over the modified packet using steps 1–4 above.
4. **Compare** the computed value with the saved checksum. If they match, the packet is valid.

Alternatively, sum all 16-bit words (including the checksum field at its original value). If the result reduces to 0xFFFF, the packet is valid.

## Maximum Sizes

The protocol enforces the following limits:

| Component       | Maximum Size | Rationale |
|-----------------|--------------|-----------|
| SACK blocks     | 3 blocks     | Fixed header field `sack_count` is 1 byte; 3 blocks fit in typical MTU. |
| SACK block size | 8 bytes each | Two 32-bit unsigned integers per block. |
| Payload         | 1024 bytes   | Configurable per implementation; chosen for balance between throughput and latency. |
| Total packet    | 1078 bytes   | 14 (header) + 24 (3 SACK blocks) + 2 (payload length) + 1024 (max payload) = 1064 bytes |

## Example: SYN Packet

A SYN packet initiating a connection:

```
Bytes 0–13:   Fixed header
  Byte 0:       flags = 0x01 (SYN)
  Bytes 1–2:    checksum = [computed value]
  Bytes 3–6:    seq_num = 1000 (initial sequence)
  Bytes 7–10:   ack_num = 0 (no data received yet)
  Bytes 11–12:  window_size = 65535 (maximum)
  Byte 13:      sack_count = 0 (no SACK blocks)
Bytes 14–15:  payload_len = 0 (no payload)
[Payload]     (empty)
```

## Example: DATA Packet

A DATA packet carrying 100 bytes of payload with an ACK:

```
Bytes 0–13:   Fixed header
  Byte 0:       flags = 0x0A (DATA + ACK)
  Bytes 1–2:    checksum = [computed value]
  Bytes 3–6:    seq_num = 1001 (data sequence start)
  Bytes 7–10:   ack_num = 2000 (acknowledge up to sequence 2000)
  Bytes 11–12:  window_size = 65000
  Byte 13:      sack_count = 0 (no SACK blocks)
Bytes 14–15:  payload_len = 100
Bytes 16–115: [100 bytes of payload data]
```

## Example: DATA Packet with SACK

A DATA packet carrying 50 bytes with 2 SACK blocks:

```
Bytes 0–13:   Fixed header
  Byte 0:       flags = 0x0A (DATA + ACK)
  Bytes 1–2:    checksum = [computed value]
  Bytes 3–6:    seq_num = 3000
  Bytes 7–10:   ack_num = 5000
  Bytes 11–12:  window_size = 32768
  Byte 13:      sack_count = 2
Bytes 14–21:  SACK block 1
  Bytes 14–17:  start = 5100
  Bytes 18–21:  end = 5200
Bytes 22–29:  SACK block 2
  Bytes 22–25:  start = 5300
  Bytes 26–29:  end = 5400
Bytes 30–31:  payload_len = 50
Bytes 32–81:  [50 bytes of payload data]
```

## Byte Order Note

All examples show values in decimal for readability. In the actual packet bytes, all multi-byte fields are stored in network byte order (big-endian). For instance, the sequence number 1000 (0x000003E8) is stored as bytes `00 00 03 E8`.
