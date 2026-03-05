"""
Educational Utility: Calculator
-------------------------------
A lightweight evaluator for mathematical expressions.
Uses Python's math library for safe execution of functions.
"""

import math

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="calc",
    description="Solve complex mathematical expressions.",
    category="Tools & Utilities",
    aliases=["math", "calculate"],
    usage="<expression> (e.g. 2+2)",
    is_public=True,
)
async def calc_handler(client: Client, message: Message):
    """
    Evaluates geometric, algebraic and basic arithmetic expressions
    within a safe restricted namespace.
    """
    args_list = extract_args(message)
    if not args_list:
        return await edit_or_reply(
            message,
            " 📋 **Mathematical Resolver**\n\n"
            "Please provide an expression to solve.\n"
            "**Example:** `.calc (10 * 2) + math.sqrt(25)`",
        )

    expression = " ".join(args_list)

    # Sandbox execution environment: only 'math' functions allowed
    allowed_names = {k: v for k, v in vars(math).items() if not k.startswith("_")}
    allowed_names["math"] = math  # Allow 'math.sin' syntax

    # restricted eval
    result = eval(expression, {"__builtins__": {}}, allowed_names)

    await edit_or_reply(message, f" 🔢 **Calculation Result**\n\n*Input:* `{expression}`\n*Output:* `{result}`")
