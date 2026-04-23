# Grading: CPSC 3600 RDP Assignment

## Overview

This assignment uses **specification grading**: each bundle is all-or-nothing.
You must pass every test in a bundle to earn credit for it. There is no partial
credit within a bundle.

| Bundle | Grade | Points | What it covers |
|--------|-------|--------|----------------|
| 1 | C | 46 | Checksum, packet building and parsing |
| 1 + 2 | B | 61 | + Handshake, data transfer, flow control |
| 1 + 2 + 3 | A | 114 | + Retransmission, SACK, loss recovery |

Bundles are cumulative. A B grade requires passing all of Bundle 1 **and** all
of Bundle 2.

---

## Bundle 1 — Framing (46 pts, C grade)

Implement the functions in `src/rdp/framing.py`. All are pure (no state).

### Functions to implement

| Function | Points | What it must do |
|----------|--------|-----------------|
| `compute_checksum` | 8 | RFC 1071 Internet checksum over arbitrary bytes |
| `is_corrupt` | 4 | Zero the checksum field, recompute, compare |
| `build_syn` | 3 | SYN packet with ISN and window size |
| `build_syn_ack` | 3 | SYN-ACK with responder ISN and ack_num |
| `build_ack` | 7 | Pure ACK with optional SACK blocks; raise ValueError if >3 blocks |
| `build_data` | 3 | DATA packet carrying a payload |
| `build_fin` | 3 | FIN with sequence number |
| `build_fin_ack` | 3 | FIN-ACK with ack_num |
| `parse` | 12 | Parse raw bytes into ParsedPacket; raise MalformedPacket on bad input |

The `_pack` helper that `build_*` functions share is not tested directly, but
all the builder tests depend on it.

### Running Bundle 1 tests

```bash
pytest tests/bundle1/ -v
```

### Common pitfalls

**Checksum carry folding:** After summing two 16-bit words the result can exceed
16 bits. You must fold the high bits back into the low 16 bits before the next
addition, not just once at the end.

**Odd-length padding:** If the byte string has an odd length, pad with a zero
byte on the right before treating it as 16-bit words. Don't modify the input —
create a temporary padded copy.

**Checksum field must be zero when computing:** `_pack` embeds the checksum into
the packet. When you call `compute_checksum` over the assembled bytes, the two
bytes at `CHECKSUM_OFFSET` must be `\x00\x00`. If they aren't, the checksum
will be wrong.

**`parse` minimum length check:** Check that `len(packet) >= HEADER_SIZE` before
unpacking. Raise `MalformedPacket`, not a bare `struct.error`.

**`sack_count` bounds check:** Raise `MalformedPacket` if `sack_count > 3` — the
format only supports up to three blocks.

---

## Bundle 2 — Handshake + Data Transfer (15 pts, B grade)

Implement the state machine in `src/rdp/connection.py`. You must also pass all
of Bundle 1.

### Scenarios

| Scenario | Points | What it exercises |
|----------|--------|-------------------|
| `handshake_basic` | 3 | Three-way SYN / SYN-ACK / ACK |
| `data_single_segment` | 3 | One DATA segment, ACK, teardown |
| `data_multi_segment` | 3 | Multiple in-order segments within window |
| `window_full` | 3 | Sender stalls when in-flight bytes reach window_size |
| `teardown_unilateral` | 3 | FIN / FIN-ACK teardown after data transfer |

### Methods to implement (minimum for Bundle 2)

- `recv_from_app` — handshake initiation (empty payload in LISTEN) and data queuing
- `recv_from_network` — corruption check, parse, dispatch to `_handle`
- `on_timer_expire` / `_retransmit_oldest` — at minimum SYN_SENT and SYN_RECEIVED cases
- `_handle` — LISTEN+SYN, SYN_SENT+SYN_ACK, SYN_RECEIVED+ACK, ESTABLISHED+DATA, ESTABLISHED+ACK, FIN handling
- `_try_send_from_queue` / `_can_send_more` — sliding-window drain
- `_send_syn` / `_send_fin`

### Common pitfalls

**Sequence number after handshake:** After the three-way handshake, both
`_next_seq` and `_window_base` on the initiator must be `isn + 1`, not `isn`.
The SYN itself consumes one sequence number.

**Window stall:** `_can_send_more` must compare bytes in-flight
(`_next_seq - _window_base`) against `window_size`, not the number of unacked
segments.

**FIN direction:** Only the side that calls `close()` sends the FIN.  The other
side replies with a FIN-ACK and transitions to CLOSING, not FIN_WAIT.

---

## Bundle 3 — Reliability (53 pts, A grade)

Extend Bundle 2 with retransmission, SACK, and loss/corruption handling. You
must also pass Bundles 1 and 2.

### Scenarios

| Category | Scenario | Points |
|----------|----------|--------|
| ACK loss | `single_ack_loss` | 3 |
| ACK loss | `consecutive_ack_loss` | 3 |
| ACK loss | `ack_loss_with_window` | 4 |
| Corruption | `data_corrupt` | 3 |
| Corruption | `ack_corrupt` | 3 |
| Corruption | `handshake_corrupt` | 3 |
| Handshake loss | `syn_lost` | 3 |
| Handshake loss | `syn_ack_lost` | 3 |
| Handshake loss | `final_ack_lost` | 3 |
| Retransmit | `simple_data_loss` | 3 |
| Retransmit | `loss_then_burst` | 3 |
| Retransmit | `double_loss` | 4 |
| SACK | `out_of_order_recovery` | 4 |
| SACK | `multiple_gaps` | 4 |
| SACK | `sack_incremental_fill` | 4 |
| Teardown | `simultaneous_close` | 3 |

### Methods to implement (beyond Bundle 2)

- `_retransmit_oldest` — full: SYN_SENT, SYN_RECEIVED, ESTABLISHED, FIN_WAIT branches
- `_drain_out_of_order` — move contiguous out-of-order segments into the receive buffer
- `_rebuild_sack_blocks` — merge sorted out-of-order sequence numbers into ≤3 `(start, end)` blocks

### Common pitfalls

**SACK pruning on every ACK:** When processing an ACK in ESTABLISHED state,
prune `_unacked` using any SACK blocks present in the packet. This must happen
even if the cumulative `ack_num` did not advance — don't gate the SACK prune
inside the `if new_base > old_base` block.

**FIN retransmit:** `_retransmit_oldest` needs a FIN_WAIT branch. The timer
starts when you send the FIN; if the FIN-ACK never arrives the timer fires, and
if there is no FIN_WAIT case nothing gets retransmitted.

**`_drain_out_of_order` must call `_rebuild_sack_blocks`:** After draining,
the SACK blocks sent in subsequent ACKs must reflect the updated
`_out_of_order` contents. Call `_rebuild_sack_blocks` at the end of
`_drain_out_of_order`.

**Retransmit count:** Increment `_retransmit_count[seq]` each time you
retransmit a segment, and enforce `MAX_HANDSHAKE_RETRIES` for SYN and SYN-ACK
retransmits.

---

## Checking your progress

```bash
# Run tests for a specific bundle
pytest tests/bundle1/ -v
pytest tests/bundle2/ -v
pytest tests/bundle3/ -v

# Run everything
pytest -v

# Stop on first failure (useful when debugging)
pytest tests/bundle1/ -x
```

When a scenario test fails, the harness prints the failing assertion, the actual
state of the connection at that point, and a hint. Read it carefully — it tells
you which state machine branch diverged from what was expected.
