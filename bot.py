import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
from pymongo import MongoClient

# -------------------------------------------------------------
# 1. Health Check Server (ለ Render)
# -------------------------------------------------------------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"BamaMusicBot is running with MongoDB!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Health check server running on port {port}...")
    server.serve_forever()

Thread(target=run_health_check_server, daemon=True).start()

# -------------------------------------------------------------
# 2. MongoDB connection & Bot Settings
# -------------------------------------------------------------
MONGO_URI = "mongodb+srv://end1r1as8_db_user:e9pGuwJHXfAGlpz0@cluster0.i4n9gvo.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["bama_music_db"]
songs_collection = db["songs"]

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7278213937:AAH2xcrIWyG75ToXf8mYvhG9TCu3KX57NCo")
REQUIRED_INVITES = 3
user_invites = {}

def get_song(title):
    return songs_collection.find_one({"title_lower": title.lower()})

def save_song_to_db(title, lyrics, audio_id=""):
    songs_collection.update_one(
        {"title_lower": title.lower()},
        {"$set": {"title": title, "title_lower": title.lower(), "lyrics": lyrics, "audio": audio_id}},
        upsert=True
    )

# -------------------------------------------------------------
# 3. Track Invites
# -------------------------------------------------------------
async def track_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    inviter = update.message.from_user.id
    new_members = update.message.new_chat_members
    
    for member in new_members:
        if not member.is_bot and member.id != inviter:
            user_invites[inviter] = user_invites.get(inviter, 0) + 1
            count = user_invites[inviter]
            await update.message.reply_text(
                f"👏 አመሰግናለሁ {update.message.from_user.first_name}! "
                f"እስካሁን **{count}** ሰው ወደ ግሩፑ አክለዋል።"
            )

# -------------------------------------------------------------
# 4. Command Handlers
# -------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🎵 Songs", "ℹ️ About"],
        ["❓ Help"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("👋 Welcome to Bama Music Bot", reply_markup=reply_markup)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 **የቦቱ ትእዛዛት (Commands):**\n\n"
        "/start - ቦቱን ለመጀመር\n"
        "/songs - ሁሉንም የመዝሙሮች ዝርዝር ለማየት\n"
        "/myinvites - የጋበዝካቸውን ሰዎች ብዛት ለማወቅ\n"
        "/about - ስለ ቦቱ መረጃ\n"
        "/help - የእርዳታ መረጃ\n\n"
        "💡 *የመዝሙር ዝርዝር ለማየት 'Songs' የሚለውን ቁልፍ ይጫኑ።*"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "🎶 **Welcome to Bama Music Bot!** 🎶\n\n"
        "Bama Music Bot is your ultimate spiritual music companion, powered by MongoDB cloud database.\n\n"
        "✨ **Key Features:**\n"
        "• 🎵 Unlimited spiritual songs & lyrics\n"
        "• 🎧 Ultra-fast audio playback\n"
        "• 🔍 Easy search & clickable directory\n\n"
        "👨‍💻 **Developed & Maintained by:** Bama\n"
        "🚀 **Version:** 2.0.0 (Cloud Database Enabled)\n\n"
        "Stay blessed and inspired! 🙏"
    )
    await update.message.reply_text(about_text)

