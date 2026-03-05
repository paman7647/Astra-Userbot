"""WhatsApp Status commands using the new Astra v3 API."""

from . import *


@astra_command(
    name="textstatus",
    description="Post a text status update.",
    category="Status",
    aliases=["ts", "statustext"],
    usage="<text> (e.g. .textstatus Hello World)",
    owner_only=True,
)
async def textstatus_handler(client: Client, message: Message):
    """Posts a text status update."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "Usage: `.textstatus <text>`")

    text = " ".join(args)
    status = await edit_or_reply(message, "Posting status...")

    try:
        result = await client.api.send_status(text)
        if result:
            await status.edit("Status posted.")
        else:
            await status.edit("Failed to post status.")
    except Exception as e:
        await status.edit(f"Error: {e}")


@astra_command(
    name="photostatus",
    description="Post a photo/video status (reply to media).",
    category="Status",
    aliases=["ps", "mediastatus", "videostatus"],
    usage="[caption] (reply to image/video)",
    owner_only=True,
)
async def photostatus_handler(client: Client, message: Message):
    """Posts a photo or video as a status update."""
    if not message.has_quoted_msg or not message.quoted:
        return await edit_or_reply(message, "Reply to an image or video to post it as a status.")

    status = await edit_or_reply(message, "Uploading status...")

    try:
        # Download media from quoted message
        media_path = await client.download_media(message.quoted)
        if not media_path:
            return await status.edit("Failed to download media from the replied message.")

        caption = " ".join(extract_args(message)) if extract_args(message) else ""
        result = await client.api.send_photo_status(media_path, caption)

        if result:
            await status.edit("Media status posted.")
        else:
            await status.edit("Failed to post media status.")

        # Cleanup temp file
        import os
        if os.path.exists(media_path):
            os.remove(media_path)
    except Exception as e:
        await status.edit(f"Error: {e}")


@astra_command(
    name="statusviewers",
    description="Check who viewed your latest status.",
    category="Status",
    aliases=["sv", "viewers"],
    usage="<message_id> (optional)",
    owner_only=True,
)
async def statusviewers_handler(client: Client, message: Message):
    """Shows viewers of a status message."""
    args = extract_args(message)

    if not args:
        return await edit_or_reply(message, "Usage: `.statusviewers <status_message_id>`\nReply to a status message or provide its ID.")

    msg_id = args[0]
    status = await edit_or_reply(message, "Fetching viewers...")

    try:
        viewers = await client.api.get_status_viewers(msg_id)
        if not viewers:
            return await status.edit("No viewers found or invalid status ID.")

        text = f"**Status Viewers ({len(viewers)}):**\n\n"
        for v in viewers[:20]:
            vid = v if isinstance(v, str) else str(v)
            text += f"- `{vid.split('@')[0]}`\n"
        if len(viewers) > 20:
            text += f"\n_...and {len(viewers) - 20} more_"
        await status.edit(text)
    except Exception as e:
        await status.edit(f"Error: {e}")
