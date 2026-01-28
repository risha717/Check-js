import os
import json
import logging
import random
import string
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ==================== কনফিগারেশন ====================
BOT_TOKEN = "8006015641:AAHMiqhkmtvRmdLMN1Rbz2EnwsIrsGfH8qU"
ADMIN_ID = 1858324638
VIDEO_CHANNEL_ID = -1003872857468  # আপনার চ্যানেল আইডি
CHANNEL_USERNAME = "@CineflixOfficialbd"  # আপনার চ্যানেল

# লগিং সেটআপ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

print("🤖 Cineflix Bot Starting...")
print(f"📢 Channel: {CHANNEL_USERNAME}")
print(f"🔑 Admin: {ADMIN_ID}")

# ==================== ডাটাবেজ ক্লাস ====================
class Database:
    def __init__(self):
        self.db_file = "data.json"
        self.data = self.load()
    
    def load(self):
        """ডাটা লোড করুন"""
        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f"✅ Database loaded with {len(data.get('videos', {}))} videos")
                return data
        except:
            print("⚠️ No database found, creating new one")
            return {"videos": {}, "stats": {"total": 0}}
    
    def save(self):
        """ডাটা সেভ করুন"""
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def add_video(self, message_id, caption=""):
        """নতুন ভিডিও যোগ করুন"""
        # ৬ ডিজিটের র‍্যান্ডম কোড তৈরি
        code = f"v_{random.randint(100000, 999999)}"
        
        # নিশ্চিত করুন কোড ইউনিক
        while code in self.data["videos"]:
            code = f"v_{random.randint(100000, 999999)}"
        
        self.data["videos"][code] = {
            "message_id": message_id,
            "title": caption[:200] if caption else "Cineflix Video",
            "date": datetime.now().strftime("%d-%m-%Y %H:%M"),
            "views": 0
        }
        
        self.data["stats"]["total"] = len(self.data["videos"])
        self.save()
        
        print(f"🎬 New video registered: {code} (Message ID: {message_id})")
        return code
    
    def get_video(self, code):
        """ভিডিও তথ্য পান"""
        return self.data["videos"].get(code)
    
    def increment_views(self, code):
        """ভিউ কাউন্ট বাড়ান"""
        if code in self.data["videos"]:
            self.data["videos"][code]["views"] += 1
            self.save()

# ডাটাবেজ ইনিশিয়ালাইজ
db = Database()

