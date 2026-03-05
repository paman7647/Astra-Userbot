"""
Social Utility: Truth or Dare
-----------------------------
A classic party game for groups.
Fetches randomized prompts from an external API with local fallback.
"""

import random
import time

import aiohttp

from . import *

# Fallback Configuration
TRUTHS = [
    "What is your biggest fear?",
    "Have you ever lied to your best friend?",
    "What is your deepest dark secret?",
    "Who is your crush?",
    "What's the most embarrassing thing you've ever done?",
    "What is your biggest regret?",
    "Have you ever cheated on a test?",
    "What is the worst gift you have ever received?",
    "What is your biggest insecurity?",
]

DARES = [
    "Send a voice note singing a song.",
    "Post a status saying 'I am a monkey'.",
    "Call your crush and say 'I love you'.",
    "Send a selfie making a funny face.",
    "Change your profile picture to a monkey for 1 hour.",
    "Send a voice note saying 'I am stupid' 5 times.",
    "Send your last copied text.",
    "Send a screenshot of your home screen.",
]


async def fetch_prompt(mode: str) -> str:
    """Fetches a prompt from the API, returns None on failure."""
    url = f"https://api.truthordarebot.xyz/v1/{mode}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("question")
    except Exception:
        return None
    return None


@astra_command(
    name="truth",
    description="Classic Truth or Dare game for social fun.",
    category="Fun & Memes",
    aliases=["dare", "td"],
    usage="<truth|dare> (e.g. truth or dare)",
    is_public=True,
)
async def truth_handler(client: Client, message: Message):
    """
    Renders a randomized prompt from API or local fallback.
    """
    args_list = extract_args(message)
    body_lower = message.body.lower()

    # Choice Resolution
    if args_list:
        choice = args_list[0].lower()
    elif body_lower.startswith((".truth", "!truth", "/truth")):
        choice = "truth"
    elif body_lower.startswith((".dare", "!dare", "/dare")):
        choice = "dare"
    else:
        choice = "truth"

    # Expand abbreviations
    if choice in ["t", "tr"]:
        choice = "truth"
    if choice in ["d", "dr"]:
        choice = "dare"

    if choice == "truth":
        status_msg = await edit_or_reply(message, " 🤔 *Fetching truth...*")
        prompt = await fetch_prompt("truth") or random.choice(TRUTHS)
        time.sleep(0.5)
        await status_msg.edit(f"🤔 **Astra Truth:**\n\n_{prompt}_")

    elif choice == "dare":
        status_msg = await edit_or_reply(message, " 🔥 *Fetching dare...*")
        prompt = await fetch_prompt("dare") or random.choice(DARES)
        time.sleep(0.5)
        await status_msg.edit(f"🔥 **Astra Dare:**\n\n_{prompt}_")

    else:
        await edit_or_reply(message, " 📋 Usage: `.truth` | `.dare` | `.td <truth|dare>`")
