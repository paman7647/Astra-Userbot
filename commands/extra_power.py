import asyncio
import base64

import aiohttp

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="ss",
    description="Take a screenshot of a website.",
    category="Tools & Utilities",
    aliases=["screenshot", "webshot"],
    usage="<url> (e.g. .ss google.com)",
    is_public=True,
)
async def ss_handler(client: Client, message: Message):
    """Website screenshot plugin."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "❌ **Usage:** `.ss <url>`")

    url = args[0]
    if not url.startswith("http"):
        url = "https://" + url

    status_msg = await edit_or_reply(
        message, f"📸 **Astra Web Capture**\n━━━━━━━━━━━━━━━━━━━━\n🌐 **Target:** `{url}`..."
    )

    # Fallback Chain for maximum reliability
    providers = [
        f"https://pageshot.site/api/render?url={url}&width=1280&height=720&format=jpeg",
        f"https://s.wordpress.com/mshots/v1/{url}?w=1280&h=720",
        f"https://image.thum.io/get/width/1280/crop/720/noAnimate/{url}",
    ]

    provider_names = ["PageShot", "WordPress", "Thum.io"]
    img_data = None

    async with aiohttp.ClientSession() as session:
        for i, prov_url in enumerate(providers):
            try:
                name = provider_names[i]
                try:
                    await status_msg.edit(
                        f"📸 **Astra Web Capture**\n━━━━━━━━━━━━━━━━━━━━\n🌐 **Target:** `{url}`\n⚙️ **Engine:** `{name}`..."
                    )
                except:
                    pass

                async with session.get(prov_url, timeout=aiohttp.ClientTimeout(total=25)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        if len(data) > 10000:
                            img_data = data
                            break
            except:
                continue

    if img_data:
        b64_data = base64.b64encode(img_data).decode("utf-8")
        media = {"mimetype": "image/jpeg", "data": b64_data, "filename": "screenshot.jpg"}

        sent = False
        try:
            await client.send_media(message.chat_id, media, caption=f"📸 **Screenshot:** {url}")
            sent = True
        except Exception as media_err:
            logger.debug(f"Image upload failed: {media_err}. Retrying as document...")
            try:
                # Retry as document/file
                await client.send_file(
                    message.chat_id, img_data, filename="screenshot.png", caption=f"📸 **Screenshot (Doc):** {url}"
                )
                sent = True
            except Exception as file_err:
                logger.error(f"Screenshot upload totally failed: {file_err}")

        if sent:
            try:
                await status_msg.delete()
            except:
                pass
            return

    try:
        await status_msg.edit(
            "⚠️ **Astra Web Capture:** All capture engines failed. The site might be heavily protected or offline."
        )
    except:
        pass


@astra_command(
    name="purge",
    description="Delete multiple messages from the current chat.",
    category="Group Management",
    aliases=["del", "purgemsg"],
    usage="[count] (reply to a message to start purging from there)",
    owner_only=True,
)
async def purge_handler(client: Client, message: Message):
    """Bulk message deletion plugin."""
    if not message.has_quoted_msg:
        return await edit_or_reply(message, "🗑️ Reply to a message to start purging from there.")

    args = extract_args(message)
    count = int(args[0]) if args and args[0].isdigit() else 10
    count = min(count, 100)  # Limit to 100 for safety

    status_msg = await edit_or_reply(
        message, f"🗑️ **Astra Purge Utility**\n━━━━━━━━━━━━━━━━━━━━\n✨ *Deleting {count} messages...*"
    )

    # Fetch messages after the quoted one
    # Note: purged messages must be the bot's own or if the bot is admin
    # On WhatsApp, you can usually only delete your own messages for everyone
    # or others' if you are admin.

    messages = await client.fetch_messages(
        message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id),
        limit=count,
        message_id=message.quoted.id,
        direction="after",
    )

    to_delete = [message.quoted.id] + [msg.id for msg in messages]

    # WhatsApp Web Bridge usually has a bulk delete or we loop
    deleted_count = 0
    for msg_id in to_delete:
        try:
            # Use client.delete_message directly as found in dir(Client)
            await client.delete_message(message.chat_id, msg_id)
            deleted_count += 1
        except:
            pass

    try:
        await status_msg.edit(
            f"✅ **Astra Purge Utility**\n━━━━━━━━━━━━━━━━━━━━\n🗑️ *Successfully purged* **{deleted_count}** *messages.*"
        )
    except:
        pass
    await asyncio.sleep(3)
    try:
        await status_msg.delete()
    except:
        pass
