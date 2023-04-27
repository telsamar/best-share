import os
import io
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from PIL import Image
from token_telegram import TOKEN_TG

# функция для обработки команды /start
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Отправьте мне тикер для получения графика.")

# функция для обработки сообщений с тикером
def get_graph(update, context):
    # получаем текст сообщения
    text = update.message.text.upper()
    
    # проверяем, содержит ли сообщение тикер
    if not text.isalpha():
        context.bot.send_message(chat_id=update.effective_chat.id, text="Пожалуйста, отправьте мне только тикер.")
        return
    
    # получаем тикер из сообщения
    ticker = text
    
    # проверяем, есть ли файл с таким именем в папке "graph"
    filename = f"{ticker}.png"
    if not os.path.exists(f"graph/{filename}"):
        context.bot.send_message(chat_id=update.effective_chat.id, text=f"К сожалению, графика для тикера {ticker} нет.")
        return
    
    # открываем файл с графиком
    with open(f"graph/{filename}", "rb") as f:
        # создаем объект изображения
        img = Image.open(f)
        # создаем объект BytesIO
        bio = io.BytesIO()
        # сохраняем изображение в формате PNG в объект BytesIO
        img.save(bio, "PNG")
        # перемещаем указатель в начало файла
        bio.seek(0)
        # отправляем данные в виде байтового потока пользователю
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=bio)

# создаем экземпляр Updater и задаем токен
updater = Updater(TOKEN_TG, use_context=True)

# добавляем обработчики команд и сообщений
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, get_graph))

# запускаем бота
updater.start_polling()
