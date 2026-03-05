import base64
import io

from PIL import Image, ImageFilter, ImageOps, ImageEnhance
from utils.bridge_downloader import bridge_downloader
from utils.plugin_utils import extract_args

from . import *
from utils.helpers import edit_or_reply


async def apply_filter(client: Client, message: Message, filter_type: str):
    """Generic image filter applier."""
    # Check if the message itself or a quoted message is an image
    is_image = message.type == MessageType.IMAGE
    has_quoted_image = message.has_quoted_msg and message.quoted_type == MessageType.IMAGE
    if not is_image and not has_quoted_image:
        return await edit_or_reply(
            message, "🖼️ **Image Tools**\n━━━━━━━━━━━━━━━━━━━━\n❌ **Reply to an image** to apply this filter."
        )

    args = extract_args(message)
    intensity = 50
    if args:
        try:
            intensity = max(1, min(100, int(args[0])))
        except ValueError:
            pass

    status_txt = f"🎨 **Astra Creative Studio**\n━━━━━━━━━━━━━━━━━━━━\n✨ *Applying {filter_type}"
    if filter_type in ("blur", "boxblur", "brightness", "contrast", "sharpen", "pixelate", "deepfry", "glitch"):
        status_txt += f" ({intensity}% intensity)"
    status_txt += "...*"
    status_msg = await edit_or_reply(message, status_txt)

    # Download media via bridge (handles quoted resolution internally)
    media_data = await bridge_downloader.download_media(client, message)
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
        radius = max(0.1, (intensity / 100) * 30)
        img = img.filter(ImageFilter.GaussianBlur(radius))
    elif filter_type == "boxblur":
        radius = max(0.1, (intensity / 100) * 30)
        img = img.filter(ImageFilter.BoxBlur(radius))
    elif filter_type == "brightness":
        factor = intensity / 50.0
        img = ImageEnhance.Brightness(img).enhance(factor)
    elif filter_type == "contrast":
        factor = intensity / 50.0
        img = ImageEnhance.Contrast(img).enhance(factor)
    elif filter_type == "sharpen":
        percent = intensity * 2
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=percent, threshold=3))
    elif filter_type == "emboss":
        img = img.filter(ImageFilter.EMBOSS)
    elif filter_type == "edges":
        img = img.filter(ImageFilter.FIND_EDGES)
    elif filter_type == "sketch":
        img = img.convert("L").filter(ImageFilter.FIND_EDGES)
        img = ImageOps.invert(img)
    elif filter_type == "pixelate":
        pixel_size = max(2, int((intensity / 100) * 50))
        img = img.resize((img.size[0] // pixel_size, img.size[1] // pixel_size), resample=Image.NEAREST)
        img = img.resize((img.size[0] * pixel_size, img.size[1] * pixel_size), resample=Image.NEAREST)
    elif filter_type == "palette":
        # Extract dominant colors and build a swatch image
        import colorgram
        from PIL import ImageDraw, ImageFont
        colors = colorgram.extract(img, 6) # extract top 6 colors
        
        # Create a new image for the palette
        palette_width = 600
        palette_height = 200
        img = Image.new('RGB', (palette_width, palette_height), color='white')
        d = ImageDraw.Draw(img)
        
        swatch_width = palette_width // len(colors)
        for i, color in enumerate(colors):
            x1 = i * swatch_width
            x2 = (i + 1) * swatch_width
            rgb = color.rgb
            d.rectangle([x1, 0, x2, palette_height - 50], fill=(rgb.r, rgb.g, rgb.b))
            
            # Label hex code below
            hex_code = f"#{rgb.r:02x}{rgb.g:02x}{rgb.b:02x}"
            # Quick text positioning hack
            d.text((x1 + 10, palette_height - 35), hex_code, fill='black')
    elif filter_type == "glitch":
        # Chromatic Aberration (RGB shift)
        img = img.convert("RGB")
        r, g, b = img.split()
        offset = int((intensity / 100) * 20)
        r = r.transform(r.size, Image.AFFINE, (1, 0, offset, 0, 1, 0))
        b = b.transform(b.size, Image.AFFINE, (1, 0, -offset, 0, 1, 0))
        img = Image.merge("RGB", (r, g, b))
    elif filter_type == "deepfry":
        # Intense meme distortion
        img = img.convert("RGB")
        factor = 1.5 + (intensity / 50.0) # Contrast boost
        img = ImageEnhance.Contrast(img).enhance(factor * 1.5)
        img = ImageEnhance.Color(img).enhance(factor * 2.0)
        img = ImageEnhance.Sharpness(img).enhance(factor * 3.0)
        # Add noise
        import random
        pixels = img.load()
        width, height = img.size
        noise_level = int((intensity / 100) * 50)
        for i in range(width):
            for j in range(height):
                if random.randint(0, 100) < noise_level:
                    r, g, b = pixels[i, j]
                    pixels[i, j] = (min(255, r + 50), max(0, g - 20), max(0, b - 20))
    elif filter_type == "ascii":
        # Convert image to ASCII art and draw it back onto an image
        from PIL import ImageDraw, ImageFont
        img = img.convert("L")
        width, height = img.size
        aspect_ratio = height / width
        new_width = 100
        new_height = int(new_width * aspect_ratio * 0.55)
        img = img.resize((new_width, new_height))
        pixels = img.getdata()
        chars = ["@", "#", "S", "%", "?", "*", "+", ";", ":", ",", "."]
        ascii_str = ""
        for pixel_value in pixels:
            ascii_str += chars[pixel_value // 25]
        
        ascii_str_lines = [ascii_str[index:index + new_width] for index in range(0, len(ascii_str), new_width)]
        ascii_img_height = len(ascii_str_lines) * 15
        ascii_img_width = new_width * 8
        ascii_img = Image.new("RGB", (ascii_img_width, ascii_img_height), color=(0, 0, 0))
        d = ImageDraw.Draw(ascii_img)
        y_text = 0
        for line in ascii_str_lines:
            d.text((0, y_text), line, fill=(0, 255, 0))
            y_text += 15
        img = ascii_img

    # Save to buffer
    out_buffer = io.BytesIO()
    img.save(out_buffer, format="JPEG", quality=90)
    b64_data = base64.b64encode(out_buffer.getvalue()).decode("utf-8")

    media = {"mimetype": "image/jpeg", "data": b64_data, "filename": f"{filter_type}.jpg"}
    await client.send_media(message.chat_id, media, caption=f"🎨 **Filter Applied:** `{filter_type}`")
    await status_msg.delete()


@astra_command(name="grey", description="Apply grayscale filter.", category="Tools & Utilities", is_public=True)
async def grey_handler(client: Client, message: Message):
    await apply_filter(client, message, "grey")


@astra_command(name="sepia", description="Apply sepia filter.", category="Tools & Utilities", is_public=True)
async def sepia_handler(client: Client, message: Message):
    await apply_filter(client, message, "sepia")


@astra_command(name="invert", description="Invert image colors.", category="Tools & Utilities", is_public=True)
async def invert_handler(client: Client, message: Message):
    await apply_filter(client, message, "invert")


@astra_command(
    name="mirror", description="Mirror the image horizontally.", category="Tools & Utilities", is_public=True
)
async def mirror_handler(client: Client, message: Message):
    await apply_filter(client, message, "mirror")


@astra_command(name="blur", description="Apply gaussian blur filter. Usage: .blur [1-100]", category="Tools & Utilities", is_public=True)
async def blur_handler(client: Client, message: Message):
    await apply_filter(client, message, "blur")


@astra_command(name="boxblur", description="Apply box blur filter. Usage: .boxblur [1-100]", category="Tools & Utilities", is_public=True)
async def boxblur_handler(client: Client, message: Message):
    await apply_filter(client, message, "boxblur")


@astra_command(name="brightness", description="Adjust brightness. Usage: .brightness [1-100]", category="Tools & Utilities", is_public=True)
async def brightness_handler(client: Client, message: Message):
    await apply_filter(client, message, "brightness")


@astra_command(name="contrast", description="Adjust contrast. Usage: .contrast [1-100]", category="Tools & Utilities", is_public=True)
async def contrast_handler(client: Client, message: Message):
    await apply_filter(client, message, "contrast")


@astra_command(name="sharpen", description="Sharpen image. Usage: .sharpen [1-100]", category="Tools & Utilities", is_public=True)
async def sharpen_handler(client: Client, message: Message):
    await apply_filter(client, message, "sharpen")


@astra_command(name="emboss", description="Apply emboss filter.", category="Tools & Utilities", is_public=True)
async def emboss_handler(client: Client, message: Message):
    await apply_filter(client, message, "emboss")


@astra_command(name="edges", description="Find edges in image.", category="Tools & Utilities", is_public=True)
async def edges_handler(client: Client, message: Message):
    await apply_filter(client, message, "edges")


@astra_command(name="sketch", description="Convert image to pencil sketch.", category="Tools & Utilities", is_public=True)
async def sketch_handler(client: Client, message: Message):
    await apply_filter(client, message, "sketch")


@astra_command(name="pixelate", description="Pixelate image. Usage: .pixelate [1-100]", category="Tools & Utilities", is_public=True)
async def pixelate_handler(client: Client, message: Message):
    await apply_filter(client, message, "pixelate")


@astra_command(name="deepfry", description="Deepfry an image (meme style). Usage: .deepfry [1-100]", category="Tools & Utilities", is_public=True)
async def deepfry_handler(client: Client, message: Message):
    await apply_filter(client, message, "deepfry")


@astra_command(name="ascii", description="Convert image to ASCII art.", category="Tools & Utilities", is_public=True)
async def ascii_handler(client: Client, message: Message):
    await apply_filter(client, message, "ascii")

@astra_command(name="glitch", description="Apply glitch effect to image. Usage: .glitch [1-100]", category="Tools & Utilities", is_public=True)
async def glitch_handler(client: Client, message: Message):
    await apply_filter(client, message, "glitch")

@astra_command(name="palette", description="Extract dominant color palette from image.", category="Tools & Utilities", is_public=True)
async def palette_handler(client: Client, message: Message):
    await apply_filter(client, message, "palette")


