# RDP Implementation Reference

This document describes the **internal code behavior** of the `TCPConnection` class — what data structures change, what decisions are made, and in what order. It is a companion to `fsm.md`, which covers the state-machine transitions and packet exchange between hosts.

Each section below shows one logical path through the code. The variable names used in node labels match the Python attributes directly so you can cross-reference with the source.

---

## 1. Incoming Packet Processing

Every packet that arrives from the network enters through `recv_from_network`. Before any protocol logic runs, the packet is checked for corruption and then parsed. Only a well-formed packet is dispatched to `_handle`.

```mermaid
flowchart TD
    A([recv_from_network called]) --> B{is_corrupt?}
    B -- yes --> C([Discard silently\nreturn])
    B -- no --> D{parse succeeds?}
    D -- MalformedPacket --> E([Discard silently\nreturn])
    D -- ok --> F[parsed packet ready]
    F --> G([Call _handle with parsed])
```

---

## 2. Send Path

Application data enters through `recv_from_app`. The special case of an empty payload on a LISTEN-state socket triggers the handshake. All other payloads are queued and then flushed by `_try_send_from_queue`, which respects the congestion window before transmitting each segment.

```mermaid
flowchart TD
    A([recv_from_app called]) --> B{state is LISTEN\nAND payload is empty?}
    B -- yes --> C([Call _send_syn\nreturn])
    B -- no --> D[Append payload to _app_send_queue]
    D --> E([Call _try_send_from_queue])

    E --> F{_app_send_queue\nnot empty?}
    F -- no --> Z([Return])
    F -- yes --> G{_can_send_more?\n_next_seq - _window_base\nless than window_size}
    G -- no --> Z
    G -- yes --> H[Pop segment from\nfront of _app_send_queue]
    H --> I[Create _UnackedSegment\nseq=_next_seq, data=payload\nAppend to _unacked]
    I --> J[Send build_data with\n_next_seq and payload]
    J --> K[_next_seq += len of payload]
    K --> L{Was _unacked\nempty before this\nsegment was added?}
    L -- yes --> M[timer.start]
    L -- no --> F
    M --> F
```

---

## 3. Receiving Data

When an established connection receives a DATA packet, `_handle` compares the packet's sequence number against `_peer_ack_num` — the next in-order byte the receiver expects. There are exactly three outcomes: the segment fills the gap perfectly (in-order), it arrives ahead of the gap (out-of-order), or it duplicates something already delivered (duplicate). Each path sends an ACK, but only the in-order path advances `_peer_ack_num` and delivers to the application.

```mermaid
flowchart TD
    A([_handle DATA packet\nESTABLISHED state]) --> B{parsed.seq_num\nvs _peer_ack_num}

    B -- seq equals _peer_ack_num\nin-order --> C[Append payload to\n_app_recv_buffer]
    C --> D[_peer_ack_num += len of payload]
    D --> E([Call _drain_out_of_order])
    E --> F[Send build_ack with\n_peer_ack_num and _sack_blocks]

    B -- seq greater than _peer_ack_num\nout-of-order --> G[Store in _out_of_order\n_out_of_order at seq = payload]
    G --> H([Call _rebuild_sack_blocks])
    H --> I[Send build_ack with\n_peer_ack_num and _sack_blocks]

    B -- seq less than _peer_ack_num\nduplicate --> J[Send build_ack with\n_peer_ack_num and _sack_blocks]
```

---

## 4. ACK Processing

When a DATA packet's ACK is received, `_handle` performs up to four actions in order: advance the window if new bytes are acknowledged, prune `_unacked` using any SACK blocks in the ACK, decide whether to stop or restart the retransmit timer, and then attempt to send more queued data. Window advancement and SACK pruning are independent — SACK pruning always happens even if the cumulative ACK did not move.

```mermaid
flowchart TD
    A([_handle ACK packet\nESTABLISHED state]) --> B{parsed.ack_num\ngreater than _window_base?}

    B -- yes --> C[_bytes_acked += parsed.ack_num - _window_base\n_window_base = parsed.ack_num]
    C --> D[Remove segments from _unacked\nwhere seg.seq + len seg.data\nis <= _window_base]
    D --> E[SACK prune: remove any segment\nwhose range falls entirely\nwithin a received SACK block]

    B -- no --> E

    E --> F{_unacked\nis empty?}
    F -- yes --> G[timer.stop]
    F -- no --> H[timer.start\nrestart]

    G --> I([Call _try_send_from_queue])
    H --> I
```

---

## 5. Retransmit Logic

The retransmit timer fires `on_timer_expire`, which delegates immediately to `_retransmit_oldest`. The action taken depends on the current connection state. Handshake states (SYN_SENT, SYN_RECEIVED) track per-phase retry counts and give up after `MAX_HANDSHAKE_RETRIES`. In ESTABLISHED state, only the oldest unacked segment (index 0 of `_unacked`) is retransmitted.

```mermaid
flowchart TD
    A([on_timer_expire fires]) --> B([Call _retransmit_oldest])

    B --> C{Current state?}

    C -- SYN_SENT --> D[_retransmit_count at SYN\n+= 1]
    D --> E{count greater than\nMAX_HANDSHAKE_RETRIES?}
    E -- yes --> F([Give up\nclose connection])
    E -- no --> G[Resend SYN\ntimer.start]

    C -- SYN_RECEIVED --> H[_retransmit_count at SYN-ACK\n+= 1]
    H --> I{count greater than\nMAX_HANDSHAKE_RETRIES?}
    I -- yes --> F
    I -- no --> J[Resend SYN-ACK\ntimer.start]

    C -- FIN_WAIT --> K[Resend FIN\ntimer.start]

    C -- ESTABLISHED --> L{_unacked\nis empty?}
    L -- yes --> M([Do nothing\nreturn])
    L -- no --> N[seg = _unacked at index 0\noldest unacked segment]
    N --> O[_retransmit_count at seg.seq\n+= 1]
    O --> P[Send DATA for seg\ntimer.start]
```

---

## 6. Out-of-Order Buffer Management

`_drain_out_of_order` is called whenever `_peer_ack_num` advances. It repeatedly checks whether the newly expected sequence number is already buffered in `_out_of_order`, and if so delivers it to the application and advances `_peer_ack_num` again. After the drain loop completes, `_rebuild_sack_blocks` re-computes the SACK ranges from whatever remains in `_out_of_order`.

```mermaid
flowchart TD
    A([_drain_out_of_order called]) --> B{_peer_ack_num\nis a key in _out_of_order?}

    B -- yes --> C[data = _out_of_order.pop at _peer_ack_num]
    C --> D[Append data to _app_recv_buffer]
    D --> E[_peer_ack_num += len of data]
    E --> B

    B -- no --> F([Call _rebuild_sack_blocks])

    F --> G{_out_of_order\nis empty?}
    G -- yes --> H[_sack_blocks = empty list\nreturn]

    G -- no --> I[Sort keys of _out_of_order\ninto ordered list]
    I --> J[Initialize first block\nstart = keys at 0\nend = start + len of data at that key]
    J --> K{More keys\nto process?}

    K -- yes --> L[Next key = next_key]
    L --> M{next_key equals\ncurrent block end?\ncontiguous}
    M -- yes --> N[Extend block end\nby len of data at next_key]
    N --> K
    M -- no --> O[Save current block\nstart new block at next_key]
    O --> K

    K -- no --> P[_sack_blocks = first 3\nmerged blocks]
    P --> Q([Return])
```
