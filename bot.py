import os
import ssl
import certifi
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
        self.wfile.write(b"BamaMusicBot is running smoothly!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

Thread(target=run_health_check_server, daemon=True).start()

# -------------------------------------------------------------
# 2. Database Connection & Settings (TLS/SSL Strict Fix)
# -------------------------------------------------------------
MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://end1r1as8_db_user:e9pGuwJHXfAGlpz0@cluster0.i4n9gvo.mongodb.net/?appName=Cluster0&retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"
)

# tlsAllowInvalidCertificates እና ssl_cert_reqs የ SSL Handshake ኤረርን ያስቀራሉ
client = MongoClient(
    MONGO_URI,
    tls=True,
    tlsAllowInvalidCertificates=True,
    tlsCAFile=certifi.where()
)
db = client["bama_music_db"]
songs_collection = db["songs"]

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7278213937:AAH2xcrIWyG75ToXf8mYvhG9TCu3KX57NCo")
REQUIRED_INVITES = 3
user_invites = {}

PAGE_SIZE = 10

def save_song_to_db(title, lyrics, audio_id=""):
    songs_collection.update_one(
        {"title_lower": title.lower()},
        {"$set": {"title": title, "title_lower": title.lower(), "lyrics": lyrics, "audio": audio_id}},
        upsert=True
    )

# -------------------------------------------------------------
# 3. Pagination Keyboard Generator
# -------------------------------------------------------------
def get_songs_keyboard(page=0):
    skip = page * PAGE_SIZE
    songs = list(songs_collection.find().skip(skip).limit(PAGE_SIZE))
    total_songs = songs_collection.count_documents({})

    keyboard = []
    for song in songs:
        keyboard.append([InlineKeyboardButton(f"🎵 {song['title']}", callback_data=f"song_{str(song['_id'])}")])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{page - 1}"))
    if (page + 1) * PAGE_SIZE < total_songs:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page + 1}"))

    if nav_buttons:
        keyboard.append(nav_buttons)

    return InlineKeyboardMarkup(keyboard), total_songs

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
        "/songs - የመዝሙሮች ዝርዝር ለማየት\n"
        "/myinvites - የጋበዝካቸውን ሰዎች ብዛት ለማወቅ\n"
        "/about - ስለ ቦቱ መረጃ\n"
        "/help - የእርዳታ መረጃ\n\n"
        "💡 *የመዝሙር ስም በቀጥታ በመጻፍ መፈለግ ትችላለህ!*"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "🎶 **Welcome to Bama Music Bot!** 🎶\n\n"
        "Bama Music Bot is powered by MongoDB Cloud Database for high-speed delivery.\n\n"
        "👨‍💻 **Maintained by:** Bama\n"
        "🚀 **Version:** 2.1.0"
    )
    await update.message.reply_text(about_text)

async def songs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        reply_markup, total = get_songs_keyboard(page=0)
        if total == 0:
            await update.message.reply_text("❌ ምንም የተመዘገበ መዝሙር አልተገኘም።")
            return

        await update.message.reply_text(
            f"📜 **የመዝሙሮች ዝርዝር (ጠቅላላ፡ {total})፡**\n"
            "ለመስማት የሚፈልጉትን መዝሙር ይጫኑ፦",
            reply_markup=reply_markup
        )
    except Exception as e:
        await update.message.reply_text(f"❌ የዳታቤዝ ስህተት፡ {str(e)}")

async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("page_"):
        page = int(query.data.split("_")[1])
        reply_markup, total = get_songs_keyboard(page=page)
        await query.edit_message_text(
            f"📜 **የመዝሙሮች ዝርዝር (ጠቅላላ፡ {total}) - ገፅ {page + 1}፡**",
            reply_markup=reply_markup
        )

    elif query.data.startswith("song_"):
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
    await update.message.reply_text(f"📊 **የጋበዙት አባላት ብዛት፡** {count}\n🎯 **የሚጠበቀው፡** {REQUIRED_INVITES}")

async def add_song_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raw_text = update.message.text[4:].strip()
        if not raw_text or "|" not in raw_text:
            await update.message.reply_text(
                "❌ **ትክክለኛ አጠቃቀም፦**\n`/add የመዝሙር ርዕስ | የመዝሙሩ ግጥም`",
                parse_mode="Markdown"
            )
            return

        parts = raw_text.split("|", 1)
        title = parts[0].strip()
        lyrics = parts[1].strip()

        if not title:
            await update.message.reply_text("❌ እባክህ የመዝሙሩን ርዕስ አስገባ!")
            return

        save_song_to_db(title, lyrics)
        await update.message.reply_text(f"✅ መዝሙር **'{title}'** በስኬት ተጨምሯል!", parse_mode="Markdown")

    except Exception as err:
        await update.message.reply_text(f"❌ ስህተት ተፈጥሯል፡ {str(err)}")

# -------------------------------------------------------------
# 5. Message Handling & Fast Search
# -------------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text.lower() in ["songs", "🎵 songs"]:
        await songs(update, context)
        return
    elif text.lower() in ["about", "ℹ️ about"]:
        await about(update, context)
        return
    elif text.lower() in ["help", "❓ help"]:
        await help(update, context)
        return

    # በፍጥነት መዝሙር በስም መፈለጊያ (Search)
    try:
        results = list(songs_collection.find({"title_lower": {"$regex": text.lower()}}).limit(10))

        if results:
            if len(results) == 1:
                song = results[0]
                await update.message.reply_text(f"📖 **{song['title']}**\n\n{song.get('lyrics', '')}")
                if song.get("audio"):
                    await update.message.reply_audio(audio=song["audio"], caption=song["title"])
            else:
                keyboard = []
                for song in results:
                    keyboard.append([InlineKeyboardButton(f"🎵 {song['title']}", callback_data=f"song_{str(song['_id'])}")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text("🔎 **የተገኙ መዝሙሮች፦**", reply_markup=reply_markup)
        else:
            await update.message.reply_text("❌ የቀረበው መዝሙር አልተገኘም። እባክዎ 'Songs' የሚለውን በመጫን ይምረጡ።")
    except Exception as e:
        await update.message.reply_text(f"❌ የመፈለግ ስህተት፡ {str(e)}")

async def handle_forwarded_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.audio:
        file_id = update.message.audio.file_id
        title = update.message.caption.strip() if update.message.caption else "ያልተሰየመ መዝሙር"
        save_song_to_db(title, "የግጥም ዝርዝር አልገባም", file_id)
        await update.message.reply_text(f"✅ Audio '{title}' ተመዝግቧል!")

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
app.add_handler(MessageHandler(filters.AUDIO & filters.FORWARDED, handle_forwarded_audio))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot running...")
app.run_polling()
