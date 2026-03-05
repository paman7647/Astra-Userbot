from . import *


@astra_command(
    name="song",
    description="Search and download audio from YouTube.",
    category="Media & Downloads",
    aliases=["music"],
    usage="<song name>",
    is_public=True,
)
async def song_handler(client: Client, message: Message):
    """Song downloader (audio only)."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "❌ **Usage:** `.song <song name>`")

    query = " ".join(args)
    is_url = query.startswith("http://") or query.startswith("https://")

    # Refine search query if it's not a direct link
    if not is_url:
        if "song" not in query.lower() and "audio" not in query.lower():
            query += " audio song"

    status_msg = await edit_or_reply(
        message, f"⚡ **Astra Media Tracking**\n━━━━━━━━━━━━━━━━━━━━\n🎵 **Query:** `{query}`..."
    )

    import yt_dlp

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "force_generic_extractor": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if is_url:
            result = ydl.extract_info(query, download=False)
            res = result["entries"][0] if "entries" in result else result
        else:
            # Search YouTube for the best match
            result = ydl.extract_info(f"ytsearch1:{query}", download=False)
            results = result.get("entries", [])
            if not results:
                return await status_msg.edit(f"❌ No song found for `{query}`.")
            res = results[0]

    target_url = res.get("webpage_url") or f"https://www.youtube.com/watch?v={res.get('id')}"
    title = res.get("title", "Unknown")
    duration = res.get("duration_string") or (
        f"{int(res['duration']) // 60}:{int(res['duration']) % 60:02d}" if res.get("duration") else "N/A"
    )

    await status_msg.edit(
        f"⚡ **Astra Media Tracking**\n━━━━━━━━━━━━━━━━━━━━\n✅ **Found:** `{title}`\n⏱️ **Duration:** `{duration}`\n\n📥 *Routing to Gateway...*"
    )

    # Use MediaChannel for download/upload
    from utils.media_channel import MediaChannel

    channel = MediaChannel(client, message, status_msg)
    file_path, metadata = await channel.run_bridge(target_url, "audio")
    await channel.upload_file(file_path, metadata, "audio")
    return


@astra_command(
    name="vsong",
    description="Search and download video from YouTube.",
    category="Media & Downloads",
    aliases=["video"],
    usage="<video name>",
    is_public=True,
)
async def vsong_handler(client: Client, message: Message):
    """Vsong downloader (video only)."""
    # ... extraction logic similar to song_handler ...
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "❌ **Usage:** `.vsong <video name>`")

    query = " ".join(args)
    is_url = query.startswith("http://") or query.startswith("https://")

    # Refine search query if it's not a direct link
    if not is_url:
        if "video" not in query.lower():
            query += " full video"

    status_msg = await edit_or_reply(
        message, f"⚡ **Astra Media Tracking**\n━━━━━━━━━━━━━━━━━━━━\n🎬 **Query:** `{query}`..."
    )

    import yt_dlp

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "force_generic_extractor": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        if is_url:
            result = ydl.extract_info(query, download=False)
            res = result["entries"][0] if "entries" in result else result
        else:
            # Search YouTube for the best match
            result = ydl.extract_info(f"ytsearch1:{query}", download=False)
            results = result.get("entries", [])
            if not results:
                return await status_msg.edit(f"❌ No video found for `{query}`.")
            res = results[0]

    target_url = res.get("webpage_url") or f"https://www.youtube.com/watch?v={res.get('id')}"
    title = res.get("title", "Unknown")
    duration = res.get("duration_string") or (
        f"{int(res['duration']) // 60}:{int(res['duration']) % 60:02d}" if res.get("duration") else "N/A"
    )

    await status_msg.edit(
        f"⚡ **Astra Media Tracking**\n━━━━━━━━━━━━━━━━━━━━\n✅ **Found:** `{title}`\n⏱️ **Duration:** `{duration}`\n\n📥 *Routing to Gateway...*"
    )

    # Use MediaChannel for download/upload
    from utils.media_channel import MediaChannel

    channel = MediaChannel(client, message, status_msg)
    file_path, metadata = await channel.run_bridge(target_url, "video")
    await channel.upload_file(file_path, metadata, "video")
    return
