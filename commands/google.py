from utils.search import perform_search

from . import *


@astra_command(
    name="google",
    description="Search the web with Google.",
    category="Tools & Utilities",
    aliases=["gs", "search"],
    usage="<query> (e.g. .google Astra Userbot)",
    is_public=True,
)
async def google_handler(client: Client, message: Message):
    """Google search plugin."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "❌ **Usage:** `.google <query>`")

    query = " ".join(args)
    status_msg = await edit_or_reply(message, f"🔍 Searching Google for `{query}`...")

    data = await perform_search(query, engines=["google"])

    if not data or not data.get("results"):
        return await status_msg.edit(f"❌ No results found for `{query}`.")

    results = data.get("results", [])[:5]
    text = (
        f"🌐 **GOOGLE SEARCH RESULTS**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 **Query:** `{query}`\n"
        f"📡 **Source:** `{data.get('instance', 'Astra Engine')}`\n\n"
    )

    # Show answer/infobox if available
    answer = data.get("answers", []) or data.get("infoboxes", [])
    if answer:
        ans_text = answer[0].get("answer") or answer[0].get("content", "")
        if ans_text:
            text += f"📝 **Note:** {ans_text}\n\n"

    for i, res in enumerate(results, 1):
        title = res.get("title", "No Title")
        link = res.get("url", res.get("link", "#"))
        snippet = res.get("content", res.get("snippet", ""))[:150]
        if snippet:
            text += f"{i}. **[{title}]({link})**\n_{snippet}_\n\n"
        else:
            text += f"{i}. **[{title}]({link})**\n\n"

    text += "━━━━━━━━━━━━━━━━━━━━"
    await status_msg.edit(text)
