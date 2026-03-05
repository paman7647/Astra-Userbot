from utils.search import perform_search

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="duckduckgo",
    description="Privacy-focused web search using DuckDuckGo.",
    category="Tools & Utilities",
    aliases=["ddg"],
    usage="<query> (e.g. .ddg Astra Bot)",
    is_public=True,
)
async def ddg_handler(client: Client, message: Message):
    """DuckDuckGo search plugin."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "❌ **Usage:** `.ddg <query>`")

    query = " ".join(args)
    status_msg = await edit_or_reply(message, f"🦆 Searching DDG for `{query}`...")

    try:
        data = await perform_search(query, engines=["duckduckgo"])

        if not data or not data.get("results"):
            return await status_msg.edit(f"❌ No results found for `{query}`.")

        results = data.get("results", [])[:5]
        text = (
            f"🦆 **DUCKDUCKGO SEARCH**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔎 **Query:** `{query}`\n"
            f"📡 **Source:** `{data.get('instance', 'Astra Engine')}`\n\n"
        )

        # Show quick info if available
        answer = data.get("answers", []) or data.get("infoboxes", [])
        if answer:
            ans_text = answer[0].get("answer") or answer[0].get("content", "")
            if ans_text:
                text += f"💡 **Info:** {ans_text}\n\n"

        for i, res in enumerate(results, 1):
            title = res.get("title", "No Title")
            link = res.get("url", res.get("link", "#"))
            snippet = res.get("content", res.get("snippet", ""))[:150]
            if snippet:
                text += f"{i}. **[{title}]({link})**\n_{snippet}_\n\n"
            else:
                text += f"{i}. **[{title}]({link})**\n\n"

        text += "━━━━━━━━━━━━━━━━━━━━"
        return await status_msg.edit(text)

    except Exception as e:
        await status_msg.edit(f"❌ **DDG Error:** {str(e)}")
