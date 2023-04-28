import os
import io
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from PIL import Image
from token_telegram import TOKEN_TG
from main import setup_webdriver

# функция для обработки команды /start
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Отправьте мне тикер для получения графика.")

# функция для обработки сообщений с тикером
def get_graph(update, context):
    text = update.message.text.upper()

    # setup_webdriver()
    #  прописать функцию, которая будет вытягивать актуальную цену

    if not text.isalpha():
        context.bot.send_message(chat_id=update.effective_chat.id, text="Пожалуйста, отправьте мне только тикер.")
        return

    ticker = text
    filename = f"{ticker}.png"
    if not os.path.exists(f"graph/{filename}"):
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"К сожалению, графика для тикера {ticker} нет.")
        return
    
    with open(f"graph/{filename}", "rb") as f:
        img = Image.open(f)
        bio = io.BytesIO()
        img.save(bio, "PNG")
        bio.seek(0)
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=bio)

def start_bot():
    updater = Updater(TOKEN_TG, use_context=True)

    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, get_graph))

    updater.start_polling()
    updater.idle()  # Добавьте эту строку, чтобы бот продолжал работать, пока его не остановят

# start_bot()