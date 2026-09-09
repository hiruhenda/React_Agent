from langchain_core.tools import tool
from app.services.calculator import evaluate_expression

@tool
def calculate_expression(expression: str) -> str:
    """Useful for evaluating arithmetic expressions and mathematical calculations.
    Input must be a single math expression string, e.g. '14 * 24' or '67000000 / 357022'.
    Do not calculate mentally; always use this tool for arithmetic.
    """
    try:
        return evaluate_expression(expression)
    except Exception as e:
        return f"Calculation Error: {str(e)}"
