"""
Essential Utilities: Carbon, Quotly
------------------------------------------
A suite of tools for developers and power users.
- Carbon: Generate beautiful code images.
- Quotly: Create sticker quotes from messages.
"""

import base64

import aiohttp
from utils.helpers import get_contact_name, safe_edit

from . import *
from utils.helpers import edit_or_reply


# --- CARBON CODE IMAGE ---
@astra_command(
    name="carbon",
    description="Create a beautiful code snippet image.",
    category="Tools & Utilities",
    aliases=["snippet"],
    usage="<text/reply> (reply to code or paste text)",
    is_public=True,
)
async def carbon_handler(client: Client, message: Message):
    """
    Uses Carbonara API to generate code images.
    """
    args_list = extract_args(message)
    code = ""

    if message.has_quoted_msg:
        code = message.quoted.body
    elif args_list:
        code = " ".join(args_list)

    if not code:
        return await edit_or_reply(
            message, "💻 **Astra Carbon Utility**\n━━━━━━━━━━━━━━━━━━━━\n❌ **Usage:** Reply to code or paste text."
        )

    status_msg = await edit_or_reply(
        message, "🎨 **Astra Carbon Utility**\n━━━━━━━━━━━━━━━━━━━━\n✨ *Generating high-res image...*"
    )

    # Carbonara API
    url = "https://carbonara.solopov.dev/api/cook"
    payload = {"code": code, "backgroundColor": "rgba(171, 184, 195, 1)", "theme": "seti"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                image_data = await resp.read()
                b64_data = base64.b64encode(image_data).decode("utf-8")

                media = {"mimetype": "image/jpeg", "data": b64_data, "filename": "carbon.jpg"}
                await client.send_media(message.chat_id, media, caption="💻 **Astra Code Snippet**")
                await status_msg.delete()
            else:
                await safe_edit(status_msg, "❌ **Astra Carbon:** Failed to generate image.")


# --- QUOTLY STICKER ---
@astra_command(
    name="quotly",
    description="Create a sticker quote from a message.",
    category="Fun & Memes",
    aliases=["q", "quote"],
    usage="(reply to message) (optionally .quotly 3 to quote 3 msgs)",
    is_public=True,
)
async def quotly_handler(client: Client, message: Message):
    """
    Generates a sticker quoting the replied message (and optionally next N messages).
    Usage: .q [count] (reply to start message)
    """
    if not message.has_quoted_msg:
        return await edit_or_reply(
            message, "🗨️ **Astra Quotly**\n━━━━━━━━━━━━━━━━━━━━\n❌ **Usage:** Reply to a message to quote it."
        )

    args = extract_args(message)
    count = 1
    if args and args[0].isdigit():
        count = min(int(args[0]), 10)  # Cap at 10 for performance

    status_msg = await edit_or_reply(
        message,
        f"🎨 **Astra Quotly**\n━━━━━━━━━━━━━━━━━━━━\n✨ *Rendering sequence {'(x' + str(count) + ')' if count > 1 else ''}...*",
    )

    start_quoted = message.quoted
    messages_to_quote = []

    # 1. Fetch sequence if count > 1
    if count > 1:
        # We fetch messages in the chat starting from the quoted message ID
        chat_id_str = message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id)
        fetched = await client.chat.fetch_messages(
            chat_id_str,
            limit=count,
            message_id=start_quoted.id,
            direction="after",  # Fetch subsequent messages
        )
        # Prepend start_quoted if not already in fetched (usually fetch_messages includes the anchor)
        if not fetched or fetched[0].id != start_quoted.id:
            messages_to_quote.append(start_quoted)
        messages_to_quote.extend(fetched[:count])
    else:
        messages_to_quote.append(start_quoted)

    # 2. Build Multi-Message Payload
    quote_list = []
    for msg in messages_to_quote:
        text = msg.body
        if msg.is_media and not text:
            media_type_map = {
                "image": "📸 Photo",
                "video": "🎥 Video",
                "audio": "🎵 Audio",
                "ptt": "🎙️ Voice Note",
                "sticker": "✨ Sticker",
                "document": "📄 Document",
            }
            text = media_type_map.get(msg.type.value, "📦 Media")

        # Resolve Identity
        # Handle both structured JID objects and raw strings
        raw_target = msg.author or msg.chat_id
        sender_id = "0"
        sender_name = "User"

        if raw_target:
            # Resolve target_jid string for helpers
            target_jid_str = raw_target.serialized if hasattr(raw_target, "serialized") else str(raw_target)
            sender_name = await get_contact_name(client, target_jid_str)
            sender_id = raw_target.user if hasattr(raw_target, "user") else target_jid_str.split("@")[0]

        quote_list.append(
            {
                "entities": [],
                "avatar": True,
                "from": {
                    "id": int(float(sender_id)) if sender_id and sender_id.isdigit() else 123456,
                    "name": sender_name,
                    "photo": {"url": "https://telegra.ph/file/18a28f73177695376046e.jpg"},
                },
                "text": text or " ",
                "replyMessage": {},
            }
        )

    payload = {
        "type": "quote",
        "format": "webp",
        "backgroundColor": "#1b1429",
        "width": 512,
        "height": 768,
        "scale": 2,
        "messages": quote_list,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://bot.lyo.su/quote/generate", json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("ok"):
                    sticker_buffer = base64.b64decode(data["result"]["image"])
                    b64_sticker = base64.b64encode(sticker_buffer).decode("utf-8")

                    await client.media.send_sticker(
                        message.chat_id.serialized
                        if hasattr(message.chat_id, "serialized")
                        else str(message.chat_id),
                        b64_sticker,
                        reply_to=start_quoted.id,
                    )
                    await status_msg.delete()
                    return
    await safe_edit(status_msg, "❌ **Astra Quotly:** Failed to render sequence.")
