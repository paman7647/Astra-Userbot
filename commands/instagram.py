from . import *


@astra_command(
    name="instagram",
    description="Download Instagram post/reel/story",
    category="Media & Downloads",
    aliases=["ig", "reel", "story"],
    usage="<url> (Instagram link)",
    owner_only=False,
)
async def instagram_handler(client: Client, message: Message):
    """Download Instagram media with optimized MediaChannel"""
    args_list = extract_args(message)
    if not args_list:
        return await edit_or_reply(message, " ❌ Please provide an Instagram URL.")

    url = args_list[0]
    # Handle username-only input for stories? No, that's for .igstory.
    # But we can detect if it's a story URL.

    args_lower = [arg.lower() for arg in args_list]
    mode = "audio" if "audio" in args_lower or "mp3" in args_lower else "video"

    status_msg = await edit_or_reply(message, " 🔍 *Initializing Instagram Engine...*")

    # Use MediaChannel for a "real-time" experience
    from utils.media_channel import MediaChannel

    channel = MediaChannel(client, message, status_msg)

    # 1. Download (run_bridge handles yt-dlp which supports stories)
    file_path, metadata = await channel.run_bridge(url, mode)

    # 2. Upload
    await channel.upload_file(file_path, metadata, mode)


@astra_command(
    name="igstory",
    description="Download the latest stories from an Instagram user.",
    category="Media & Downloads",
    usage="<username>",
    is_public=True,
)
async def igstory_handler(client: Client, message: Message):
    """Downloader to fetch active stories by username."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "❌ **Usage:** `.igstory <username>`")

    username = args[0].replace("@", "")
    status_msg = await edit_or_reply(
        message, f"📥 **Astra Story Fetcher**\n━━━━━━━━━━━━━━━━━━━━\n📡 Looking for active stories of `@{username}`..."
    )

    # We construct the story URL and pass it to the standard instagram handler logic
    story_url = f"https://www.instagram.com/stories/{username}/"

    from utils.media_channel import MediaChannel

    channel = MediaChannel(client, message, status_msg)

    try:
        # We attempt to download all stories using yt-dlp's generic downloader
        # Note: Stories often require cookies for server-side downloads.
        file_path, metadata = await channel.run_bridge(story_url, "video")

        await channel.upload_file(file_path, metadata, "video")

    except Exception as e:
        if "No active stories" in str(e) or "private" in str(e).lower():
            await status_msg.edit(
                f"ℹ️ **No active public stories** found for `@{username}`.\n(They might be expired or the account is private)"
            )
        else:
            raise e
