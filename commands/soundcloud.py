from utils.media_channel import MediaChannel

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="soundcloud",
    description="Download SoundCloud track",
    category="Media & Downloads",
    aliases=["sc"],
    usage="<url> (SoundCloud track link)",
    owner_only=False,
)
async def soundcloud_handler(client: Client, message: Message):
    """Download SoundCloud track with optimized MediaChannel"""
    args_list = extract_args(message)
    if not args_list:
        return await edit_or_reply(message, " ❌ Please provide a SoundCloud URL.")

    url = args_list[0]
    status_msg = await edit_or_reply(message, " 🔍 *Initializing SoundCloud Engine...*")

    channel = MediaChannel(client, message, status_msg)
    # SoundCloud is audio
    file_path, metadata = await channel.run_bridge(url, "audio")
    await channel.upload_file(file_path, metadata, "audio")
