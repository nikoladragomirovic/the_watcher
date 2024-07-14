import os
from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN: Final = os.environ.get('THE_WATCHER_TOKEN')
BOT_USERNAME: Final = '@esp32_watcher_bot'

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await context.bot.send_message(chat_id=chat_id, text=f"Your chat ID is: {chat_id}")

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass

if __name__ == '__main__':

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler('id', get_chat_id))

    app.add_error_handler(error)

    app.run_polling(poll_interval=0, drop_pending_updates=True)