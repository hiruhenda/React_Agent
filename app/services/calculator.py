import ast
import operator

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_MAX_EXPONENT = 10000  # Protection against 2 ** 999999999 denial of service


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    elif isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")
        return node.value
    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return _ALLOWED_OPERATORS[op_type](_eval_node(node.operand))
    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if op_type is ast.Pow and (isinstance(right, (int, float)) and right > _MAX_EXPONENT):
            raise ValueError(f"Exponent exceeds safety threshold ({_MAX_EXPONENT})")
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            raise ZeroDivisionError("Division by zero")
        return _ALLOWED_OPERATORS[op_type](left, right)
    else:
        raise ValueError(f"Unsupported expression syntax: {type(node).__name__}")


def evaluate_expression(expr: str) -> str:
    """Evaluates an arithmetic expression safely using an AST whitelist."""
    clean_expr = expr.strip()
    if not clean_expr:
        raise ValueError("Expression is empty")
    try:
        parsed = ast.parse(clean_expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"Malformed arithmetic expression: {str(e)}")
    
    result = _eval_node(parsed)
    # Format floating numbers that are integers cleanly
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    return str(result)