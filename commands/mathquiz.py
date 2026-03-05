"""
Entertainment Utility: Math Quiz
--------------------------------
Generates randomized arithmetic challenges with spoiler-hidden answers.
"""

import random

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="mathquiz",
    description="Challenge the group with a quick randomized math problem.",
    category="Fun & Memes",
    aliases=["mq"],
    usage=".mathquiz (no arguments)",
    is_public=True,
)
async def mathquiz_handler(client: Client, message: Message):
    """
    Generates a problem, calculates the solution, and renders a
    spoiler-protected quiz card.
    """
    # Generate operands and operator
    a = random.randint(1, 100)
    b = random.randint(1, 50)
    op = random.choice(["+", "-", "*"])

    # Resolve result
    if op == "+":
        result = a + b
    elif op == "-":
        result = a - b
    else:
        result = a * b

    # Render Quiz Card
    report = f"🔢 **Astra Quick Math Quiz**\n\nSolve: `{a} {op} {b} = ?`\n\n💡 *Answer:* ||{result}||"

    await edit_or_reply(message, report)
