# Implementation Guide: CPSC 3600 RDP Assignment

This guide tells you **in what order to implement things** and when to stop
and test. Follow it linearly — each step either unlocks the next one or
produces a test you can check immediately.

---

## Before You Write Any Code

Read these in order. You will reference them constantly while coding.

1. **`docs/protocol/wire-format.md`** — the byte-level layout of every packet
   type. You cannot implement `framing.py` without this.
2. **`docs/protocol/fsm.md`** — state machine and sequence diagrams showing
   which packets travel between hosts and when.
3. **`docs/protocol/implementation.md`** — flowcharts showing what your code
   does internally: how the send queue drains, how ACKs are processed, how
   out-of-order data is buffered.
4. **`template/rdp/framing.py`** — read every docstring. They specify exactly
   what each function must do.
5. **`template/rdp/connection.py`** — read every docstring, especially the
   `_handle` docstring which enumerates every state/packet combination.

Do not skim. The docstrings are the specification.

---

## Bundle 1 — Framing

All functions in `src/rdp/framing.py` are pure (no state, no class). You can
run a single test at a time: `pytest tests/bundle1/test_framing.py::test_name -v`.

### Step 1 — `compute_checksum`

This is the hardest function in Bundle 1. Get it right before touching
anything else, because every packet builder depends on it.

Work through this order:

1. Handle even-length input: split into 16-bit big-endian words and sum them.
2. Add carry folding: after each addition, if the result exceeds 16 bits, add
   the overflow back into the low 16 bits.
3. Handle odd-length input: pad with a zero byte on the right before
   processing (do not modify the original bytes).
4. Return the bitwise NOT of the final sum, masked to 16 bits (`~total & 0xFFFF`).

**Test checkpoint:** `pytest tests/bundle1/ -k "checksum" -v` — four tests,
all should pass before moving on.

### Step 2 — `_pack`

This is the internal builder used by every `build_*` function. Get it working
before implementing any of the public builders.

Steps:
1. Raise `ValueError` if `len(sack_blocks) > 3`.
2. Pack the fixed header using `struct.pack(HEADER_FMT, ...)` with the
   checksum field set to zero.
3. Append each SACK block packed with `struct.pack(SACK_FMT, start, end)`.
4. Append the payload length packed with `PAYLOAD_LEN_FMT`, then the raw payload.
5. Compute the checksum over the complete byte string (checksum bytes are
   still zero at this point).
6. Splice the checksum into positions `CHECKSUM_OFFSET` through
   `CHECKSUM_OFFSET + CHECKSUM_SIZE` and return the result.

`_pack` has no direct tests, but every builder test exercises it.

### Step 3 — `build_syn`, `build_syn_ack`, `build_ack`, `build_data`, `build_fin`, `build_fin_ack`

Each of these is a one-liner that calls `_pack` with the right arguments.
Check `wire-format.md` for which fields each packet type uses; unused fields
are zero and unused lists are empty.

**Test checkpoint:** `pytest tests/bundle1/ -k "round_trip or checksum_valid or sack or raises" -v`
— thirteen tests. All should pass before moving on.

### Step 4 — `is_corrupt`

1. Return `True` immediately if the packet is shorter than `CHECKSUM_SIZE`
   bytes (it cannot even contain a checksum).
2. Extract the embedded checksum from bytes `CHECKSUM_OFFSET` through
   `CHECKSUM_OFFSET + CHECKSUM_SIZE`.
3. Build a zeroed copy of the packet with those bytes replaced by `\x00\x00`.
4. Recompute the checksum over the zeroed copy and compare. Return `True` if
   they differ.

**Test checkpoint:** `pytest tests/bundle1/ -k "corrupt" -v` — two tests.

### Step 5 — `parse`

`parse` is the inverse of `_pack`. Work through the layout in the same order
`_pack` assembled it:

1. Check `len(packet) >= HEADER_SIZE`; raise `MalformedPacket` if not.
2. Unpack the fixed header with `struct.unpack(HEADER_FMT, packet[:HEADER_SIZE])`.
3. Validate `sack_count <= 3`; raise `MalformedPacket` if not.
4. Read `sack_count` SACK blocks, each `SACK_SIZE` bytes. Raise
   `MalformedPacket` if the packet is too short.
5. Read the 2-byte payload length field. Raise `MalformedPacket` if the packet
   is too short to contain it.
6. Slice `payload_len` bytes of payload. Raise `MalformedPacket` if fewer
   bytes are available.
