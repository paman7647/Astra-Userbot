import os
import asyncio
import time

from utils.bridge_downloader import bridge_downloader
from utils.plugin_utils import extract_args
from . import *
from utils.helpers import edit_or_reply

@astra_command(name="todoc", description="Convert an image or video to a document file.", category="Tools & Utilities", aliases=["todocument"])
async def todoc_handler(client: Client, message: Message):
    """Downloads replied media and uploads it as a document."""
    if not message.has_quoted_msg or message.quoted_type not in (MessageType.IMAGE, MessageType.VIDEO):
        return await edit_or_reply(message, "📄 **Converter**\n━━━━━━━━━━━━━━━━━━━━\n❌ **Reply to an image or video** to convert it to a document.")

    status_msg = await edit_or_reply(message, "📄 **Astra Converter**\n━━━━━━━━━━━━━━━━━━━━\n✨ *Converting to document format...*")

    try:
        ext = "mp4" if message.quoted_type == MessageType.VIDEO else "jpg"
        temp_file = f"/tmp/astra_doc_conv_{int(time.time())}.{ext}"
        
        media_path = await message.quoted.download(temp_file)
        if not media_path:
            return await status_msg.edit("❌ Failed to download original media.")

        mimetype = "video/mp4" if ext == "mp4" else "image/jpeg"
        
        # In whatsapp-web.js / Astra, setting sendMediaAsDocument in options triggers document upload
        await client.send_file(
            message.chat_id, 
            temp_file, 
            caption="📄 *Converted to Document*",
            document=True
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"❌ Conversion failed: {str(e)}")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

@astra_command(name="toimg", description="Convert a document (if it's an image) to an inline image.", category="Tools & Utilities", aliases=["toimage"])
async def toimg_handler(client: Client, message: Message):
    """Downloads replied document and uploads it as an inline image."""
    if not message.has_quoted_msg or message.quoted_type != MessageType.DOCUMENT:
        return await edit_or_reply(message, "🖼️ **Converter**\n━━━━━━━━━━━━━━━━━━━━\n❌ **Reply to a document** to convert it to an image.")

    status_msg = await edit_or_reply(message, "🖼️ **Astra Converter**\n━━━━━━━━━━━━━━━━━━━━\n✨ *Processing document as image...*")

    try:
        # Standard file path handling
        temp_file = f"/tmp/astra_img_conv_{int(time.time())}.jpg"
        
        media_path = await message.quoted.download(temp_file)
        if not media_path:
            return await status_msg.edit("❌ Failed to download document.")

        # Ensure we send it explicitly without the document flag
        await client.send_image(
            message.chat_id, 
            temp_file, 
            caption="🖼️ *Converted to Image*"
        )
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"❌ Conversion failed: {str(e)}")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

@astra_command(name="pdf2img", description="Extract images from a PDF document.", category="Tools & Utilities", aliases=["pdftoimage"])
async def pdf2img_handler(client: Client, message: Message):
    """Downloads replied PDF document and extracts all pages as images."""
    if not message.has_quoted_msg or message.quoted_type != MessageType.DOCUMENT:
        return await edit_or_reply(message, "📄 **Converter**\n━━━━━━━━━━━━━━━━━━━━\n❌ **Reply to a PDF document** to extract images.")

    status_msg = await edit_or_reply(message, "📄 **Astra Converter**\n━━━━━━━━━━━━━━━━━━━━\n✨ *Extracting images from PDF... This might take a while.*")

    temp_pdf = f"/tmp/astra_pdf_in_{int(time.time())}.pdf"
    
    try:
        media_path = await message.quoted.download(temp_pdf)
        if not media_path:
            return await status_msg.edit("❌ Failed to download PDF document.")

        import fitz  # PyMuPDF
        
        doc = fitz.open(temp_pdf)
        num_pages = len(doc)
        
        if num_pages == 0:
            return await status_msg.edit("❌ The PDF appears to be empty.")
            
        await status_msg.edit(f"📄 **Astra Converter**\n━━━━━━━━━━━━━━━━━━━━\n✨ *Extracting {num_pages} page(s) from PDF...*")
        
        # Determine DPI, usually 150-300 is good, keeping it moderate to save time/bandwidth
        zoom_x = 2.0  # horizontal zoom
        zoom_y = 2.0  # vertical zoom
        mat = fitz.Matrix(zoom_x, zoom_y)

        # Batch send pages
        for page_num in range(num_pages):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=mat)
            
            temp_img = f"/tmp/astra_pdf_out_{int(time.time())}_page_{page_num+1}.jpg"
            pix.save(temp_img)
            
            await client.send_image(
                message.chat_id, 
                temp_img, 
                caption=f"📄 *Page {page_num + 1} of {num_pages}*"
            )
            
            if os.path.exists(temp_img):
                os.remove(temp_img)
                
            # Prevent rate limiting on large PDFs
            if page_num < num_pages - 1:
                await asyncio.sleep(0.5)

        doc.close()
        await status_msg.delete()

    except ImportError:
        await status_msg.edit("❌ PyMuPDF (`fitz`) is not installed. Run `pip install PyMuPDF`.")
    except Exception as e:
        await status_msg.edit(f"❌ Extraction failed: {str(e)}")
    finally:
        if os.path.exists(temp_pdf):
            os.remove(temp_pdf)
