from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="pinterest",
    description="Download Pinterest media",
    category="Media & Downloads",
    aliases=["pin"],
    usage="<url> (Pinterest media link)",
    owner_only=False,
)
async def pinterest_handler(client: Client, message: Message):
    """Download Pinterest media with optimized MediaChannel"""
    args_list = extract_args(message)
    if not args_list:
        return await edit_or_reply(message, " ❌ Please provide a Pinterest URL.")

    url = args_list[0]
    status_msg = await edit_or_reply(message, " 🔍 *Initializing Pinterest Engine...*")

    # Use MediaChannel for a "real-time" experience
    from utils.media_channel import MediaChannel

    channel = MediaChannel(client, message, status_msg)

    # 1. Download
    file_path, metadata = await channel.run_bridge(url, "video")

    # 2. Upload
    await channel.upload_file(file_path, metadata, "video")