7. Return a populated `ParsedPacket`.

**Test checkpoint:** `pytest tests/bundle1/ -v` — all 19 tests should now pass.

---

## Bundle 2 — Handshake and Data Transfer

Bundle 2 adds a class with state. The key discipline is: **implement the
minimum needed to pass one scenario, run it, then extend.** Do not try to
implement all of `_handle` at once.

### Step 1 — Plumbing (`recv_from_network`, `on_timer_expire`, `close`)

These three are short and just delegate to other methods:

- `recv_from_network`: call `is_corrupt` → return if corrupt; call `parse` →
  return on `MalformedPacket`; call `_handle`.
- `on_timer_expire`: call `_retransmit_oldest`.
- `close`: call `_send_fin`.

Implement all three now. They will do nothing useful until the methods they
call are implemented, but they need to exist.

### Step 2 — Initiator handshake path

The handshake goes: A sends SYN → B sends SYN-ACK → A sends ACK.

Implement in this order:

1. **`_send_syn`**: build a SYN packet, send it, transition to `SYN_SENT`,
   start the timer.
2. **`recv_from_app` (LISTEN + empty payload case)**: if state is `LISTEN` and
   payload is `b""`, call `_send_syn` and return.
3. **`_handle` — `SYN_SENT + SYN_ACK` branch**: validate `ack_num == isn + 1`;
   record `_peer_isn`; set `_next_seq` and `_window_base` to `isn + 1`; send
   ACK; transition to `ESTABLISHED`; stop timer.
4. **`_retransmit_oldest` — `SYN_SENT` branch**: increment
   `_retransmit_count['SYN']`; if over `MAX_HANDSHAKE_RETRIES`, give up;
   otherwise resend SYN and restart the timer.

**Test checkpoint:** nothing passes yet — the responder path is not done.

### Step 3 — Responder handshake path

1. **`_handle` — `LISTEN + SYN` branch**: record `_peer_isn`; send SYN-ACK
   with your own ISN and `ack_num = peer_isn + 1`; transition to
   `SYN_RECEIVED`; start timer.
2. **`_handle` — `SYN_RECEIVED + ACK` branch**: validate `ack_num == isn + 1`;
   set `_next_seq` and `_window_base` to `isn + 1`; transition to
   `ESTABLISHED`; stop timer.
3. **`_retransmit_oldest` — `SYN_RECEIVED` branch**: same pattern as SYN_SENT
   but resends SYN-ACK.

**Test checkpoint:** `pytest tests/bundle2/handshake_basic.json -v` — should
pass.

### Step 4 — Send path

1. **`_can_send_more`**: return `(_next_seq - _window_base) < window_size`.
2. **`_try_send_from_queue`**: loop while the send queue is non-empty AND
   `_can_send_more()`: pop a segment, create an `_UnackedSegment`, append to
   `_unacked`, send the DATA packet, advance `_next_seq`. Start the timer when
   the first segment is enqueued (i.e., `_unacked` was empty before this
   segment).
3. **`recv_from_app` (data case)**: append payload to `_app_send_queue` and
   call `_try_send_from_queue`.

### Step 5 — Receive path (in-order only)

1. **`_handle` — `ESTABLISHED + DATA` in-order branch** (`seq == _peer_ack_num`):
   append payload to `_app_recv_buffer`; advance `_peer_ack_num`; call
   `_drain_out_of_order` (implement it as a no-op stub for now — you will fill
   it in during Bundle 3); send ACK.
2. **`_handle` — `ESTABLISHED + ACK` branch**: if `ack_num > _window_base`,
   advance `_window_base` and `_bytes_acked`, remove retired segments from
   `_unacked`. Stop the timer if `_unacked` is empty, otherwise restart it.
   Call `_try_send_from_queue`.

**Test checkpoint:** `pytest tests/bundle2/ -v` — all five Bundle 2 scenarios
should now pass. If `window_full` fails, check that `_can_send_more` correctly
stalls the sender when in-flight bytes reach `window_size` and that the ACK
handler properly restarts the send queue after the window reopens.

### Step 6 — Teardown

1. **`_send_fin`**: build and send a FIN packet; transition to `FIN_WAIT`;
   start the timer.
2. **`_handle` — FIN received**: send FIN-ACK with `ack_num = fin_seq + 1`. If
   current state is `FIN_WAIT`, transition to `CLOSED` and stop the timer.
   Otherwise transition to `CLOSING`.
