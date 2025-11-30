import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.main import run_pipeline
from data.db import get_all_sneakers
from app.log import print_log

API_TOKEN = '8412343796:AAEkyiQSdWuQgYKMSp4trAhYCvUlOJQpjpY'
bot = telebot.TeleBot(API_TOKEN)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEXTS_DIR = os.path.join(BASE_DIR, "..", "data", "product_texts")
IMAGES_DIR = os.path.join(BASE_DIR, "..", "media")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я твой бот, который отвечает на FAQ!")

@bot.message_handler(commands=['que'])
def que_user(message):
    bot.send_message(message.chat.id, 'Введите вопрос, который вас интересует')
    bot.register_next_step_handler(message, process_que)

def process_que(message):
    user_text = message.text
    result = run_pipeline(user_text=user_text)
    bot.send_message(message.chat.id, result)

@bot.message_handler(commands=['product'])
def product_review(message):
    items = get_all_sneakers()
    if not items:
        bot.send_message(message.chat.id, "Кроссовок пока нет")
        return

    markup = InlineKeyboardMarkup()
    for name, price in items:
        
        display_name = name.replace("_", " ")
        button_text = f"{display_name} — {price} ₽"
        
        markup.add(InlineKeyboardButton(button_text, callback_data=name))

    bot.send_message(message.chat.id, "Выберите кроссовки:", reply_markup=markup)


def send_product(chat_id, product_name):
    text_path = os.path.join(TEXTS_DIR, f"{product_name}.txt")
    image_path = os.path.join(IMAGES_DIR, f"{product_name}.png")

    print_log(level_log='info',text= f"Ищу текст: {text_path}, изображение: {image_path}")


    description = "Описание недоступно 😢"
    try:
        if os.path.exists(text_path):
            with open(text_path, "r", encoding="utf-8") as f:
                description = f.read()
        else:
            print_log(level_log='warning', text=f"Файл текста не найден: {text_path}")
    except Exception as e:
        print_log(level_log='error', text=f"Ошибка при чтении файла текста {text_path}: {e}")

    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as img:
                bot.send_photo(chat_id, img, caption=description)
        else:
            print_log(level_log='warning', text=f"Файл изображения не найден: {image_path}")
            bot.send_message(chat_id, description)
    except Exception as e:
        print_log(level_log='error', text=f"Ошибка при отправке изображения {image_path}: {e}")
        bot.send_message(chat_id, description)

def process_que_sneaker(message, product_name):
    user_text = message.text
    result = run_pipeline(user_text=user_text, product_name=product_name)
    bot.send_message(message.chat.id, result)


@bot.message_handler(commands=['que_sneakers'])
def que_snea(message):
    items = get_all_sneakers()
    if not items:
        bot.send_message(message.chat.id, "Кроссовок пока нет")
        return

    markup = InlineKeyboardMarkup()
    for name, price in items:
        display_name = name.replace("_", " ")
        button_text = f"{display_name} — {price} ₽"
        markup.add(InlineKeyboardButton(button_text, callback_data=f"QUE_{name}"))

    bot.send_message(message.chat.id, "Выберите кроссовки, про которые хотите задать вопрос:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    data = call.data

    if not data.startswith("QUE_"):
        send_product(call.message.chat.id, data)
        return

    product_name = data.replace("QUE_", "")
    bot.send_message(call.message.chat.id, f"Введите ваш вопрос про {product_name.replace('_', ' ')}:")
    bot.register_next_step_handler(call.message, lambda msg: process_que_sneaker(msg, product_name))


if __name__ == "__main__":
    print_log(level_log='info', text="[INFO] Бот запущен...")
    bot.polling(none_stop=True)

