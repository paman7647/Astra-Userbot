import asyncio
import os
import calendar
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont

from config import config
from . import *

# Shared Constants
TZ = ZoneInfo(config.TIMEZONE)
FONT_PATH = os.path.join(config.BASE_DIR, "utils", "logos", "font1.ttf")
BG_FOLDER = os.path.join(config.BASE_DIR, "utils", "logos")

@astra_command(
    name="time",
    description="Display current time in India or major world cities.",
    category="Tools & Utilities",
    aliases=["clock", "now"],
    usage=".time [-all] [-img]"
)
async def time_handler(client: Client, message: Message):
    """Current Time Handler"""
    args = extract_args(message)
    is_all = "-all" in args
    is_img = "-img" in args
    
    now = datetime.now(TZ)
    
    if is_all:
        cities = {
            "🇮🇳 Delhi": TZ,
            "🇬🇧 London": ZoneInfo("Europe/London"),
            "🇺🇸 New York": ZoneInfo("America/New_York"),
            "🇯🇵 Tokyo": ZoneInfo("Asia/Tokyo"),
            "🇦🇪 Dubai": ZoneInfo("Asia/Dubai")
        }
        
        report = "🌍 **World Station Clock**\n━━━━━━━━━━━━━━━━━━━━\n"
        for city, zi in cities.items():
            c_now = datetime.now(zi)
            report += f"{city}: `{c_now.strftime('%H:%M:%S')} ({c_now.strftime('%d %b')})`\n"
        
        return await edit_or_reply(message, report)

    if is_img:
        status_msg = await edit_or_reply(message, "🎨 *Rendering stylized clock...*")
        try:
            # Drawing Logic
            img = Image.new("RGB", (800, 400), color=(20, 20, 25))
            draw = ImageDraw.Draw(img)
            
            # Use a random background if available
            bg_path = os.path.join(BG_FOLDER, "bg1.jpg") 
            if os.path.exists(bg_path):
                bg = Image.open(bg_path).convert("RGB")
                bg = bg.resize((800, 400))
                from PIL import ImageFilter
                bg = bg.filter(ImageFilter.GaussianBlur(10))
                img.paste(bg, (0, 0))
                
            # Glassmorphism effect overlay
            overlay = Image.new("RGBA", (700, 300), (255, 255, 255, 30))
            img.paste(overlay, (50, 50), overlay)
            
            # Fonts
            font_lg = ImageFont.truetype(FONT_PATH, 100)
            font_sm = ImageFont.truetype(FONT_PATH, 40)
            
            time_str = now.strftime("%H:%M:%S")
            date_str = now.strftime("%A, %d %B %Y")
            
            # Draw Time
            w, h = draw.textbbox((0, 0), time_str, font=font_lg)[2:]
            draw.text(((800-w)//2, 130), time_str, font=font_lg, fill=(255, 255, 255))
            
            # Draw Date
            w, h = draw.textbbox((0, 0), date_str, font=font_sm)[2:]
            draw.text(((800-w)//2, 250), date_str, font=font_sm, fill=(200, 200, 200))
            
            # Draw Logo/Brand
            draw.text((60, 60), "ASTRA USERBOT", font=ImageFont.truetype(FONT_PATH, 20), fill=(255, 255, 255, 150))
            
            output_path = "/tmp/astra_time.jpg"
            img.save(output_path, quality=95)
            
            import base64
            with open(output_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
                
            media = {"mimetype": "image/jpeg", "data": b64_data, "filename": "time.jpg"}
            await client.send_media(message.chat_id, media, caption=f"🕒 **Current Time:** `{now.strftime('%H:%M:%S')}`", reply_to=message.id)
            await status_msg.delete()
            return
        except Exception as e:
            await status_msg.edit(f"❌ Failed to render image: {str(e)}")
            # Fallback to text
    
    # Standard Text Response
    report = (
        f"🕒 **Astra Clock Engine**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 **Date:** `{now.strftime('%d %B %Y')}`\n"
        f"⏰ **Time:** `{now.strftime('%H:%M:%S')}`\n"
        f"🌐 **Zone:** `{config.TIMEZONE}`\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    await edit_or_reply(message, report)

@astra_command(
    name="calendar",
    description="Display monthly or yearly calendar.",
    category="Tools & Utilities",
    aliases=["cal"],
    usage=".calendar [-year] [-img]"
)
async def calendar_handler(client: Client, message: Message):
    """Calendar Handler"""
    args = extract_args(message)
    is_year = "-year" in args
    is_img = "-img" in args
    
    now = datetime.now(TZ)
    
    if is_year:
        cal_str = calendar.TextCalendar(calendar.SUNDAY).formatyear(now.year)
        if len(cal_str) > 3500: # Truncation check
            cal_str = cal_str[:3500] + "..."
        return await edit_or_reply(message, f"📅 **Yearly Calendar: {now.year}**\n```\n{cal_str}\n```")

    if is_img:
        status_msg = await edit_or_reply(message, "🎨 *Rendering calendar...*")
        try:
            img = Image.new("RGB", (1000, 900), color=(15, 15, 20))
            draw = ImageDraw.Draw(img)
            
            # Background
            bg_path = os.path.join(BG_FOLDER, f"bg{now.month % 10 or 1}.jpg")
            if os.path.exists(bg_path):
                bg = Image.open(bg_path).convert("RGB").resize((1000, 900))
                from PIL import ImageFilter
                img.paste(bg.filter(ImageFilter.GaussianBlur(5)), (0, 0))
            
            # Glassmorphism
            overlay = Image.new("RGBA", (900, 800), (0, 0, 0, 160))
            img.paste(overlay, (50, 50), overlay)
            
            font_title = ImageFont.truetype(FONT_PATH, 70)
            font_days = ImageFont.truetype(FONT_PATH, 45)
            font_nums = ImageFont.truetype(FONT_PATH, 50)
            
            title = f"{calendar.month_name[now.month]} {now.year}"
            draw.text((100, 100), title, font=font_title, fill=(255, 215, 0)) # Gold title
            
            headers = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            cl_days = calendar.monthcalendar(now.year, now.month)
            
            # Draw headers
            for i, h in enumerate(headers):
                draw.text((100 + i*120, 220), h, font=font_days, fill=(100, 200, 255))
                
            # Draw numbers
            for r_idx, week in enumerate(cl_days):
                for c_idx, day in enumerate(week):
                    if day == 0: continue
                    color = (255, 255, 255)
                    if day == now.day:
                        color = (0, 255, 0) # Today
                        draw.ellipse([85 + c_idx*120, 290 + r_idx*100, 155 + c_idx*120, 360 + r_idx*100], outline=(0, 255, 0), width=3)
                    
                    draw.text((100 + c_idx*120, 300 + r_idx*100), str(day), font=font_nums, fill=color)
            
            output_path = "/tmp/astra_cal.jpg"
            img.save(output_path)
            
            import base64
            with open(output_path, "rb") as f:
                b64_data = base64.b64encode(f.read()).decode("utf-8")
            
            media = {"mimetype": "image/jpeg", "data": b64_data, "filename": "calendar.jpg"}
            await client.send_media(message.chat_id, media, caption=f"🗓️ **Monthly Calendar:** `{calendar.month_name[now.month]} {now.year}`", reply_to=message.id)
            await status_msg.delete()
            return
        except Exception as e:
            await status_msg.edit(f"❌ Failed to render image: {str(e)}")

    # Text fall-back / standard
    cal_str = calendar.TextCalendar(calendar.SUNDAY).formatmonth(now.year, now.month)
    await edit_or_reply(message, f"📅 **Calendar: {calendar.month_name[now.month]} {now.year}**\n```\n{cal_str}\n```")

@astra_command(
    name="timediff",
    description="Calculate difference between two dates or zones.",
    category="Tools & Utilities",
    usage=".timediff [Date/Time] (e.g. .timediff 2026-12-31)"
)
async def timediff_handler(client: Client, message: Message):
    """Time Diff Handler"""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "⚠️ Usage: `.timediff <YYYY-MM-DD>` or `.timediff <HH:MM>`")
    
    # Basic countdown implementation
    target_str = args[0]
    now = datetime.now(TZ)
    try:
        if ":" in target_str and "-" not in target_str:
            # Assume HH:MM for today/tomorrow
            t_time = datetime.strptime(target_str, "%H:%M").time()
            target = datetime.combine(now.date(), t_time).replace(tzinfo=TZ)
            if target < now:
                target += timedelta(days=1)
        else:
            target = datetime.fromisoformat(target_str).replace(tzinfo=TZ)
            
        diff = target - now
        
        if diff.total_seconds() < 0:
            return await edit_or_reply(message, f"⏳ **Event Passed:** `{abs(diff)}` ago.")
            
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        report = (
            f"⏳ **Astra Countdown**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 **Target:** `{target.strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"📅 **Remaining:** `{f'{days}d ' if days else ''}{hours}h {minutes}m {seconds}s`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await edit_or_reply(message, report)
    except Exception as e:
        await edit_or_reply(message, "❌ Invalid format. Use `YYYY-MM-DD` or `HH:MM`.")

@astra_command(
    name="holiday",
    description="List upcoming Indian holidays.",
    category="Tools & Utilities",
)
async def holiday_handler(client: Client, message: Message):
    """Holiday Handler (Simulated/Static for now, can be expanded with API)"""
    # Using a high-quality static list for common 2026 holidays
    holidays = [
        ("Jan 26", "Republic Day"),
        ("Mar 03", "Holi"),
        ("Mar 31", "Id-ul-Fitr"),
        ("Apr 14", "Ambedkar Jayanti"),
        ("Aug 15", "Independence Day"),
        ("Oct 02", "Gandhi Jayanti"),
        ("Oct 20", "Dussehra"),
        ("Nov 08", "Diwali"),
        ("Dec 25", "Christmas")
    ]
    
    report = "🇮🇳 **Upcoming Indian Holidays (2026)**\n━━━━━━━━━━━━━━━━━━━━\n"
    for date, name in holidays:
        report += f"• `{date}`: **{name}**\n"
    
    await edit_or_reply(message, report)

@astra_command(
    name="event",
    description="Manage local events/reminders.",
    category="Tools & Utilities",
    usage=".event [add|list|del] [text]"
)
async def event_handler(client: Client, message: Message):
    """Event Tracker Handler"""
    # Using db.state to store events as a JSON list for simplicity in this version
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "⚠️ Usage: `.event add [desc]` or `.event list`")
    
    from utils.database import db
    
    cmd = args[0].lower()
    events = await db.get("user_events") or []
    
    if cmd == "add":
        desc = " ".join(args[1:])
        if not desc: return await edit_or_reply(message, "❌ Provide a description.")
        events.append({"desc": desc, "time": datetime.now(TZ).strftime("%Y-%m-%d %H:%M")})
        await db.set("user_events", events)
        return await edit_or_reply(message, f"✅ **Event Added:** `{desc}`")
        
    if cmd == "list":
        if not events: return await edit_or_reply(message, "ℹ️ No events found.")
        report = "📝 **Astra Event Diary**\n━━━━━━━━━━━━━━━━━━━━\n"
        for i, ev in enumerate(events, 1):
            report += f"{i}. [{ev['time']}] {ev['desc']}\n"
        return await edit_or_reply(message, report)
    
    if cmd == "del":
        try:
            idx = int(args[1]) - 1
            removed = events.pop(idx)
            await db.set("user_events", events)
            return await edit_or_reply(message, f"🗑️ **Removed:** `{removed['desc']}`")
        except:
            return await edit_or_reply(message, "❌ Invalid index.")
