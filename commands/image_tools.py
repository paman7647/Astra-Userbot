# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

from . import *
from PIL import Image, ImageOps, ImageFilter
import io
import base64
from utils.bridge_downloader import bridge_downloader
from utils.helpers import handle_command_error

async def apply_filter(client: Client, message: Message, filter_type: str):
    """Generic image filter applier."""
    target = message.quoted if message.has_quoted_msg else message
    if not target or not target.is_media or target.type != MessageType.IMAGE:
        return await smart_reply(message, "🖼️ **Image Tools**\n━━━━━━━━━━━━━━━━━━━━\n❌ **Reply to an image** to apply this filter.")

    status_msg = await smart_reply(message, f"🎨 **Astra Creative Studio**\n━━━━━━━━━━━━━━━━━━━━\n✨ *Applying {filter_type} filter...*")

    try:
        # Download (Pass the target message which actually has the media)
        media_data = await bridge_downloader.download_media(client, target)
        if not media_data:
            return await status_msg.edit("❌ Failed to download image.")

        # Process with PIL
        img = Image.open(io.BytesIO(media_data))
        
        if filter_type == "grey":
            img = ImageOps.grayscale(img)
        elif filter_type == "sepia":
            # Sepia transformation
            width, height = img.size
            pixels = img.load()
            for py in range(height):
                for px in range(width):
                    r, g, b = img.getpixel((px, py))
                    tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                    tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                    tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                    pixels[px, py] = (min(tr, 255), min(tg, 255), min(tb, 255))
        elif filter_type == "invert":
            img = ImageOps.invert(img.convert("RGB"))
        elif filter_type == "mirror":
            img = ImageOps.mirror(img)
        elif filter_type == "blur":
            img = img.filter(ImageFilter.BLUR)

        # Save to buffer
        out_buffer = io.BytesIO()
        img.save(out_buffer, format="JPEG", quality=90)
        b64_data = base64.b64encode(out_buffer.getvalue()).decode('utf-8')

        media = {
            "mimetype": "image/jpeg",
            "data": b64_data,
            "filename": f"{filter_type}.jpg"
        }
        await client.send_media(message.chat_id, media, caption=f"🎨 **Filter Applied:** `{filter_type}`")
        await status_msg.delete()

    except Exception as e:
        await handle_command_error(client, message, e, context=f'Image filter ({filter_type}) failure')

@astra_command(name="grey", description="Apply grayscale filter.", category="Tools & Utilities", is_public=True)
async def grey_handler(client: Client, message: Message):
    await apply_filter(client, message, "grey")

@astra_command(name="sepia", description="Apply sepia filter.", category="Tools & Utilities", is_public=True)
async def sepia_handler(client: Client, message: Message):
    await apply_filter(client, message, "sepia")

@astra_command(name="invert", description="Invert image colors.", category="Tools & Utilities", is_public=True)
async def invert_handler(client: Client, message: Message):
    await apply_filter(client, message, "invert")

@astra_command(name="mirror", description="Mirror the image horizontally.", category="Tools & Utilities", is_public=True)
async def mirror_handler(client: Client, message: Message):
    await apply_filter(client, message, "mirror")

@astra_command(name="blur", description="Apply blur filter.", category="Tools & Utilities", is_public=True)
async def blur_handler(client: Client, message: Message):
    await apply_filter(client, message, "blur")