# ==================== হেল্পার ফাংশন ====================
async def check_channel_member(user_id, bot):
    """ইউজার চ্যানেলে আছে কিনা চেক করুন"""
    try:
        member = await bot.get_chat_member(VIDEO_CHANNEL_ID, user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception as e:
        print(f"❌ Channel check error: {e}")
        return False

# ==================== কমান্ড হ্যান্ডলার ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """স্টার্ট কমান্ড"""
    user = update.effective_user
    print(f"👤 User started: {user.id} (@{user.username})")
    
    # যদি কোড সহ আসে
    if context.args:
        code = context.args[0]
        print(f"🔗 Code received: {code}")
        await handle_video_request(update, context, code)
        return
    
    # স্বাগতম মেসেজ
    welcome = f"""
🎬 *Cineflix Universe Pro*

👋 Hello {user.first_name}!

📱 *How to use:*
1. Open our Mini App
2. Select any video
3. Click 'WATCH NOW'
4. Get video instantly!

🔗 Mini App: https://cinaflix-streaming.vercel.app

📢 Channel: {CHANNEL_USERNAME}
🤖 Bot: @Cinaflix_Streembot

⚡ *Direct Code:* Send me `v_123456`
"""
    
    await update.message.reply_text(welcome, parse_mode="Markdown", disable_web_page_preview=True)

async def handle_video_request(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    """ভিডিও রিকোয়েস্ট হ্যান্ডল করুন"""
    user = update.effective_user
    print(f"🔄 Processing code: {code} for user: {user.id}")
    
    # চ্যানেল চেক
    is_member = await check_channel_member(user.id, context.bot)
    
    if not is_member:
        print(f"❌ User {user.id} not in channel, asking to join")
        
        keyboard = [
            [InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("🔍 I Joined", callback_data=f"check_{code}")]
        ]
        
        await update.message.reply_text(
            f"🔒 *Content Locked*\n\nJoin {CHANNEL_USERNAME} to watch.\nAfter joining click below:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    # ভিডিও পাঠানো
    await send_video(update, context, code, user.id)

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str, user_id: int):
    """ভিডিও পাঠান"""
    
    if code.startswith("v_"):
        video = db.get_video(code)
        
        if not video:
            print(f"❌ Video not found: {code}")
            await update.message.reply_text("❌ Video not found! Check the code.")
            return
        
        print(f"📤 Sending video: {code} (Message ID: {video['message_id']})")
        
        try:
            # ভিডিও ফরওয়ার্ড করার চেষ্টা করুন
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=VIDEO_CHANNEL_ID,
                message_id=video["message_id"],
                caption=f"🎬 {video['title']}\n✅ @Cinaflix_Streembot"
            )
            
            # ভিউ কাউন্ট বাড়ান
            db.increment_views(code)
            print(f"✅ Video sent successfully: {code}")
            
        except Exception as e:
            print(f"❌ Failed to send video: {e}")
            
            # ডিবাগ তথ্য
            debug_info = f"""
❌ *Error Details:*
• Code: `{code}`
• Message ID: `{video['message_id']}`
• Channel ID: `{VIDEO_CHANNEL_ID}`
• Error: {str(e)[:100]}
"""
            
            await update.message.reply_text(
                "❌ Failed to send video! Admin has been notified.",
                parse_mode="Markdown"
            )
            
            # অ্যাডমিনকে জানান
            try:
                await context.bot.send_message(
                    ADMIN_ID,
                    f"🚨 *Video Send Failed!*\n\n"
                    f"Code: `{code}`\n"
                    f"User: {user_id}\n"
                    f"Error: {e}\n\n"
                    f"Check bot permissions in channel!",
                    parse_mode="Markdown"
                )
            except:
                pass
    
    else:
        await update.message.reply_text("❌ Invalid code format!")

# ==================== ক্যালব্যাক হ্যান্ডলার ====================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ক্যালব্যাক হ্যান্ডল করুন"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("check_"):
        code = query.data.replace("check_", "")
        user_id = query.from_user.id
        
        # আবার চেক করুন
        if await check_channel_member(user_id, context.bot):
            await query.edit_message_text("✅ Verified! Sending video...")
            await send_video(update, context, code, user_id)
        else:
            await query.answer("❌ You haven't joined the channel!", show_alert=True)

# ==================== চ্যানেল হ্যান্ডলার ====================
async def channel_post_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """চ্যানেলে নতুন পোস্ট হ্যান্ডল করুন"""
    message = update.channel_post
    
    # শুধু ভিডিও/ডকুমেন্ট হ্যান্ডল করুন
    if message.video or message.document:
        print(f"📹 New video in channel: ID={message.message_id}")
        
        # কোড তৈরি করুন
        code = db.add_video(message.message_id, message.caption)
        
        # অ্যাডমিনকে নোটিফাই করুন
        try:
            await context.bot.send_message(
                ADMIN_ID,
                f"🎬 *New Video Registered!*\n\n"
                f"Title: {message.caption[:50] if message.caption else 'No title'}\n"
                f"Code: `{code}`\n"
                f"Time: {datetime.now().strftime('%H:%M')}\n\n"
                f"Add to Google Sheet: `{code}`",
                parse_mode="Markdown"
            )
            print(f"📨 Admin notified for code: {code}")
        except Exception as e:
            print(f"Failed to notify admin: {e}")

# ==================== অ্যাডমিন কমান্ড ====================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """বট স্ট্যাটস"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    total_videos = len(db.data["videos"])
    total_views = sum(v.get("views", 0) for v in db.data["videos"].values())
    
    stats_text = f"""
📊 *Bot Statistics*

🎬 Total Videos: {total_videos}
👁️ Total Views: {total_views}
📢 Channel: {CHANNEL_USERNAME}
🤖 Bot: @Cinaflix_Streembot

🔄 Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    await update.message.reply_text(stats_text, parse_mode="Markdown")

async def debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ডিবাগ তথ্য"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    # চ্যানেল তথ্য
    try:
        chat = await context.bot.get_chat(VIDEO_CHANNEL_ID)
        channel_info = f"""
📢 *Channel Info:*
Title: {chat.title}
ID: {chat.id}
Type: {chat.type}
Username: @{chat.username}
"""
    except Exception as e:
        channel_info = f"❌ Channel error: {e}"
    
    # বট ইনফো
    bot_info = await context.bot.get_me()
    
    debug_text = f"""
🔧 *Debug Information*

🤖 *Bot Info:*
Name: {bot_info.first_name}
Username: @{bot_info.username}
ID: {bot_info.id}

{channel_info}

📁 *Database:*
Total Videos: {len(db.data['videos'])}
File: data.json
"""
    
    await update.message.reply_text(debug_text, parse_mode="Markdown")

# ==================== মেইন ফাংশন ====================
def main():
    """বট শুরু করুন"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # হ্যান্ডলার যোগ করুন
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("debug", debug))
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # চ্যানেল হ্যান্ডলার
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_post_handler))
    
    # সরাসরি কোড মেসেজ
    async def handle_direct_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip()
        if text.startswith("v_") or text.startswith("d_"):
            await handle_video_request(update, context, text)
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_direct_code))
    
    print("=" * 50)
    print("✅ Bot is ready!")
    print("=" * 50)
    
    # বট রান করুন
    app.run_polling()

if __name__ == "__main__":
    main()
