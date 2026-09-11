import ast
import operator
from typing import Tuple, Optional, Any

# Structural whitelist of safe binary operators (Constraint 1: No eval/exec)
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

SAFE_UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

MAX_EXPONENT = 1000  # Guard against memory exhaustion via 2**999999999


def _eval_node(node: ast.AST) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Operator {op_type.__name__} is not allowed")

        left = _eval_node(node.left)
        right = _eval_node(node.right)

        # Check for division by zero
        if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
            raise ZeroDivisionError("Division by zero")

        # Check exponent bounds
        if op_type == ast.Pow and right > MAX_EXPONENT:
            raise OverflowError(f"Exponent {right} exceeds safe limit of {MAX_EXPONENT}")

        return SAFE_OPERATORS[op_type](left, right)

    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_UNARY_OPERATORS:
            raise ValueError(f"Unary operator {op_type.__name__} is not allowed")
        operand = _eval_node(node.operand)
        return SAFE_UNARY_OPERATORS[op_type](operand)

    else:
        raise ValueError(f"Disallowed AST node: {type(node).__name__}")


def safe_calculate(expression: str) -> Tuple[bool, float, Optional[str]]:
    """
    Evaluates an arithmetic expression safely using an AST whitelist.
    Returns: (success: bool, result: float, error_message: Optional[str])
    """
    expr = expression.strip()
    if not expr:
        return False, 0.0, "Expression cannot be empty"

    try:
        parsed = ast.parse(expr, mode="eval")
        result = _eval_node(parsed.body)
        return True, float(result), None
    except ZeroDivisionError:
        return False, 0.0, "Division by zero is undefined"
    except OverflowError as oe:
        return False, 0.0, f"Calculation overflow: {str(oe)}"
    except (ValueError, SyntaxError) as e:
        return False, 0.0, f"Invalid or unsafe arithmetic expression: {str(e)}"
    except Exception as e:
        return False, 0.0, f"Evaluation error: {str(e)}"


# Alias to satisfy callers importing either name
evaluate_expression = safe_calculate