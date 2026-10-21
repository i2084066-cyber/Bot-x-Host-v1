import os
import logging
import sqlite3
import time
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN", "").strip()
DB_PATH = os.getenv("DB_PATH", "history.db")
MAX_HISTORY_REPLY = 50
MAX_TEXT = 10000

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

def connect_db():
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    return con

def init_db():
    with connect_db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER,
                username TEXT,
                message_type TEXT NOT NULL,
                message_text TEXT,
                created_at TEXT NOT NULL
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_history_chat_id ON history(chat_id)")
        con.commit()

def save_message(update: Update, message_type: str, message_text: str = ""):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or not chat:
        return
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        with connect_db() as con:
            con.execute(
                """INSERT INTO history
                (chat_id, user_id, username, message_type, message_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (chat.id, user.id if user else None, user.username if user else None,
                 message_type, (message_text or "")[:MAX_TEXT], timestamp)
            )
            con.commit()
    except sqlite3.Error:
        logging.exception("Could not save history entry")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_message(update, "command", "/start")
    await update.effective_message.reply_text(
        "Telegram History Bot online hai ✅\n\n"
        "Commands:\n"
        "/start - bot shuru karein\n"
        "/help - madad\n"
        "/history [number] - recent history\n"
        "/count - total saved entries\n"
        "/export - history TXT file mein\n\n"
        "Bot ko jo messages milte hain, wahi save hote hain."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_message(update, "command", "/help")
    await update.effective_message.reply_text(
        "Text message bhejein, bot use history mein save karega.\n"
        "/history 20 - recent 20 entries\n"
        "/count - total entries\n"
        "/export - history file\n\n"
        "Bot purane chats ko khud se access nahi kar sakta."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text:
        return
    save_message(update, "text", msg.text)
    await msg.reply_text("Saved ✅")

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_message(update, "command", "/history")
    chat = update.effective_chat
    if not chat:
        return
    try:
        limit = int(context.args[0]) if context.args else 10
    except (ValueError, IndexError):
        limit = 10
    limit = max(1, min(limit, MAX_HISTORY_REPLY))
    with connect_db() as con:
        rows = con.execute(
            """SELECT message_type, message_text, created_at FROM history
               WHERE chat_id=? ORDER BY id DESC LIMIT ?""",
            (chat.id, limit)
        ).fetchall()
    if not rows:
        await update.effective_message.reply_text("Abhi history khaali hai.")
        return
    lines = []
    for kind, body, created in reversed(rows):
        clean = (body or "").replace("\n", " ")
        lines.append(f"{created} [{kind}] {clean[:350]}")
    result = "\n".join(lines)
    if len(result) > 3800:
        result = result[-3800:]
    await update.effective_message.reply_text(result)

async def count_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_message(update, "command", "/count")
    chat = update.effective_chat
    with connect_db() as con:
        count = con.execute(
            "SELECT COUNT(*) FROM history WHERE chat_id=?",
            (chat.id,)
        ).fetchone()[0]
    await update.effective_message.reply_text(f"Total saved entries: {count}")

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_message(update, "command", "/export")
    chat = update.effective_chat
    with connect_db() as con:
        rows = con.execute(
            """SELECT created_at, message_type, message_text FROM history
               WHERE chat_id=? ORDER BY id ASC""", (chat.id,)
        ).fetchall()
    if not rows:
        await update.effective_message.reply_text("Export karne ke liye history nahi hai.")
        return
    path = f"/tmp/history_{chat.id}_{int(time.time())}.txt"
    with open(path, "w", encoding="utf-8") as f:
        for created, kind, body in rows:
            f.write(f"{created} [{kind}] {body or ''}\n")
    try:
        with open(path, "rb") as f:
            await update.effective_message.reply_document(
                document=f, filename="telegram_history.txt",
                caption=f"Exported {len(rows)} entries."
            )
    finally:
        try:
            os.remove(path)
        except OSError:
            pass

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Unhandled exception: %s", context.error)

def main():
    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN missing. Render > Environment mein BOT_TOKEN add karein."
        )
    init_db()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("count", count_command))
    app.add_handler(CommandHandler("export", export_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_error_handler(error_handler)
    logging.info("Telegram History Bot starting")
    app.run_polling(drop_pending_updates=False)

if __name__ == "__main__":
    main()
