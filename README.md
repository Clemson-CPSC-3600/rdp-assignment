# CPSC 3600: RDP Assignment

## Overview

In this assignment you build **RDP** — a TCP-flavored reliable byte-stream protocol — entirely in Python. You will implement the core mechanisms that make TCP reliable: a checksum for corruption detection, a three-way handshake to open a connection, a sliding-window for flow control, cumulative acknowledgment, selective acknowledgment (SACK), and retransmission on loss.

The assignment is structured in three bundles. Passing Bundle 1 earns a C, Bundle 2 earns a B, and Bundle 3 earns an A. Each bundle builds on the previous one.

## Setup

```bash
python -m venv venv

# Windows
venv\Scripts\activate
# Mac / Linux
source venv/bin/activate

pip install -r requirements.txt

# Copy starter files into your working directory
cp template/rdp/framing.py   src/rdp/
cp template/rdp/connection.py src/rdp/
cp template/rdp/timers.py    src/rdp/
```

After copying, open `src/rdp/framing.py` and start there.

## Project Structure

```
rdp-assignment/
├── src/rdp/
│   ├── framing.py        <-- YOU IMPLEMENT THIS (Bundle 1)
│   ├── connection.py     <-- YOU IMPLEMENT THIS (Bundles 2-3)
│   └── timers.py         ships working; do not modify
├── tests/
│   ├── bundle1/          framing tests
│   ├── bundle2/          handshake + data transfer tests
│   └── bundle3/          retransmission, SACK, loss recovery tests
├── template/rdp/         starter stubs — copy to src/rdp/ to begin
├── docs/protocol/
│   └── wire-format.md    packet layout reference
└── AI_POLICY.md          AI use policy
```

Files you edit: `src/rdp/framing.py` and `src/rdp/connection.py`.  
Files you must **not** modify: anything under `tests/`, `template/`, or `solution/`.

## Running Tests

```bash
# Bundle 1 — framing (start here)
pytest tests/bundle1/ -v

# Bundle 2 — handshake + data transfer
pytest tests/bundle2/ -v

# Bundle 3 — retransmission, SACK, corruption
pytest tests/bundle3/ -v

# All tests at once
pytest -v
```

Bundle 2 and Bundle 3 tests run scenario files (JSON) through a harness that simulates packet delivery, drops, and corruption. When a test fails the harness prints a diagnostic showing the exact assertion that failed, the actual protocol state at that point, and a hint about which code path to investigate. Read that output carefully — it tells you where in your state machine the divergence occurred.

## Bundle Descriptions

**Bundle 1 — Framing** (`src/rdp/framing.py`)  
Implement `compute_checksum`, `is_corrupt`, `_pack`, `parse`, and the six packet-builder functions (`build_syn`, `build_syn_ack`, `build_ack`, `build_data`, `build_fin`, `build_fin_ack`). All functions are pure (no state). Read the wire-format reference and the docstrings before writing any code.

**Bundle 2 — Handshake + Data Transfer** (`src/rdp/connection.py`)  
Implement the `TCPConnection` state machine: the three-way SYN / SYN-ACK / ACK handshake, in-order data delivery, byte-indexed sequence numbers, sliding-window flow control, cumulative ACK, and a clean FIN / FIN-ACK teardown.

**Bundle 3 — Reliability** (`src/rdp/connection.py`)  
Extend Bundle 2 with retransmission on timer expiry, SACK-aware out-of-order buffering, `_rebuild_sack_blocks`, loss recovery for SYN and FIN packets, and correct behavior under simulated corruption.

## Protocol Reference

The byte-level packet layout is specified in `docs/protocol/wire-format.md`. Read it before implementing anything in `framing.py`.

## Academic Integrity and AI Policy

See `AI_POLICY.md` for the full policy. The short version: you are expected to write your own code. AI tools may help you understand concepts, read error messages, and debug, but you may not use them to generate complete function bodies for graded code.

## Grading

| Bundle | What it covers | Grade |
|--------|----------------|-------|
| 1 | Checksum, packet building/parsing | C |
| 2 | Handshake, data transfer, flow control | B |
| 3 | Retransmission, SACK, loss recovery | A |

You must pass **all tests in a bundle** to earn credit for that bundle. Partial bundle credit is not awarded.