async def songs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_songs = list(songs_collection.find().limit(50))
    if not all_songs:
        await update.message.reply_text("❌ ምንም የተመዘገበ መዝሙር አልተገኘም።")
        return

    keyboard = []
    for song in all_songs:
        keyboard.append([InlineKeyboardButton(f"🎵 {song['title']}", callback_data=f"song_{str(song['_id'])}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📜 **የመዝሙሮች ዝርዝር (ለመስማት የሚፈልጉትን መዝሙር ይጫኑ)፡**",
        reply_markup=reply_markup
    )

async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("song_"):
        from bson.objectid import ObjectId
        song_id = query.data.split("_")[1]
        song = songs_collection.find_one({"_id": ObjectId(song_id)})

        if song:
            await query.message.reply_text(f"📖 **{song['title']}**\n\n{song.get('lyrics', '')}")
            if song.get("audio"):
                await query.message.reply_audio(audio=song["audio"], caption=song["title"])

async def my_invites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    count = user_invites.get(user_id, 0)
    await update.message.reply_text(
        f"📊 **የጋበዙት አባላት ብዛት፡** {count}\n"
        f"🎯 **የሚጠበቅብዎት አነስተኛ ብዛት፡** {REQUIRED_INVITES}"
    )

async def add_song_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.replace("/add", "").strip()
        if not text:
            await update.message.reply_text("❌ እባክህ መዝሙሩን በዚህ ፎርማት ላክ፡\n\n`/add ርዕስ | ግጥም | Audio_File_ID`")
            return

        parts = text.split("|")
        title = parts[0].strip()
        lyrics = parts[1].strip() if len(parts) > 1 else ""
        audio_id = parts[2].strip() if len(parts) > 2 else ""

        if not title or not lyrics:
            await update.message.reply_text("❌ እባክህ ቢያንስ ርዕስ እና ግጥም አስገባ!")
            return

        save_song_to_db(title, lyrics, audio_id)
        await update.message.reply_text(f"✅ መዝሙር '{title}' በስኬት ወደ MongoDB ተጨምሯል!")

    except Exception:
        await update.message.reply_text("❌ ስህተት ተፈጥሯል! እባክህ ፎርማቱን አስተካክለህ ድጋሚ ሞክር።")

# -------------------------------------------------------------
# 5. Message & Audio Handlers
# -------------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type

    if chat_type in ["group", "supergroup"]:
        invites_count = user_invites.get(user_id, 0)
        if invites_count < REQUIRED_INVITES:
            await update.message.reply_text(
                f"⚠️ **ይቅርታ {update.message.from_user.first_name}!**\n\n"
                f"ቢያንስ **{REQUIRED_INVITES} አዲስ ሰዎችን** ወደ ግሩፑ መጨመር አለብህ።\n"
                f"እስካሁን የጨመርከው፡ **{invites_count}** ሰው ነው።"
            )
            return

    text = update.message.text.strip()

    if text.lower() in ["songs", "🎵 songs"]:
        await songs(update, context)
        return
    elif text == "ℹ️ About":
        await about(update, context)
        return
    elif text == "❓ Help":
        await help(update, context)
        return

    song = get_song(text)
    if song:
        await update.message.reply_text(song["lyrics"])
        if song.get("audio"):
            await update.message.reply_audio(audio=song["audio"], caption=song["title"])
    else:
        await update.message.reply_text("❌ መዝሙሩ አልተገኘም። እባክህ 'Songs' የሚለውን በመጫን ከዝርዝሩ ውስጥ ምረጥ።")

async def handle_forwarded_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.audio:
        file_id = update.message.audio.file_id
        title = update.message.caption.strip() if update.message.caption else "ያልተሰየመ መዝሙር"
        lyrics = "የግጥም ዝርዝር አልገባም"
        save_song_to_db(title, lyrics, file_id)

async def handle_direct_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Audioው በተሳካ ሁኔታ ደርሷል!")

# -------------------------------------------------------------
# 6. Start Bot
# -------------------------------------------------------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("about", about))
app.add_handler(CommandHandler("songs", songs))
app.add_handler(CommandHandler("myinvites", my_invites))
app.add_handler(CommandHandler("add", add_song_command))

app.add_handler(CallbackQueryHandler(handle_button_click))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_invites))
app.add_handler(MessageHandler(filters.AUDIO & filters.FORWARDED, handle_forwarded_audio))
app.add_handler(MessageHandler(filters.AUDIO & ~filters.FORWARDED, handle_direct_audio))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running with MongoDB Atlas...")
app.run_polling()
