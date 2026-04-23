# RDP Writeup

Due: [see assignment page on Canvas]

## Purpose

The writeup demonstrates that you understand how your implementation works —
not just that it passes tests. Passing tests is necessary but not sufficient:
a student who copies a reference solution or generates code with AI still passes
tests. The writeup is the primary evidence of your own authorship and
understanding. Graders will ask follow-up questions if any section is vague.

## Instructions

Choose **3 scenarios** from the test suite, covering **at least 3 different
categories** from the following list:

- `retransmit`
- `sack`
- `ack_loss`
- `corruption`
- `handshake_loss`
- `teardown_edge`

For each scenario write approximately 500 words:

1. **Scenario name and category** — state the file path (e.g.,
   `tests/bundle3/sack/out_of_order_recovery.json`) and the category.

2. **What the scenario tests** — in your own words, describe the network
   condition being simulated and why it is a hard case for a reliable transport.
   Do not simply copy the scenario file's comments or test docstrings.

3. **Walk through your implementation** — trace the event sequence from the
   scenario JSON through your code. For each key step, reference the line in
   your `connection.py` (or `framing.py`) where the decision happens. Example:
   "At event 2, the `drop_next` trap fires and the DATA packet is silently
   dropped. When the timer expires in `on_timer_expire` (line XX), my code calls
   `_retransmit_oldest` (line YY), which checks `_retransmit_count` for the
   oldest unacked sequence number and re-sends the segment."

4. **Commit SHA** — paste the 7-character git SHA of the commit your writeup
   describes (run `git log --oneline -1` in your repo). Your writeup must
   describe code that actually exists in your commit history.

## Submission

Submit a single PDF to Canvas with all three scenario walkthroughs.

Your writeup must:
- Reference specific line numbers in your implementation
- Be written in your own words (AI-assisted drafting is OK for grammar and
  structure, but the analysis must be yours)
- Describe your actual code, not the reference solution or a generic description
