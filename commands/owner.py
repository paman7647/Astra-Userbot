"""
Owner Commands: Profile and Account Management
--------------------------------------------
Commands to update profile info, bio, pfp, and status stories.
"""

import base64

from utils.bridge_downloader import bridge_downloader

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="setname",
    description="Update your profile display name.",
    category="Owner",
    usage="<new_name> (e.g. John Doe)",
    owner_only=True,
)
async def setname_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, " ⚠️ Provide a new name. Usage: `.setname My New Name`")

    new_name = " ".join(args)
    status_msg = await edit_or_reply(message, f" 🔄 Updating profile name to: *{new_name}*...")

    try:
        await client.account.set_name(new_name)
        await status_msg.edit(f" ✅ Profile name updated to: *{new_name}*")
    except Exception as e:
        await status_msg.edit(f" ❌ Failed to update name: {str(e)}")


@astra_command(
    name="bio",
    description="Update your profile 'About' (Bio) text.",
    category="Owner",
    aliases=["setbio", "setabout"],
    usage="<text> (e.g. Available)",
    owner_only=True,
)
async def setbio_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, " ⚠️ Provide a bio text. Usage: `.bio Available`")

    new_bio = " ".join(args)
    status_msg = await edit_or_reply(message, " 🔄 Updating profile bio...")

    try:
        await client.account.set_about_text(new_bio)
        await status_msg.edit(f" ✅ Bio updated to: *{new_bio}*")
    except Exception as e:
        await status_msg.edit(f" ❌ Failed to update bio: {str(e)}")


@astra_command(
    name="setpfp",
    description="Update your profile picture.",
    category="Owner",
    usage="(reply to image) (e.g. .setpfp reply)",
    owner_only=True,
)
async def setpfp_handler(client: Client, message: Message):
    if not message.has_quoted_msg or not (message.quoted_type and message.quoted_type == MessageType.IMAGE):
        return await edit_or_reply(message, " ⚠️ Reply to an image to set it as your profile picture.")

    status_msg = await edit_or_reply(message, " ⏳ *Updating profile picture...*")

    try:
        # Use high-reliability bridge downloader
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit(" ❌ Failed to extract media from message.")

        media_b64 = base64.b64encode(media_data).decode("utf-8")

        # Call API method
        success = await client.account.update_profile_pic(media_b64)

        if success:
            await status_msg.edit(" ✅ Profile picture updated successfully!")
        else:
            await status_msg.edit(" ❌ Profile picture update returned false.")
    except Exception as e:
        await status_msg.edit(f" ❌ Failed to update PFP: {str(e)}")


@astra_command(
    name="setgpic",
    description="Update the current group's picture.",
    category="Owner",
    aliases=["setgrouppfp"],
    usage="(reply to image) (e.g. .setgpic reply)",
    owner_only=True,
)
async def setgpic_handler(client: Client, message: Message):
    if not str(message.chat_id).endswith("@g.us"):
        return await edit_or_reply(message, " ❌ This command only works in groups.")
    if not message.has_quoted_msg or not (message.quoted_type and message.quoted_type == MessageType.IMAGE):
        return await edit_or_reply(message, " ⚠️ Reply to an image to set it as group picture.")

    status_msg = await edit_or_reply(message, " ⏳ *Updating group picture...*")

    try:
        # Use high-reliability bridge downloader
        media_data = await bridge_downloader.download_media(client, message)
        if not media_data:
            return await status_msg.edit(" ❌ Failed to extract media from message.")

        media_b64 = base64.b64encode(media_data).decode("utf-8")
        success = await client.group.update_profile_pic(message.chat_id, media_b64)

        if success:
            await status_msg.edit(" ✅ Group picture updated successfully!")
        else:
            await status_msg.edit(" ❌ Group picture update returned false.")
    except Exception as e:
        await status_msg.edit(f" ❌ Failed to update group PFP: {str(e)}")


@astra_command(
    name="privacy",
    description="View or update your privacy settings.",
    category="Owner",
    usage="[category value] (e.g. last_seen all)",
    owner_only=True,
)
async def privacy_handler(client: Client, message: Message):
    args = extract_args(message)

    if not args:
        status_msg = await edit_or_reply(message, " 🔍 *Fetching privacy settings...*")
        try:
            settings = await client.account.get_settings()
            text = " 🛡️ **Privacy Settings**\n\n"
            for k, v in settings.items():
                text += f" • *{k.replace('_', ' ').title()}:* `{v}`\n"
            text += "\n_Use `.privacy <category> <value>` to update._\n_Categories: last_seen, profile_pic, about, status, read_receipts_"
            await status_msg.edit(text)
        except Exception as e:
            await status_msg.edit(f" ❌ Failed to fetch settings: {str(e)}")
        return

    if len(args) < 2:
        return await edit_or_reply(
            message,
            " ⚠️ Usage: `.privacy <category> <value>`\nCategories: last_seen, profile_pic, about, status, read_receipts\nValues: all, contacts, none",
        )

    category = args[0].lower()
    value = args[1].lower()

    # Map read_receipts bool
    if category == "read_receipts":
        value = value in ["true", "on", "yes", "enabled", "all"]

    status_msg = await edit_or_reply(message, f" 🔄 Updating *{category}* to *{value}*...")

    try:
        method_map = {
            "last_seen": client.account.set_last_seen,
            "profile_pic": client.account.set_profile_pic,
            "about": client.account.set_about,
            "status": client.account.set_status,
            "read_receipts": client.account.set_read_receipts,
        }

        if category not in method_map:
            return await status_msg.edit(f" ❌ Invalid category: {category}")

        await method_map[category](value)
        await status_msg.edit(f" ✅ Privacy setting *{category}* updated to *{value}*!")
    except Exception as e:
        await status_msg.edit(f" ❌ Privacy update failed: {str(e)}")