3. **`_handle` — FIN-ACK received**: if current state is `FIN_WAIT` or
   `CLOSING`, transition to `CLOSED` and stop the timer.

**Test checkpoint:** `pytest tests/bundle2/ -v` — all five still pass. The
teardown was already included in `teardown_unilateral`.

---

## Bundle 3 — Reliability

Bundle 3 extends `connection.py`. At this point Bundle 2 must be fully
passing. Work through the categories below in order — each one enables the
next.

### Step 1 — ESTABLISHED retransmit

Add the `ESTABLISHED` branch to `_retransmit_oldest`: if `_unacked` is empty,
do nothing; otherwise take `_unacked[0]` (the oldest unacked segment),
increment `_retransmit_count[seg.seq]`, resend the DATA packet, and restart
the timer.

**Test checkpoint:** `pytest tests/bundle3/retransmit/simple_data_loss.json tests/bundle3/ack_loss/single_ack_loss.json -v`

### Step 2 — Out-of-order receive and SACK

Implement these three together — they form a unit:

1. **`_drain_out_of_order`**: loop while `_peer_ack_num` is a key in
   `_out_of_order`; pop that entry, append to `_app_recv_buffer`, advance
   `_peer_ack_num`. After the loop, call `_rebuild_sack_blocks`.
2. **`_rebuild_sack_blocks`**: if `_out_of_order` is empty, set `_sack_blocks = []`
   and return. Otherwise sort the keys, walk them and merge contiguous ranges
   (a key that equals the current block's `end` extends it; otherwise start a
   new block), and store at most 3 results in `_sack_blocks`.
3. **`_handle` — `ESTABLISHED + DATA` out-of-order and duplicate branches**:
   out-of-order stores in `_out_of_order` and calls `_rebuild_sack_blocks`;
   duplicate just re-sends the current ACK. All three DATA branches send an ACK
   using the current `_peer_ack_num` and `_sack_blocks`.

Now remove the stub from `_drain_out_of_order` in the in-order branch and call
the real implementation.

**Test checkpoint:** `pytest tests/bundle3/sack/ -v` — all three SACK scenarios
should pass.

### Step 3 — SACK-aware ACK processing

Add SACK pruning to the `ESTABLISHED + ACK` branch in `_handle`. After
advancing `_window_base` (or even if it did not advance), remove any segment
from `_unacked` whose entire byte range falls within a SACK block reported by
the incoming ACK. This must run on every ACK, not only when the cumulative
ack number moves.

**Test checkpoint:** `pytest tests/bundle3/ack_loss/ -v` and
`pytest tests/bundle3/retransmit/ -v`

### Step 4 — Handshake loss and FIN retransmit

Add the `FIN_WAIT` branch to `_retransmit_oldest`: resend the FIN and restart
the timer. (The `SYN_SENT` and `SYN_RECEIVED` branches from Bundle 2 already
handle handshake loss — verify they pass the new scenarios.)

**Test checkpoint:** `pytest tests/bundle3/handshake_loss/ tests/bundle3/teardown_edge/ -v`

### Step 5 — Corruption

No new code is required here. Corruption scenarios test that `recv_from_network`
silently discards corrupt packets (already implemented in step 1 of Bundle 2)
and that the timer then retransmits the lost packet. If these scenarios fail,
the issue is most likely in the retransmit or ACK processing path, not in
corruption detection itself.

**Test checkpoint:** `pytest tests/bundle3/corruption/ -v`

### Final checkpoint — all bundles

```bash
pytest tests/bundle1/ tests/bundle2/ tests/bundle3/ -v
```

All 40 assignment tests should pass.

---

## Habits That Help

**Test after each function, not after each file.** The test suite is designed
so individual functions produce passing tests. Running the full suite against a
half-finished implementation produces a wall of red that is hard to interpret.

**Read the failure output.** When a scenario test fails the harness prints the
failing assertion, the actual state of the connection at that point, and a
hint. The hint names the code path that diverged. Read it before opening your
editor.

**Print the state machine when stuck.** Add `print(f"[{self.role}] {self._state} recv {parsed.type}")` at the top of `_handle`. Re-run the failing scenario. If the
state sequence differs from the diagram in `docs/protocol/fsm.md`, you have
found where your implementation diverges.

**Keep Bundle 2 green while working on Bundle 3.** Run
`pytest tests/bundle2/ -v` periodically. Bundle 3 work occasionally breaks
Bundle 2 (usually the ACK handler or the send queue logic). Catch it early.
