import asyncio
import os
import time

from moviepy.editor import VideoFileClip
from utils.bridge_downloader import bridge_downloader
from utils.plugin_utils import extract_args
from . import *
from utils.helpers import edit_or_reply

async def apply_video_edit(client: Client, message: Message, edit_type: str):
    is_video = message.type == MessageType.VIDEO
    has_quoted_video = message.has_quoted_msg and message.quoted_type == MessageType.VIDEO
    is_audio = message.type == MessageType.AUDIO
    has_quoted_audio = message.has_quoted_msg and message.quoted_type == MessageType.AUDIO
    
    if edit_type == "audioviz":
        if not is_audio and not has_quoted_audio:
            return await edit_or_reply(message, "🎬 **Video Tools**\n━━━━━━━━━━━━━━━━━━━━\n❌ **Reply to an audio file** to generate a visualizer.")
    else:
        if not is_video and not has_quoted_video:
            return await edit_or_reply(message, "🎬 **Video Tools**\n━━━━━━━━━━━━━━━━━━━━\n❌ **Reply to a video** to apply this effect.")

    status_msg = await edit_or_reply(message, f"🎬 **Astra Creative Studio**\n━━━━━━━━━━━━━━━━━━━━\n✨ *Applying {edit_type} effect... This might take a while.*")

    args = extract_args(message)
    factor = 1.0
    if args and edit_type == "speed":
        try:
            factor = float(args[0])
        except ValueError:
            pass

    # Download media directly to file
    target = message.quoted if (has_quoted_video or has_quoted_audio) else message
    temp_in = f"/tmp/astra_media_in_{int(time.time())}.{'mp3' if edit_type == 'audioviz' else 'mp4'}"
    temp_out = f"/tmp/astra_media_out_{int(time.time())}.{'gif' if edit_type == 'togif' else 'mp3' if edit_type == 'audio' else 'mp4'}"
    
    try:
        media_path = await target.download(temp_in)
        if not media_path:
            return await status_msg.edit("❌ Failed to download video.")

        def process_video():
            if edit_type == "audioviz":
                from moviepy.editor import AudioFileClip, ColorClip
                import math
                audio_clip = AudioFileClip(temp_in).subclip(0, min(15, AudioFileClip(temp_in).duration)) # Limit to 15s to save resources
                video = ColorClip(size=(640, 360), color=(10, 10, 30), duration=audio_clip.duration)
                video = video.set_audio(audio_clip)
                # simple 'pulse' visualizer hack without heavy array manipulation:
                def make_frame(t):
                    # just drawing a pulsing circle based on time to simulate visualizer
                    import numpy as np
                    frame = np.full((360, 640, 3), (10, 10, 30), dtype=np.uint8)
                    import cv2
                    radius = int(50 + 30 * math.sin(t * 10))
                    cv2.circle(frame, (320, 180), radius, (0, 255, 150), -1)
                    return frame
                
                from moviepy.editor import VideoClip
                final_video = VideoClip(make_frame, duration=audio_clip.duration).set_audio(audio_clip)
                final_video.write_videofile(temp_out, fps=24, codec="libx264", logger=None)
                audio_clip.close()
                return

            clip = VideoFileClip(temp_in)
            if edit_type == "togif":
                # Convert first 10 seconds to GIF
                clip = clip.subclip(0, min(10, clip.duration))
                clip = clip.resize(width=320)
                clip.write_gif(temp_out, fps=10, logger=None)
            elif edit_type == "reverse":
                from moviepy.video.fx.all import time_mirror
                clip = time_mirror(clip)
                clip.write_videofile(temp_out, codec="libx264", logger=None)
            elif edit_type == "speed":
                from moviepy.video.fx.all import speedx
                clip = speedx(clip, factor)
                clip.write_videofile(temp_out, codec="libx264", logger=None)
            elif edit_type == "audio":
                clip.audio.write_audiofile(temp_out, logger=None)
            else:
                raise ValueError("Unknown video edit type.")
            clip.close()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, process_video)

        mimetype = "image/gif" if edit_type == "togif" else "audio/mp3" if edit_type == "audio" else "video/mp4"
        await client.send_media(message.chat_id, temp_out, mimetype, caption=f"🎬 **Media Effect:** `{edit_type}`")
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"❌ Error processing video: {str(e)}")
    finally:
        if os.path.exists(temp_in):
            os.remove(temp_in)
        if os.path.exists(temp_out):
            os.remove(temp_out)

@astra_command(name="vtg", description="Convert video to GIF (max 10s).", category="Tools & Utilities", is_public=True)
async def vtg_handler(client: Client, message: Message):
    await apply_video_edit(client, message, "togif")

@astra_command(name="reversevid", description="Reverse a video.", category="Tools & Utilities", is_public=True)
async def reversevid_handler(client: Client, message: Message):
    await apply_video_edit(client, message, "reverse")

@astra_command(name="speedvid", description="Change video speed. Usage: .speedvid [factor]", category="Tools & Utilities", is_public=True)
async def speedvid_handler(client: Client, message: Message):
    await apply_video_edit(client, message, "speed")

@astra_command(name="extractaudio", description="Extract audio from a video.", category="Tools & Utilities", is_public=True)
async def extractaudio_handler(client: Client, message: Message):
    await apply_video_edit(client, message, "audio")

@astra_command(name="audioviz", description="Create an audio visualizer video from audio track.", category="Tools & Utilities", is_public=True)
async def audioviz_handler(client: Client, message: Message):
    await apply_video_edit(client, message, "audioviz")

