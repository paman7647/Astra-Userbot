# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

from . import *

@astra_command(
    name="notes",
    description="Manage your notes/snippets.",
    category="Utility",
    aliases=["note", "save", "get"],
    usage="save <keyword> <content> | get <keyword> | del <keyword> | list (ex: save note1 hello)",
    owner_only=True
)
async def notes_handler(client: Client, message: Message):
    """Manage your notes/snippets."""
    try:
        args_list = extract_args(message)
        
        if not args_list:
            usage = "save <keyword> <content> | get <keyword> | del <keyword> | list"
            return await smart_reply(message, f" *Usage:* `.notes {usage}`")
    
        from utils.state import state
        action = args_list[0].lower()
    
        if action in ["save", "add"]:
            if len(args_list) < 3: return await smart_reply(message, " *Usage:* `.save <keyword> <content>`")
            keyword = args_list[1].lower().replace('#', '')
            content = " ".join(args_list[2:])
            state.set_note(keyword, content)
            await smart_reply(message, f" ✅ Note `{keyword}` saved! Access via `#keyword` or `get {keyword}`.")
        
        elif action == "get":
            if len(args_list) < 2: return await smart_reply(message, " Specify a keyword.")
            keyword = args_list[1].lower().replace('#', '')
            content = state.get_note(keyword)
            if content: await smart_reply(message, content)
            else: await smart_reply(message, " ❌ Note not found.")
        
        elif action in ["del", "rem"]:
            if len(args_list) < 2: return await smart_reply(message, " Specify a keyword to delete.")
            keyword = args_list[1].lower().replace('#', '')
            state.delete_note(keyword)
            await smart_reply(message, f" 🗑️ Note `{keyword}` deleted.")
        
        elif action == "list":
            notes = state.state.get("notes", {})
            if not notes: return await smart_reply(message, " You have no saved notes.")
            txt = " 📝 *Your Notes:*\n\n" + "\n".join([f"• #{k}" for k in notes.keys()])
            await smart_reply(message, txt)
        else:
            await smart_reply(message, " Unknown action. Use: save, get, del, list")
    
    except Exception as e:
        await smart_reply(message, f" ❌ Error: {str(e)}")
        await report_error(client, e, context='Command notes failed')

# Corrected filter usage: Using functional default
def is_hashtag(event):
    body = getattr(event, 'body', '')
    return body and body.startswith("#")

@Client.on_message(Filters.create(is_hashtag))
async def note_trigger_handler(client: Client, message: Message):
    """Trigger note content using #keyword."""
    try:
        # Re-check just in case
        if message.body and message.body.startswith("#"):
            keyword = message.body[1:].split()[0].lower()
            from utils.state import state
            content = state.get_note(keyword)
            if content:
                await smart_reply(message, content)
    except Exception:
        pass
