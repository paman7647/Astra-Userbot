from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="ai",
    description="Chat with Google Gemini AI",
    category="AI & Search",
    aliases=["chat", "ask", "gemini"],
    usage="<prompt> (e.g. 'Hello AI!')",
    owner_only=False,
)
async def ai_handler(client: Client, message: Message):
    """Chat with Google Gemini AI"""
    args_list = extract_args(message)

    prompt = " ".join(args_list)

    # Handle quoted message if no prompt provided
    if not prompt and message.has_quoted_msg:
        quoted = message.quoted
        if quoted:
            prompt = quoted.body

    if not prompt:
        return await edit_or_reply(
            message,
            "📋 **Usage:** Please provide a prompt or reply to a message.\n*Example:* `.ai What is the capital of France?`",
        )

    from config import config

    api_key = config.GEMINI_API_KEY
    if not api_key:
        return await edit_or_reply(
            message, " ❌ Gemini API key not found. Please set `GEMINI_API_KEY` environment variable."
        )

    from google import genai

    gen_client = genai.Client(api_key=api_key)

    status_msg = await edit_or_reply(message, "✨ **Astra AI**\n━━━━━━━━━━━━━━━━━━━━\n🧠 *Thinking...*")

    import asyncio

    # Run in a thread if it's blocking
    response = await asyncio.to_thread(
        gen_client.models.generate_content, model="gemini-3-flash-preview", contents=prompt
    )

    if response and response.text:
        text = f"✨ **Astra AI**\n━━━━━━━━━━━━━━━━━━━━\n{response.text}"
        await status_msg.edit(text)
    else:
        await status_msg.edit("❌ **Astra AI:** Returned an empty response.")
