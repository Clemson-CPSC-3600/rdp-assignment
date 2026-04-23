import ast

ALLOWED_NODES = (
    ast.Expression, ast.Compare, ast.Name, ast.Constant, ast.Subscript,
    ast.Load, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.In, ast.NotIn, ast.List, ast.Tuple, ast.And, ast.Or, ast.BoolOp,
)


def evaluate_assertion(expression: str, host_state: dict) -> bool:
    """Safely evaluate an assertion expression against a host's state dict.

    Allowed: comparisons, identifiers (resolved from host_state or treated as
    string literals), integer literals, list/tuple literals, subscript access,
    boolean combinators (and/or). Raises ValueError for anything else.
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"invalid expression: {e}") from e
    _validate_ast(tree)
    return _walk(tree.body, host_state)


def _validate_ast(node):
    for child in ast.walk(node):
        if not isinstance(child, ALLOWED_NODES):
            raise ValueError(f"disallowed AST node type: {type(child).__name__}")


def _walk(node, state):
    if isinstance(node, ast.Compare):
        left = _walk(node.left, state)
        for op, comparator in zip(node.ops, node.comparators):
            right = _walk(comparator, state)
            if not _apply_op(op, left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.BoolOp):
        values = [_walk(v, state) for v in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
    if isinstance(node, ast.Name):
        if node.id in state:
            return state[node.id]
        return node.id  # bare identifier → string literal fallback
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Subscript):
        container = _walk(node.value, state)
        key = _walk(node.slice, state)
        return container[key]
    if isinstance(node, ast.List):
        return [_walk(elt, state) for elt in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_walk(elt, state) for elt in node.elts)
    raise ValueError(f"unexpected node in walk: {type(node).__name__}")


def _apply_op(op, left, right):
    if isinstance(op, ast.Eq): return left == right
    if isinstance(op, ast.NotEq): return left != right
    if isinstance(op, ast.Lt): return left < right
    if isinstance(op, ast.LtE): return left <= right
    if isinstance(op, ast.Gt): return left > right
    if isinstance(op, ast.GtE): return left >= right
    if isinstance(op, ast.In): return left in right
    if isinstance(op, ast.NotIn): return left not in right
    raise ValueError(f"unsupported comparison operator: {op}")
