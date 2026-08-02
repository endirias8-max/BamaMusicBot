import json
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = "7278213937:AAEkAf3PEoyeLEgvIJPB1ZPjRXJeRCHDbMM"


# ከ JSON ፋይል ውስጥ የመዝሙር ዳታዎችን ለማንበብ የሚረዳ Function
def load_songs():
    file_path = "songs.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}


# አዲስ መዝሙር ወደ JSON ፋይል የሚፅፍ Function
def save_song(title, lyrics, audio_id="`CQACAgIAAx0CcWT_IQACAgJqbESCiN4eQDtBONhv4ZZYpSPkmgAC6qsAAlRdYUstP8lTyC4z5T0E`"):
    songs = load_songs()
    songs[title] = {
        "lyrics": lyrics,
        "audio": audio_id
    }
    with open("songs.json", "w", encoding="utf-8") as file:
        json.dump(songs, file, ensure_ascii=False, indent=4)


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
        "/songs - የመዝሙሮች ዝርዝር ለማየት\n"
        "/about - ስለ ቦቱ መረጃ\n"
        "/help - የእርዳታ መረጃ\n\n"
        "➕ **አዲስ መዝሙር ለመጨመር፡**\n"
        "`/add ርዕስ | ግጥም | Audio_File_ID`\n\n"
        "*(የድምፅ ፋይል id ከሌለህ የድምፁን ኮድ ሳታስገባ ርዕስ እና ግጥሙን ብቻ መላክ ትችላለህ)*"
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "This bot was created by Bama."
    )


async def songs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    songs_database = load_songs()
    text = ""

    if not songs_database:
        text = "❌ ምንም የተመዘገበ መዝሙር አልተገኘም።"
    else:
        text = "📜 **የመዝሙሮች ዝርዝር፡**\n\n"
        for song in songs_database:
            text += "• " + song + "\n"

    await update.message.reply_text(text)


# በቴሌግራም መልእክት አዲስ መዝሙር መጨመሪያ Handler
async def add_song_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # ከ /add በኋላ ያለውን ጽሁፍ መውሰድ
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

    except Exception as e:
        await update.message.reply_text("❌ ስህተት ተፈጥሯል! እባክህ ፎርማቱን አስተካክለህ ድጋሚ ሞክር።")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "🎵 Songs":
        await songs(update, context)
        return

    if text == "ℹ️ About":
        await about(update, context)
        return

    if text == "❓ Help":
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
        await update.message.reply_text("❌ መዝሙሩ አልተገኘም።")


# Audio ፋይል ሲላክ File ID መስጫ
async def get_audio_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.audio.file_id

    await update.message.reply_text(
        f"🎵 Audio File ID:\n\n`{file_id}`"
    )


app = ApplicationBuilder().token(BOT_TOKEN).build()

# Command Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("about", about))
app.add_handler(CommandHandler("songs", songs))
app.add_handler(CommandHandler("add", add_song_command))

# Message Handlers
app.add_handler(MessageHandler(filters.AUDIO, get_audio_file_id))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
print("Bot is running...")
app.run_polling()
import json
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = "7278213937:AAEkAf3PEoyeLEgvIJPB1ZPjRXJeRCHDbMM"


# ከ JSON ፋይል ውስጥ የመዝሙር ዳታዎችን ለማንበብ የሚረዳ Function
def load_songs():
    file_path = "songs.json"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}


# አዲስ መዝሙር ወደ JSON ፋይል የሚፅፍ Function
def save_song(title, lyrics, audio_id="`CQACAgIAAx0CcWT_IQACAgJqbESCiN4eQDtBONhv4ZZYpSPkmgAC6qsAAlRdYUstP8lTyC4z5T0E`"):
    songs = load_songs()
    songs[title] = {
        "lyrics": lyrics,
        "audio": audio_id
    }
    with open("songs.json", "w", encoding="utf-8") as file:
        json.dump(songs, file, ensure_ascii=False, indent=4)


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
        "/songs - የመዝሙሮች ዝርዝር ለማየት\n"
        "/about - ስለ ቦቱ መረጃ\n"
        "/help - የእርዳታ መረጃ\n\n"
        "➕ **አዲስ መዝሙር ለመጨመር፡**\n"
        "`/add ርዕስ | ግጥም | Audio_File_ID`\n\n"
        "*(የድምፅ ፋይል id ከሌለህ የድምፁን ኮድ ሳታስገባ ርዕስ እና ግጥሙን ብቻ መላክ ትችላለህ)*"
    )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "This bot was created by Bama."
    )


async def songs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    songs_database = load_songs()
    text = ""

    if not songs_database:
        text = "❌ ምንም የተመዘገበ መዝሙር አልተገኘም።"
    else:
        text = "📜 **የመዝሙሮች ዝርዝር፡**\n\n"
        for song in songs_database:
            text += "• " + song + "\n"

    await update.message.reply_text(text)


# በቴሌግራም መልእክት አዲስ መዝሙር መጨመሪያ Handler
async def add_song_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # ከ /add በኋላ ያለውን ጽሁፍ መውሰድ
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

    except Exception as e:
        await update.message.reply_text("❌ ስህተት ተፈጥሯል! እባክህ ፎርማቱን አስተካክለህ ድጋሚ ሞክር።")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "🎵 Songs":
        await songs(update, context)
        return

    if text == "ℹ️ About":
        await about(update, context)
        return

    if text == "❓ Help":
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
        await update.message.reply_text("❌ መዝሙሩ አልተገኘም።")


# Audio ፋይል ሲላክ File ID መስጫ
async def get_audio_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id = update.message.audio.file_id

    await update.message.reply_text(
        f"🎵 Audio File ID:\n\n`{file_id}`"
    )


app = ApplicationBuilder().token(BOT_TOKEN).build()

# Command Handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help))
app.add_handler(CommandHandler("about", about))
app.add_handler(CommandHandler("songs", songs))
app.add_handler(CommandHandler("add", add_song_command))

# Message Handlers
app.add_handler(MessageHandler(filters.AUDIO, get_audio_file_id))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
print("Bot is running...")
app.run_polling()

