"""
Mathematical calculator tool for CriticSearch.
"""

import ast
import operator
import math
from typing import Union


def calculate(expression: str) -> dict:
    """
    Execute safe mathematical expressions.
    
    Supports basic arithmetic operations (+, -, *, /, %, **) and common mathematical functions (sin, cos, tan, log, sqrt, etc.).
    For security reasons, only mathematical expressions are allowed, no arbitrary code execution.
    
    Args:
        expression (str): Mathematical expression to calculate, e.g., "2 + 3 * 4", "sin(30 * pi / 180)", "sqrt(16)"
    
    Returns:
        dict: Dictionary containing calculation results
            {
                "expression": str,  # Original expression
                "result": float,    # Calculation result
                "status": str       # "success" or "error"
            }
    
    Examples:
        >>> calculate("2 + 3 * 4")
        {"expression": "2 + 3 * 4", "result": 14.0, "status": "success"}
        
        >>> calculate("sqrt(16) + 2")
        {"expression": "sqrt(16) + 2", "result": 6.0, "status": "success"}
    """
    
    # Safe operators and functions whitelist
    safe_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    safe_functions = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'sinh': math.sinh,
        'cosh': math.cosh,
        'tanh': math.tanh,
        'log': math.log,
        'log10': math.log10,
        'log2': math.log2,
        'sqrt': math.sqrt,
        'exp': math.exp,
        'ceil': math.ceil,
        'floor': math.floor,
        'degrees': math.degrees,
        'radians': math.radians,
        'factorial': math.factorial,
    }
    
    safe_constants = {
        'pi': math.pi,
        'e': math.e,
        'tau': math.tau,
        'inf': math.inf,
    }
    
    def safe_eval(node):
        """Safe expression evaluation function"""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
            return node.n
        elif isinstance(node, ast.Name):
            if node.id in safe_constants:
                return safe_constants[node.id]
            else:
                raise ValueError(f"Unsafe variable name: {node.id}")
        elif isinstance(node, ast.BinOp):
            left = safe_eval(node.left)
            right = safe_eval(node.right)
            op = safe_operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = safe_eval(node.operand)
            op = safe_operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op(operand)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in safe_functions:
                func = safe_functions[node.func.id]
                args = [safe_eval(arg) for arg in node.args]
                return func(*args)
            else:
                raise ValueError(f"Unsafe function call: {ast.dump(node.func)}")
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")
    
    try:
        # Parse expression
        parsed = ast.parse(expression.strip(), mode='eval')
        
        # Calculate result
        result = safe_eval(parsed.body)
        
        # Ensure result is numeric type
        if isinstance(result, (int, float, complex)):
            return {
                "expression": expression,
                "result": float(result) if not isinstance(result, complex) else result,
                "status": "success"
            }
        else:
            return {
                "expression": expression,
                "result": None,
                "status": "error",
                "error": f"Result is not numeric type: {type(result).__name__}"
            }
            
    except ZeroDivisionError:
        return {
            "expression": expression,
            "result": None,
            "status": "error",
            "error": "Division by zero"
        }
    except (ValueError, SyntaxError, TypeError) as e:
        return {
            "expression": expression,
            "result": None,
            "status": "error",
            "error": str(e)
        }
    except Exception as e:
        return {
            "expression": expression,
            "result": None,
            "status": "error",
            "error": f"Unknown error: {str(e)}"
        } 