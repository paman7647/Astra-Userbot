from utils.media_channel import MediaChannel

from . import *


@astra_command(
    name="facebook",
    description="Download Facebook video",
    category="Media & Downloads",
    aliases=["fb"],
    usage="<url> (Facebook video link)",
    owner_only=False,
)
async def facebook_handler(client: Client, message: Message):
    """Download Facebook video with optimized MediaChannel"""
    args_list = extract_args(message)
    if not args_list:
        return await edit_or_reply(message, " ❌ Please provide a Facebook URL.")

    url = args_list[0]
    status_msg = await edit_or_reply(message, " 🔍 *Initializing Facebook Engine...*")

    channel = MediaChannel(client, message, status_msg)
    file_path, metadata = await channel.run_bridge(url, "video")
    await channel.upload_file(file_path, metadata, "video")
