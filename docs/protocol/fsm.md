# RDP Protocol Diagrams

GitHub and VS Code both render Mermaid diagrams inline. If you are reading
a plain text copy, every code block tagged `mermaid` is a diagram.

---

## Connection State Machine

Each `TCPConnection` starts in **LISTEN** and ends in **CLOSED**.
The diagram shows every state transition.

Notation: `recv X` = packet X arrived from network; `send X` = packet X
transmitted; `timer` = retransmit timer fired. Events that keep the connection
in **ESTABLISHED** (receiving DATA, receiving ACK, timer retransmit) are
described in the note below rather than shown as self-arrows.

```mermaid
stateDiagram-v2
    direction LR

    [*] --> LISTEN

    LISTEN --> SYN_SENT     : recv_from_app(∅)\nsend SYN · start timer
    LISTEN --> SYN_RECEIVED : recv SYN\nsend SYN-ACK · start timer

    SYN_SENT --> SYN_SENT     : timer\nsend SYN (retry)
    SYN_SENT --> ESTABLISHED  : recv SYN-ACK\nsend ACK · stop timer

    SYN_RECEIVED --> SYN_RECEIVED : timer\nsend SYN-ACK (retry)
    SYN_RECEIVED --> ESTABLISHED  : recv ACK\nstop timer

    ESTABLISHED --> FIN_WAIT : close()\nsend FIN · start timer
    ESTABLISHED --> CLOSING  : recv FIN\nsend FIN-ACK

    FIN_WAIT --> FIN_WAIT : timer\nsend FIN (retry)
    FIN_WAIT --> CLOSED    : recv FIN-ACK\nstop timer
    FIN_WAIT --> CLOSED    : recv FIN\nsend FIN-ACK · stop timer

    CLOSING --> FIN_WAIT : close()\nsend FIN · start timer
    CLOSING --> CLOSED   : recv FIN-ACK\nstop timer

    CLOSED --> CLOSING : recv FIN\nsend FIN-ACK

    CLOSED --> [*]
```

**ESTABLISHED in-state events** (no state change):

| Event | Action |
|-------|--------|
| `recv DATA` (in-order) | Append to receive buffer; advance `_peer_ack_num`; drain out-of-order buffer; send ACK |
| `recv DATA` (out-of-order) | Store in `_out_of_order`; rebuild SACK blocks; send ACK with SACK |
| `recv DATA` (duplicate) | Send ACK with current cumulative ack number |
| `recv ACK` | Advance `_window_base`; prune `_unacked` with SACK blocks; try to send more from queue |
| `timer` | Retransmit oldest unacked segment; increment retransmit count |

---

## Three-Way Handshake

Both sides start in LISTEN. The initiator triggers the handshake by calling
`recv_from_app(b"")`.

```mermaid
sequenceDiagram
    participant A as A (initiator)
    participant B as B (responder)

    Note over A: LISTEN
    Note over B: LISTEN

    A->>B: SYN  seq=isn_A
    Note over A: SYN_SENT

    B->>A: SYN-ACK  seq=isn_B  ack=isn_A+1
    Note over B: SYN_RECEIVED

    A->>B: ACK  ack=isn_B+1
    Note over A: ESTABLISHED
    Note over B: ESTABLISHED
```

After the handshake: `_next_seq = isn + 1` and `_window_base = isn + 1` on
both sides. The SYN occupies one sequence number.

---

## In-Order Data Transfer

The sender keeps sending as long as bytes-in-flight < `window_size`.
When the window fills, it stalls until an ACK advances `_window_base`.

```mermaid
sequenceDiagram
    participant A as A (sender)
    participant B as B (receiver)

    Note over A,B: ESTABLISHED — window_size=30  A.next_seq=1001

    A->>B: DATA  seq=1001  len=10
    A->>B: DATA  seq=1011  len=10
    A->>B: DATA  seq=1021  len=10
    Note over A: 30 bytes in flight — window full, cannot send more

    B->>A: ACK  ack=1031
    Note over A: window_base→1031  window reopens
    Note over B: bytes_delivered=30
```

---

## Out-of-Order Delivery and SACK

When a segment arrives out of order, the receiver stores it in `_out_of_order`,
reports its range in a SACK block, and replies with the cumulative ACK up to
the gap. The sender retransmits the missing segment. Once the gap is filled,
`_drain_out_of_order` delivers the buffered data in order.

```mermaid
sequenceDiagram
    participant A as A (sender)
    participant B as B (receiver)

    Note over A,B: ESTABLISHED

    A->>B: DATA  seq=1001  len=5
    A--xB: DATA  seq=1006  len=5  [dropped]
    A->>B: DATA  seq=1011  len=5

    Note over B: gap at [1006, 1011)<br/>_out_of_order = {1011: data}
    B->>A: ACK  ack=1006  SACK=[(1011,1016)]

    Note over A: retransmit timer fires
    A->>B: DATA  seq=1006  len=5  [retransmit]

    Note over B: gap filled — drain delivers both segments
    B->>A: ACK  ack=1016  SACK=[]
    Note over B: bytes_delivered=15
```

Up to three non-overlapping SACK blocks can appear in a single ACK. The sender
uses them to skip already-received segments when deciding what to retransmit.

---

## Handshake Loss and Retransmit

The retransmit timer fires if a SYN or SYN-ACK is not acknowledged within
`timer_interval`. Both sides retry up to `MAX_HANDSHAKE_RETRIES` times.

```mermaid
sequenceDiagram
    participant A as A (initiator)
    participant B as B (responder)

    A--xB: SYN  seq=isn_A  [dropped]
    Note over A: SYN_SENT — timer running

    Note over A: timer fires
    A->>B: SYN  seq=isn_A  [retransmit]

    B->>A: SYN-ACK  seq=isn_B  ack=isn_A+1
    Note over B: SYN_RECEIVED

    A->>B: ACK  ack=isn_B+1
    Note over A: ESTABLISHED
    Note over B: ESTABLISHED
```

---

## Unilateral Teardown

The initiating side reaches CLOSED immediately when its FIN-ACK arrives.
The responding side reaches CLOSING and remains there until its own `close()`
is called (or until the session ends).

```mermaid
sequenceDiagram
    participant A as A (initiates close)
    participant B as B

    Note over A,B: ESTABLISHED

    A->>B: FIN  seq=N
    Note over A: FIN_WAIT

    B->>A: FIN-ACK  ack=N+1
    Note over B: CLOSING

    Note over A: CLOSED — timer stopped
```

---

## Bidirectional Teardown

Both sides eventually call `close()`. The second close is issued from CLOSING,
which sends a FIN and re-enters the FIN_WAIT / CLOSED cycle.

```mermaid
sequenceDiagram
    participant A as A
    participant B as B

    Note over A,B: ESTABLISHED

    rect rgb(235,245,255)
        Note over A,B: A initiates close
        A->>B: FIN  seq=M
        Note over A: FIN_WAIT
        B->>A: FIN-ACK  ack=M+1
        Note over B: CLOSING
        Note over A: CLOSED
    end

    rect rgb(255,240,235)
        Note over A,B: B initiates close (from CLOSING)
        B->>A: FIN  seq=N
        Note over B: FIN_WAIT
        A->>B: FIN-ACK  ack=N+1
        Note over A: CLOSING
        Note over B: CLOSED
    end
```

When A receives B's FIN while in CLOSED, it sends a FIN-ACK and transitions
to CLOSING. B receives that FIN-ACK and transitions to CLOSED.
