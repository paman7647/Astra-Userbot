import os
import time
from gtts import gTTS

from utils.plugin_utils import extract_args
from . import *
from utils.helpers import edit_or_reply

@astra_command(
    name="tts", 
    description="Convert text to speech voice note. Usage: .tts [lang_code] [text] (e.g. .tts en Hello world)", 
    category="Tools & Utilities", 
    is_public=True
)
async def tts_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args and not message.has_quoted_msg:
        return await edit_or_reply(message, "🗣️ **TTS Engine**\n━━━━━━━━━━━━━━━━━━━━\n❌ **Provide text** or reply to a text message. Usage: `.tts [lang] [text]`")

    # Determine language and text
    lang = "en"
    text = ""
    
    if args:
        # Check if first arg is a valid 2-letter language code AND there's more text
        if len(args[0]) == 2 and args[0].lower() in ["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "hi", "ar"]:
            if len(args) > 1:
                lang = args[0].lower()
                text = " ".join(args[1:])
            else:
                # Only one 2-letter word provided, treat it as text in default lang
                text = args[0]
        else:
            text = " ".join(args)
            
    if not text and message.has_quoted_msg:
        if hasattr(message.quoted, 'body') and message.quoted.body:
             text = message.quoted.body
        else:
             return await edit_or_reply(message, "❌ Quoted message must contain text.")
             
    if not text:
        return await edit_or_reply(message, "❌ No text provided.")

    status_msg = await edit_or_reply(message, f"🗣️ **Astra TTS Engine**\n━━━━━━━━━━━━━━━━━━━━\n✨ *Generating voice note in '{lang}'...*")

    temp_audio = f"/tmp/astra_tts_{int(time.time())}.mp3"
    
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(temp_audio)
        
        await client.send_audio(
            message.chat_id, 
            temp_audio, 
            caption=f"🗣️ **TTS Generated:** `{lang}`",
            options={"sendAudioAsVoice": True}
        )
        await status_msg.delete()

    except ValueError:
        await status_msg.edit(f"❌ Invalid language code: `{lang}`")
    except Exception as e:
        await status_msg.edit(f"❌ TTS Generation failed: {str(e)}")
    finally:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
