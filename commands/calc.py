# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Educational Utility: Calculator
-------------------------------
A lightweight evaluator for mathematical expressions.
Uses Python's math library for safe execution of functions.
"""

import math
from . import *

@astra_command(
    name="calc",
    description="Solve complex mathematical expressions.",
    category="Education",
    aliases=["math", "calculate"],
    usage="<expression> (e.g. 2+2)",
    is_public=True
)
async def calc_handler(client: Client, message: Message):
    """
    Evaluates geometric, algebraic and basic arithmetic expressions 
    within a safe restricted namespace.
    """
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " 📋 **Mathematical Resolver**\n\n"
                                             "Please provide an expression to solve.\n"
                                             "**Example:** `.calc (10 * 2) + math.sqrt(25)`")

        expression = " ".join(args_list)
        
        # Sandbox execution environment: only 'math' functions allowed
        allowed_names = {k: v for k, v in vars(math).items() if not k.startswith("_")}
        allowed_names['math'] = math # Allow 'math.sin' syntax
        
        # restricted eval
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        
        await smart_reply(message, f" 🔢 **Calculation Result**\n\n"
                                   f"*Input:* `{expression}`\n"
                                   f"*Output:* `{result}`")

    except Exception as e:
        await smart_reply(message, f" ❌ **Math Error:** `{str(e)}`")
        await report_error(client, e, context='Calculator module failure')
