from utils.plugin_utils import extract_args
from . import *
from utils.helpers import edit_or_reply

FONTS = {
    'fancy1': str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶 individual_z𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ"),
    'fancy2': str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"),
    'fancy3': str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", "𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ"),
    'fancy4': str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"),
    'flip': str.maketrans("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ", "ɐqɔpǝɟƃɥıظʞןɯuodbɹsʇnʌʍxʎz∀ꓭƆᗡƎℲꓨHIſꞰꓶWNOԀꓤꓤSꓕ∩ΛMX⅄Z")
}

@astra_command(
    name="fancy", 
    description="Convert text to fancy font styles. Usage: .fancy [text] or reply to text.", 
    category="Tools & Utilities", 
    is_public=True
)
async def fancy_handler(client: Client, message: Message):
    args = extract_args(message)
    text = ""
    
    if args:
        text = " ".join(args)
    elif message.has_quoted_msg and hasattr(message.quoted, 'body'):
        text = message.quoted.body
        
    if not text:
        return await edit_or_reply(message, "📝 **Fancy Text**\n━━━━━━━━━━━━━━━━━━━━\n❌ By Astra: Provide text or reply to a message.")

    result = f"✨ **Astra Fancy Text** ✨\n\n"
    result += f"**Gothic:** {text.translate(FONTS['fancy1'])}\n\n"
    result += f"**Bold Sans:** {text.translate(FONTS['fancy2'])}\n\n"
    result += f"**Outline:** {text.translate(FONTS['fancy3'])}\n\n"
    result += f"**Fullwidth:** {text.translate(FONTS['fancy4'])}\n\n"
    result += f"**Upside Down:** {text.translate(FONTS['flip'])[::-1]}"
    
    await edit_or_reply(message, result)

@astra_command(
    name="monospaced", 
    description="Format text as code block.", 
    category="Tools & Utilities", 
    is_public=True
)
async def monospaced_handler(client: Client, message: Message):
    args = extract_args(message)
    text = ""
    if args:
        text = " ".join(args)
    if not text and message.has_quoted_msg and hasattr(message.quoted, 'body'):
        text = message.quoted.body
        
    if not text:
        return await edit_or_reply(message, "Provide text or reply to a message.")
        
    await edit_or_reply(message, f"```\n{text}\n```")
