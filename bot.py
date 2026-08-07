import json
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

# -------------------------------------------------------------
# 1. Render Port Error እንዳያሳይ የሚረዳ Web Server (Health Check)
# -------------------------------------------------------------
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"BamaMusicBot is alive and running!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Health check server running on port {port}...")
    server.serve_forever()

Thread(target=run_health_check_server, daemon=True).start()

# -------------------------------------------------------------
# 2. የቦት ቅንብሮች እና Data Storage
# -------------------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7278213937:AAEkAf3PEoyeLEgvIJPB1ZPjRXJeRCHDbMM")
REQUIRED_INVITES = 3  # ተጠቃሚው አገልግሎት ለማግኘት መጋበዝ ያለበት አነስተኛ ሰው ብዛት

user_invites = {}

def load_songs():
    file_path = "songs.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            try:
                return json.load(file)
            except Exception:
                return {}
    return {}

def save_song(title, lyrics, audio_id=""):
    songs = load_songs()
    songs[title] = {
        "lyrics": lyrics,
        "audio": audio_id
    }
    with open("songs.json", "w", encoding="utf-8") as file:
        json.dump(songs, file, ensure_ascii=False, indent=4)

# -------------------------------------------------------------
# 3. አዲስ ሰው ሲጨመር መቆጣጠሪያ (Track Invites)
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
    await update.message.reply_text(
        "👋 Welcome to Bama Music Bot",
        reply_markup=reply_markup
    )

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
        "Bama Music Bot is your ultimate spiritual music companion, designed to bring you "
        "uplifting songs, lyrics, and audio content directly inside Telegram.\n\n"
        "✨ **Key Features:**\n"
        "• 🎵 Access a rich collection of spiritual songs & lyrics\n"
        "• 🎧 Listen to and download high-quality audio files\n"
        "• 🔍 Easy and fast song search by title\n"
        "• 👥 Community-driven music sharing\n\n"
        "👨‍💻 **Developed & Maintained by:** Bama\n"
        "🚀 **Version:** 1.0.0\n\n"
        "Thank you for using Bama Music Bot! Stay blessed and inspired. 🙏"
    )
    await update.message.reply_text(about_text)

# መዝሙሮችን በሚነኩ ቁልፎች (Clickable Buttons) ማቅረቢያ
async def songs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    songs_database = load_songs()
    if not songs_database:
        await update.message.reply_text("❌ ምንም የተመዘገበ መዝሙር አልተገኘም።")
        return

    keyboard = []
    for index, title in enumerate(songs_database.keys()):
        # እያንዳንዱን መዝሙር የሚነካ ቁልፍ ማድረግ
        keyboard.append([InlineKeyboardButton(f"🎵 {title}", callback_data=f"song_{index}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📜 **የመዝሙሮች ዝርዝር (ለመስማት የሚፈልጉትን መዝሙር ይጫኑ)፡**",
        reply_markup=reply_markup
    )

# ተጠቃሚው የሚነካውን ቁልፍ ሲጫን የሚሰራ Function
async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    songs_database = load_songs()
    song_titles = list(songs_database.keys())

    if query.data.startswith("song_"):
        index = int(query.data.split("_")[1])
        if index < len(song_titles):
            title = song_titles[index]
            data = songs_database[title]

            # ግጥሙን ይልካል
            await query.message.reply_text(f"📖 **{title}**\n\n{data.get('lyrics', '')}")

            # Audio ካለው ድምፁን ይልካል
            if data.get("audio", "") != "":
                await query.message.reply_audio(
                    audio=data["audio"],
                    caption=title
                )

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
            await update.message.reply_text(
                "❌ እባክህ መዝሙሩን በዚህ ፎርማት ላክ፡\n\n"
                "`/add ርዕስ | ግጥም | Audio_File_ID`"
            )
            return

        parts = text.split("|")
        title = parts[0].strip()
        lyrics = parts[1].strip() if len(parts) > 1 else ""
        audio_id = parts[2].strip() if len(parts) > 2 else ""

        if not title or not lyrics:
            await update.message.reply_text("❌ እባክህ ቢያንስ ርዕስ እና ግጥም አስገባ!")
            return

        save_song(title, lyrics, audio_id)
        await update.message.reply_text(f"✅ መዝሙር '{title}' በስኬት ተጨምሯል!")

    except Exception:
        await update.message.reply_text("❌ ስህተት ተፈጥሯል! እባክህ ፎርማቱን አስተካክለህ ድጋሚ ሞክር።")

# -------------------------------------------------------------
# 5. Message & Audio Handlers
# -------------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_type = update.effective_chat.type

    # ግሩፕ ውስጥ ከሆነ የተጋበዘውን ብዛት ያረጋግጣል
    if chat_type in ["group", "supergroup"]:
        invites_count = user_invites.get(user_id, 0)
        if invites_count < REQUIRED_INVITES:
            await update.message.reply_text(
                f"⚠️ **ይቅርታ {update.message.from_user.first_name}!**\n\n"
                f"የሙዚቃ ግጥም እና ድምፅ ለማግኘት ቢያንስ **{REQUIRED_INVITES} አዲስ ሰዎችን** ወደ ግሩፑ መጨመር (Add ማድረግ) አለብህ።\n"
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

    songs_database = load_songs()
    found = False

    for title, data in songs_database.items():
        if text.lower() == title.lower():
            found = True
            await update.message.reply_text(data["lyrics"])
            if data.get("audio", "") != "":
                await update.message.reply_audio(
                    audio=data["audio"],
                    caption=title
                )
            break

    if not found:
        await update.message.reply_text("❌ መዝሙሩ አልተገኘም። እባክህ 'Songs' የሚለውን በመጫን ከዝርዝሩ ውስጥ ምረጥ።")

# ቻናል ላይ Forward የተደረገ Audio ሲመጣ በዝምታ መመዝገቢያ
async def handle_forwarded_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.audio:
        file_id = update.message.audio.file_id
        title = update.message.caption.strip() if update.message.caption else "ያልተሰየመ መዝሙር"
        lyrics = "የግጥም ዝርዝር አልገባም"
        
        save_song(title, lyrics, file_id)

# ኖርማል Audio ሲላክ
async def handle_direct_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Audioው በተሳካ ሁኔታ ደርሷል!")

# -------------------------------------------------------------
# 6. ቦቱን ማስነሳት
# -------------------------------------------------------------
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Commands
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("about", about))
app.add_handler(CommandHandler("songs", songs))
app.add_handler(CommandHandler("myinvites", my_invites))
app.add_handler(CommandHandler("add", add_song_command))

# Handlers
app.add_handler(CallbackQueryHandler(handle_button_click))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_invites))
app.add_handler(MessageHandler(filters.AUDIO & filters.FORWARDED, handle_forwarded_audio))
app.add_handler(MessageHandler(filters.AUDIO & ~filters.FORWARDED, handle_direct_audio))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")
app.run_polling()
