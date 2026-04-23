# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a Python project starter template for introductory programming courses. The repository provides a minimal foundation for students learning Python, with focus on clarity and educational value.

## Educational Context

This starter is designed for students with limited Python experience. The project includes Claude agents specialized for:
- Creating programming assignments with detailed specifications
- Writing clear, well-commented Python code for beginners
- Developing step-by-step tutorials
- Debugging and code review for learning
- Grading based on assignment specifications

## Project Setup Commands

### Virtual Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Common Development Commands

```bash
# Test with specification grading (recommended)
python run_tests.py        # Runs tests and shows grade achieved
python run_tests.py -v     # Verbose output with failing test details

# Test the reference solution
# Place solution files in solution/ directory, then:
python run_tests.py        # Automatically tests solution if present

# Standard pytest commands
pytest                     # Run all tests
pytest -v                  # Verbose output
pytest tests/test_example.py              # Run specific test file
pytest tests/test_example.py::test_name   # Run specific test
pytest --cov=src          # Run with coverage
pytest -m "bundle(1)"     # Run only Bundle 1 tests
```

## Project Structure

```
project/
├── src/               # Student implementation (copied from template/)
├── solution/          # Reference solution (instructor only)
├── tests/            # Test files with bundle markers
├── template/         # Starter code for students
├── run_tests.py      # Specification grading test runner
├── requirements.txt  # Project dependencies
├── README.md         # Project documentation
└── .gitignore       # Git ignore patterns
```

The `run_tests.py` script:
- Detects if `solution/` exists and tests it automatically
- Backs up student code, tests solution, then restores student code
- Provides clear grading feedback based on bundle completion
- Shows which bundle level (1, 2, or 3) corresponds to which grade (C, B, or A)

## Testing Guidelines

- Use pytest for all testing
- Write simple, clear test cases
- Focus on testing functionality, not implementation details
- Use descriptive test function names that explain what is being tested

## Code Style for Students

When writing or reviewing student code:
- Use clear, descriptive variable names
- Add comments explaining logic (not just what, but why)
- Break complex problems into simple functions
- Include docstrings for all functions
- Prefer readability over cleverness
- Use type hints where helpful for learning

## Available Tools

### Testing
- **pytest**: Simple, powerful testing framework
- **pytest-cov**: Coverage reporting to see which code is tested
- **pytest-timeout**: Prevent tests from running too long

### Utilities
- **click**: For creating command-line interfaces
- **rich**: For colorful, formatted terminal output

## Important Notes

- This is an educational repository - prioritize learning over optimization
- Code should be accessible to beginners
- Include helpful error messages that guide debugging
- Examples should be complete and runnable
- Focus on teaching good programming practices gradually

## Development Trace Capture

This template includes an automatic commit/push layer in `tests/conftest.py` and `tests/_capture/`. It fires on every pytest invocation (CLI, IDE test runner, debug mode) and creates a structured commit of the student's working tree.

- Never modify `tests/_capture/` files casually — changes invalidate the integrity audit hashes in `tools/INTEGRITY_HASHES.txt`.
- If you add new files that students should *not* be captured into commits, scope `git_ops.stage_student_files()` explicitly rather than extending `.gitignore`.
- Default per-test timeout is 30 seconds (configured in `pyproject.toml`). Override per-test with `@pytest.mark.timeout(N)`.
- Session-level hard deadline is enforced by `tests/_capture/watchdog.py` — see plan document for rationale.

### Calibrate timeout before releasing each assignment

The default `--timeout=30` in `pyproject.toml` is a generic ceiling, not an assignment-specific target. Before distributing an assignment:

1. Run the reference solution locally and note the slowest test's wall time.
2. Set `--timeout=` in `pyproject.toml` to roughly 3-5x that slowest time (headroom for slow student machines, CI runners, debuggers). Typical values for intro-Python assignments: 5-15 seconds. Networking assignments with sockets may need 30-60 seconds.
3. The watchdog's session deadline derives from the per-test timeout (`max(120, 3 * N * per_test_timeout)`), so a shorter per-test timeout both catches hangs faster AND shortens the session watchdog window proportionally. Picking a realistic timeout for the specific assignment gives students faster feedback on a hung test.
4. If specific tests need longer (e.g., one integration test with real I/O), override with `@pytest.mark.timeout(N)` on that test rather than relaxing the global default.

### Codex integration (logging + guardrails)

This template ships Codex (OpenAI CLI) scaffolding:
- **`AGENTS.md` (root)** — Socratic tutor framing Codex reads automatically when cwd is inside the repo.
- **`.codex/config.toml`** — pre-seeded `approval_policy = "on-request"`, sandbox `workspace-write`, `model_reasoning_effort = "medium"`. Layers on top of the user's global `~/.codex/config.toml`.
- **`AI_POLICY.md`** — student-facing disclosure of what is captured.
- **`tests/_capture/codex_ingest.py`** — scans `$CODEX_HOME/sessions/` (default `~/.codex/sessions/`) recursively on every pytest `session_finish`, filters rollouts by `cwd` match (with Windows drive-letter normalization) and mtime ≥ session start, copies matches into `.codex-transcripts/`, where `stage_student_files` picks them up.

Rollout schema (from real Codex 0.119.x, documented in `docs/superpowers/plans/2026-04-22-codex-rollout-notes.md`): first JSONL line has `type == "session_meta"` with `payload.cwd` nested. Rollouts live at `~/.codex/sessions/YYYY/MM/DD/rollout-<timestamp>-<uuid>.jsonl`.

If you add new paths that should enter capture commits, extend the allowlist in `tests/_capture/git_ops.py::stage_student_files`. The pre-filter (`[p for p in allowlist if (repo / p).exists()]`) is load-bearing — naive `git add -A -- <paths>` exits 128 and stages nothing when any pathspec is missing; `--ignore-errors` does NOT suppress that.

Deferred work (tracked for future plans): custom MCP server for synchronous tool-call interception; `[notify]` hook integration for per-turn hooks.