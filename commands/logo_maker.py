import base64
import io
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from . import *

# Configuration
LOGOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utils", "logos")
os.makedirs(LOGOS_DIR, exist_ok=True)


@astra_command(
    name="logo",
    description="Create a beautiful logo with local professional backgrounds.",
    category="Creative Suite",
    usage="<text>",
    is_public=True,
)
async def logo_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, " Usage: `.logo MyName`")

    text = " ".join(args)
    status_msg = await edit_or_reply(message, " Processing...")

    # 1. Pick a random local background (Prefer manually added bg1, bg2, etc.)
    bg_files = [f for f in os.listdir(LOGOS_DIR) if f.startswith("bg") and f.endswith((".jpg", ".jpeg", ".png"))]
    if not bg_files:
        bg_files = [f for f in os.listdir(LOGOS_DIR) if f.endswith((".jpg", ".jpeg", ".png"))]

    if not bg_files:
        # Fallback to local color if no images found
        img = Image.new("RGB", (1024, 1024), color=(15, 12, 25))
    else:
        bg_path = os.path.join(LOGOS_DIR, random.choice(bg_files))
        img = Image.open(bg_path)
        img = img.resize((1024, 1024), Image.LANCZOS)

    # 2. Process Image (Blur & Darken for premium text readability)
    img = img.filter(ImageFilter.GaussianBlur(radius=2))
    # Semi-transparent dark overlay for high contrast
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 130))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    # 3. Draw Text
    draw = ImageDraw.Draw(img)

    # Stylized Font Selection: Pick a random font from font1.ttf to font5.ttf
    available_fonts = [f for f in os.listdir(LOGOS_DIR) if f.startswith("font") and f.endswith(".ttf")]
    if not available_fonts:
        # Fallback to system fonts if no local fonts found
        font_paths = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "arial.ttf",
        ]
    else:
        font_paths = [os.path.join(LOGOS_DIR, f) for f in available_fonts]
        random.shuffle(font_paths)  # Randomized style each time

    font = None
    for p in font_paths:
        try:
            # Increased font size for a more premium, high-impact look
            font = ImageFont.truetype(p, 180)
            break
        except:
            continue

    if not font:
        font = ImageFont.load_default()

    # Center text
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((1024 - w) / 2, (1024 - h) / 2), text, font=font, fill=(255, 255, 255))

    # 4. Save & Send
    out_buffer = io.BytesIO()
    img.save(out_buffer, format="JPEG", quality=90)
    b64_data = base64.b64encode(out_buffer.getvalue()).decode("utf-8")

    media = {"mimetype": "image/jpeg", "data": b64_data, "filename": "logo.jpg"}
    await client.send_media(message.chat_id, media, caption=f"🏷️ **Custom Logo for:** `{text}`")
    await status_msg.delete()
