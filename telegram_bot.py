import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.ext import ConversationHandler
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import messagequeue as mq

load_dotenv()

# Пользователи, зарегистрированные и принятые администратором
registered_users = []
# Пользователи, которые начали взаимодействие, но ещё не приняты администратором
pending_users = []
# ID администратора берется из переменных окружения
admin_user_id = int(os.getenv('ADMIN_USER_ID'))
# Список пар чатов для синхронизации
chat_pairs = []

# Структура конечного автомата для обработки ввода пользователя
STATE_MAIN_MENU = 1
STATE_ADD_PAIR = 2

# Стартовая команда. Регистрирует пользователя.
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if user_id == admin_user_id:
        context.bot.send_message(chat_id=user_id, text="Вы администратор бота.")
    else:
        context.bot.send_message(chat_id=user_id, text="Добро пожаловать! Ожидайте акцепции администратора.")
        pending_users.append(user_id)

# Акцепция пользователя админ
def accept_user(update: Update,) -> None:
    user_id = update.effective_user.id
    
    # Проверка на администратора
    if user_id == admin_user_id:
        # Проверка на наличие ожидающих пользователей
        if len(pending_users) > 0:
            # Принимаем пользователя
            accepted_user_id = pending_users.pop(0)
            registered_users.append(accepted_user_id)
            # Уведомляем пользователя о принятии
            context.bot.send_message(chat_id=accepted_user_id, text="Ваш аккаунт акцептирован.")
            context.bot.send_message(chat_id=user_id, text="Пользователь акцептирован.")
        else:
            context.bot.send_message(chat_id=user_id, text="Нет пользователей, ожидающих акцепции.")
    else:
        context.bot.send_message(chat_id=user_id, text="У вас нет прав на выполнение этой команды.")

# Добавление пары синхронизируемых чатов
def add_pair(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    # Проверка, что пользователь зарегистрирован
    if user_id in registered_users:
        context.bot.send_message(chat_id=user_id, text="Введите пару синхронизируемых чатов в формате:\nWhatsApp Chat\nTelegram Chat")
        return STATE_ADD_PAIR
    else:
        context.bot.send_message(chat_id=user_id, text="Вам необходимо пройти регистрацию и акцепцию администратора.")

# Обработка ввода пользователя при добавлении пары чатов
def add_pair_input(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    text = update.message.text

    # Разделение ввода на два чата
    pair = text.split('\n', 1)

    if len(pair) == 2:
        # Обработка и добавление пары чатов
        whatsapp_chat = pair[0].strip()
        telegram_chat = pair[1].strip()

        chat_pairs.append((whatsapp_chat, telegram_chat))

        # Уведомляем пользователя о добавлении пары чатов
        response = f"Новая пара синхронизируемых чатов добавлена:\nWhatsApp: {whatsapp_chat}\nTelegram: {telegram_chat}"
        context.bot.send_message(chat_id=user_id, text=response)
    else:
        context.bot.send_message(chat_id=user_id, text="Неверный формат ввода. Введите пару синхронизируемых чатов в формате:\nWhatsApp Chat\nTelegram Chat")

    return STATE_MAIN_MENU

# Обработка сообщений
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    
    if user_id in registered_users:
        text = update.message.text
        context.bot.send_message(chat_id=user_id, text="Сообщение получено: " + text)
    else:
        context.bot.send_message(chat_id=user_id, text="Вам необходимо пройти регистрацию и акцепцию администратора.")

# Главная функция, запускающая бота
def main() -> None:
    # Загрузка переменных окружения
    load_dotenv()

    # Получение токена бота и ID администратора
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    admin_user_id = os.getenv('ADMIN_USER_ID') 

    # Создание объектов обновления и диспетчера
    updater = Updater(token=telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Регистрация обработчиков команд
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    accept_handler = CommandHandler('accept', accept_user)
    dispatcher.add_handler(accept_handler)

    add_pair_handler = CommandHandler('add_pair', add_pair)
    dispatcher.add_handler(add_pair_handler)
    
    # Создание конверсационного обработчика для добавления пар чатов
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add_pair', add_pair)],
        states={
            STATE_MAIN_MENU: [
                CommandHandler('start', start),
                CommandHandler('accept', accept_user),
                MessageHandler(Filters.text, handle_message)
            ],
            STATE_ADD_PAIR: [
                MessageHandler(Filters.text, add_pair_input)
            ]
        },
        fallbacks=[]
    )
    dispatcher.add_handler(conv_handler)

    # Начало опроса обновлений
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()


