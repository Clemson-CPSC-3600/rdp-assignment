# Testing Guide: CPSC 3600 RDP Assignment

## Quick Reference

| Goal | Command |
|------|---------|
| Check your grade | `python run_tests.py` |
| Grade + list failed tests | `python run_tests.py -v` |
| Bundle 1 only (framing) | `pytest tests/bundle1/ -v` |
| Bundle 2 only (handshake + data) | `pytest tests/bundle2/ -v` |
| Bundle 3 only (reliability) | `pytest tests/bundle3/ -v` |
| All tests | `pytest -v` |
| Stop on first failure | `pytest tests/bundle1/ -x` |
| Re-run only failing tests | `pytest --lf` |

Run all commands from the **project root directory** (where `pyproject.toml` lives).

---

## run_tests.py vs pytest

### `python run_tests.py`

Use this to see your grade summary. It runs all tests and prints a report
showing which bundles you passed and what grade that corresponds to.

```
python run_tests.py          # grade summary
python run_tests.py -v       # grade summary + names of failing tests
python run_tests.py --failed # re-run only tests that failed last time
```

### `pytest` directly

Use pytest when you're actively debugging — it gives faster, more detailed
output and lets you target a specific bundle or test.

```bash
# Run a specific bundle
pytest tests/bundle1/ -v
pytest tests/bundle2/ -v
pytest tests/bundle3/ -v

# Run a single framing test
pytest tests/bundle1/test_framing.py::test_checksum_known_vector -v

# Run a single scenario
pytest "tests/bundle3/sack/out_of_order_recovery.json" -v

# Run tests matching a name fragment
pytest tests/bundle3/ -k "sack" -v

# Stop on first failure and show full traceback
pytest tests/bundle1/ -x --tb=long
```

---

## Understanding Test Output

### Bundle 1 — framing tests

These are standard pytest assertions. When a test fails you see the expected
value and what your function actually returned:

```
FAILED tests/bundle1/test_framing.py::test_checksum_known_vector
AssertionError: assert None == 64505
  where None = compute_checksum(b'\x01\x02\x03\x04')
```

`None` means the function returned nothing — it still has `pass` as its body.
Any other unexpected value means the logic is wrong.

### Bundle 2 and 3 — scenario tests

Each scenario test replays a scripted sequence of network events and checks
assertions at specific points. When one fails the harness prints:

```
FAILED tests/bundle3/sack/out_of_order_recovery.json::out_of_order_recovery

AssertionError: Assertion failed after event 3 on host B
  check:    sack_blocks[0] == (1006, 1011)
  actual:   sack_blocks = []
  hint:     B received out-of-order data but _sack_blocks was not updated.
            Check _rebuild_sack_blocks and whether it is called after storing
            a segment in _out_of_order.
```

**Read the `hint` line carefully.** It tells you which code path diverged.

To see the full event sequence for a scenario, open the JSON file. The
`"events"` list is the script; `"assertions"` maps event indices to checks.

---

## Debugging Strategies

### Print the state machine

When a scenario test fails, the most useful first step is to see what state
your connection is in at each step:

```python
def _handle(self, parsed: ParsedPacket) -> None:
    print(f"[{self.role}] state={self._state} pkt={parsed.type}")
    # ... rest of your code
```

Re-run the failing test. If the state sequence diverges from what the scenario
description says, that's where your FSM logic is wrong.

### Check sequence numbers

Sequence number bugs are common and subtle. Add prints to verify:

```python
print(f"[{self.role}] window_base={self._window_base} next_seq={self._next_seq} peer_ack={self._peer_ack_num}")
```

### Isolate a single scenario

Scenario JSON files live at `tests/bundle2/*.json` and `tests/bundle3/**/*.json`.
Run just one at a time while debugging:

```bash
pytest "tests/bundle3/retransmit/double_loss.json" -v -s
```

The `-s` flag disables output capture so your `print` statements appear.

---

## VS Code Integration

### Setting up the test runner

1. Open the project root folder in VS Code
2. Press `Ctrl+Shift+P` → **Python: Select Interpreter** → choose your venv
3. Press `Ctrl+Shift+P` → **Python: Configure Tests** → select pytest → `tests/`
4. Click the **Testing** icon (flask) in the Activity Bar

### Running tests from VS Code

The Testing sidebar shows all tests in a tree. Click ▶ next to any test, file,
or folder to run it. Results appear inline: ✅ passed, ❌ failed.

Bundle 1 tests appear as individual items. Bundle 2 and 3 scenario tests appear
as JSON file nodes.

### Debugging with breakpoints

1. Set a breakpoint by clicking in the gutter (left of the line number)
2. In the Testing sidebar, click the bug icon (**Debug Test**) instead of ▶
3. Execution pauses at your breakpoint

Useful debug panel features:
- **Variables**: inspect `self._state`, `self._unacked`, `self._out_of_order`
- **Call Stack**: trace back from `_handle` to the harness event that triggered it
- **Watch**: add expressions like `self._next_seq - self._window_base` to monitor in-flight bytes

Keyboard shortcuts:
- `F10` — step over
- `F11` — step into
- `Shift+F11` — step out
- `F5` — continue

---

## Timeouts

Each test has a 10-second timeout. If your code hangs:

- Check for an infinite loop (e.g., `while True` without a break condition)
- Check that the timer is being stopped after a handshake completes — if it
  keeps firing and retransmitting, the scenario never advances
- Check that `_drain_out_of_order` has a termination condition (it loops while
  `_peer_ack_num` is in `_out_of_order`; if you accidentally set `_peer_ack_num`
  wrong, it can loop forever)

The 10-second limit gives roughly 14x headroom over the slowest expected test
on a fast machine, so legitimate implementations never hit it.

---

## Troubleshooting Setup

**`ModuleNotFoundError: No module named 'src'`**  
You're running pytest from inside `src/` or a subdirectory. Always run from
the project root (where `pyproject.toml` is).

**Tests not appearing in VS Code Test Explorer**  
Press `Ctrl+Shift+P` → **Python: Refresh Tests**. If they still don't appear,
verify that the selected interpreter is the project venv (not system Python).

**`ImportError` on a bundle 1 test**  
Your `framing.py` has a syntax error that prevents it from importing. Run
`python src/rdp/framing.py` to see the error before running pytest.
