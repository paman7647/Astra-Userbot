# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Entertainment Utility: Math Quiz
--------------------------------
Generates randomized arithmetic challenges with spoiler-hidden answers.
"""

import random
from . import *

@astra_command(
    name="mathquiz",
    description="Challenge the group with a quick randomized math problem.",
    category="Fun/Lite",
    aliases=["mq"],
    usage=".mathquiz (no arguments)",
    is_public=True
)
async def mathquiz_handler(client: Client, message: Message):
    """
    Generates a problem, calculates the solution, and renders a 
    spoiler-protected quiz card.
    """
    try:
        # Generate operands and operator
        a = random.randint(1, 100)
        b = random.randint(1, 50)
        op = random.choice(['+', '-', '*'])

        # Resolve result
        if op == '+': 
            result = a + b
        elif op == '-': 
            result = a - b
        else: 
            result = a * b

        # Render Quiz Card
        report = (
            "🔢 **Astra Quick Math Quiz**\n\n"
            f"Solve: `{a} {op} {b} = ?`\n\n"
            f"💡 *Answer:* ||{result}||"
        )

        await smart_reply(message, report)

    except Exception as e:
        await smart_reply(message, " ⚠️ Quiz generator failure.")
        await report_error(client, e, context='MathQuiz command failure')
