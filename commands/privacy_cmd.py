"""Privacy settings commands using the new Astra v3 API."""

from . import *


@astra_command(
    name="privacy",
    description="View or change privacy settings.",
    category="Account",
    aliases=["priv"],
    usage="<category> <value>\nCategories: last_seen, profile_pic, about, status, read_receipts\nValues: all, contacts, none",
    owner_only=True,
)
async def privacy_handler(client: Client, message: Message):
    """View or update WhatsApp privacy settings."""
    args = extract_args(message)

    # No args: show current privacy settings
    if not args:
        status = await edit_or_reply(message, "Fetching privacy settings...")
        try:
            settings = await client.api.get_privacy_settings()
            if not settings:
                return await status.edit("Could not fetch privacy settings.")

            text = "**Privacy Settings:**\n\n"
            labels = {
                "last_seen": "Last seen",
                "profile_pic": "Profile picture",
                "about": "About",
                "status": "Status",
                "read_receipts": "Read receipts",
            }
            for key, label in labels.items():
                val = settings.get(key, "unknown")
                if isinstance(val, bool):
                    val = "on" if val else "off"
                text += f"- **{label}:** `{val}`\n"

            text += "\nUsage: `.privacy <category> <value>`"
            await status.edit(text)
        except Exception as e:
            await status.edit(f"Error: {e}")
        return

    if len(args) < 2:
        return await edit_or_reply(
            message,
            "**Usage:** `.privacy <category> <value>`\n\n"
            "**Categories:** `last_seen`, `profile_pic`, `about`, `status`, `read_receipts`\n"
            "**Values:** `all` (everyone), `contacts` (my contacts), `none` (nobody)"
        )

    category = args[0].lower()
    value = args[1].lower()

    valid_cats = ["last_seen", "profile_pic", "about", "status", "read_receipts"]
    if category not in valid_cats:
        return await edit_or_reply(message, f"Invalid category. Use: {', '.join(valid_cats)}")

    valid_vals = ["all", "contacts", "none", "nobody", "everyone"]
    if value not in valid_vals and category != "read_receipts":
        return await edit_or_reply(message, f"Invalid value. Use: all, contacts, none")

    # Normalize
    if value == "everyone":
        value = "all"
    if value == "nobody":
        value = "none"

    status = await edit_or_reply(message, f"Updating {category} to {value}...")

    try:
        result = await client.api.set_privacy(category, value)
        if result:
            await status.edit(f"Privacy updated: **{category}** → `{value}`")
        else:
            await status.edit(f"Failed to update {category}. Try again.")
    except Exception as e:
        await status.edit(f"Error: {e}")


@astra_command(
    name="setname",
    description="Change your WhatsApp display name.",
    category="Account",
    aliases=["pushname", "nick"],
    usage="<new name>",
    owner_only=True,
)
async def setname_handler(client: Client, message: Message):
    """Updates the user's WhatsApp pushname."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "Usage: `.setname <new name>`")

    name = " ".join(args)
    status = await edit_or_reply(message, f"Updating name to: {name}...")

    try:
        result = await client.api.set_profile_name(name)
        if result:
            await status.edit(f"Display name updated to: **{name}**")
        else:
            await status.edit("Failed to update name.")
    except Exception as e:
        await status.edit(f"Error: {e}")


@astra_command(
    name="setabout",
    description="Change your WhatsApp about/bio text.",
    category="Account",
    aliases=["bio", "setbio"],
    usage="<text>",
    owner_only=True,
)
async def setabout_handler(client: Client, message: Message):
    """Updates the user's about text."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "Usage: `.setabout <text>`")

    text = " ".join(args)
    status = await edit_or_reply(message, f"Updating about...")

    try:
        result = await client.api.set_about_text(text)
        if result:
            await status.edit(f"About updated: _{text}_")
        else:
            await status.edit("Failed to update about.")
    except Exception as e:
        await status.edit(f"Error: {e}")


@astra_command(
    name="setpfp",
    description="Set your profile picture (reply to image).",
    category="Account",
    aliases=["setdp", "setavatar"],
    usage="(reply to an image)",
    owner_only=True,
)
async def setpfp_handler(client: Client, message: Message):
    """Updates the user's profile picture."""
    if not message.has_quoted_msg or not message.quoted:
        return await edit_or_reply(message, "Reply to an image to set it as your profile picture.")

    status = await edit_or_reply(message, "Updating profile picture...")

    try:
        media_path = await client.download_media(message.quoted)
        if not media_path:
            return await status.edit("Failed to download the image.")

        import base64
        with open(media_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()

        result = await client.api.update_profile_pic(data)
        if result:
            await status.edit("Profile picture updated.")
        else:
            await status.edit("Failed to update profile picture.")

        import os
        if os.path.exists(media_path):
            os.remove(media_path)
    except Exception as e:
        await status.edit(f"Error: {e}")
