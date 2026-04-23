import pytest
from tests._harness.assertions import evaluate_assertion


def test_simple_equality_true():
    assert evaluate_assertion("window_base == 1000", {"window_base": 1000}) is True


def test_simple_equality_false():
    assert evaluate_assertion("window_base == 1000", {"window_base": 999}) is False


def test_greater_equal():
    assert evaluate_assertion("retransmit_count >= 1", {"retransmit_count": 2}) is True


def test_subscript_access():
    assert evaluate_assertion("retransmit_count[1000] >= 1",
                              {"retransmit_count": {1000: 3}}) is True


def test_state_identifier_as_string():
    # State values are compared against bare identifiers like ESTABLISHED,
    # which the evaluator treats as string literals when not in state dict.
    assert evaluate_assertion("state == ESTABLISHED",
                              {"state": "ESTABLISHED"}) is True


def test_disallowed_ast_node_raises():
    with pytest.raises(ValueError):
        evaluate_assertion("__import__('os')", {})


def test_function_call_disallowed():
    with pytest.raises(ValueError):
        evaluate_assertion("len(sack_blocks) > 0", {"sack_blocks": [(1, 2)]})
