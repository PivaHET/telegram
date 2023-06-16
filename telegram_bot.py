import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.ext import ConversationHandler
from telegram.ext import CallbackQueryHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import messagequeue as mq
from python_telegram_bot_menu import BotMenu, ButtonMenuState
from python_telegram_bot_menu.button_location import ButtonLocation
load_dotenv()
registered_users = []
pending_users = []
admin_user_id = int(os.getenv('ADMIN_USER_ID'))
chat_pairs = []
faq = """
Привет! Я бот для синхронизации чатов WhatsApp и Telegram.
Вот список доступных команд:
/start - Начать взаимодействие с ботом
/accept - Акцептировать ожидающего пользователя (только для администратора)
/add_pair - Добавить новую пару синхронизируемых чатов (только для зарегистрированных пользователей)
/help - Показать эту справку с инструкцией
"""
STATE_MAIN_MENU = 1
STATE_ADD_PAIR = 2
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
   if user_id == admin_user_id:
        context.bot.send_message(chat_id=user_id, text="Вы администратор бота.")
    else:
        context.bot.send_message(chat_id=user_id, text="Добро пожаловать! Ожидайте акцепции администратора.")
        pending_users.append(user_id)
def accept_user(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
      if user_id == admin_user_id:
        if len(pending_users) > 0:
            accepted_user_id = pending_users.pop(0)
            registered_users.append(accepted_user_id)
            context.bot.send_message(chat_id=accepted_user_id, text="Ваш аккаунт акцептирован.")
            context.bot.send_message(chat_id=user_id, text="Пользователь акцептирован.")
        else:
            context.bot.send_message(chat_id=user_id, text="Нет пользователей, ожидающих акцепции.")
    else:
        context.bot.send_message(chat_id=user_id, text="У вас нет прав на выполнение этой команды.")
def add_pair(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
       if user_id in registered_users:
        context.bot.send_message(chat_id=user_id, text="Введите пару синхронизируемых чатов в формате:\nWhatsApp Chat\nTelegram Chat")
        return STATE_ADD_PAIR
    else:
        context.bot.send_message(chat_id=user_id, text="Вам необходимо пройти регистрацию и акцепцию администратора.")
def add_pair_input(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    text = update.message.text
    pair = text.split('\n', 1)
    if     pair = text.split('\n', 1)
    if len(pair) == 2:
        whatsapp_chat = pair[0].strip()
        telegram_chat = pair[1].strip()
        chat_pairs.append((whatsapp_chat, telegram_chat))
        response = f"Новая пара синхронизируемых чатов добавлена:\nWhatsApp: {whatsapp_chat}\nTelegram: {telegram_chat}"
        context.bot.send_message(chat_id=user_id, text=response)
    else:
        context.bot.send_message(chat_id=user_id, text="Неверный формат ввода. Введите пару синхронизируемых чатов в формате:\nWhatsApp Chat\nTelegram Chat")
    return STATE_MAIN_MENU
def help_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    context.bot.send_message(chat_id=user_id, text=faq)
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
       if user_id in registered_users:
        text = update.message.text
        context.bot.send_message(chat_id=user_id, text="Сообщение получено: " + text)
    else:
        context.bot.send_message(chat_id=user_id, text="Вам необходимо пройти регистрацию и акцепцию администратора.")
def main() -> None:
    load_dotenv()
    telegram_bot_token = input("Введите API токен вашего Telegram-бота: ")
    admin_user_id = input("Введите ID администратора: ")
    os.environ['TELEGRAM_BOT_TOKEN'] = telegram_bot_token
    os.environ['ADMIN_USER_ID'] = admin_user_id
    updater = Updater(token=telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    accept_handler = CommandHandler('accept', accept_user)
    dispatcher.add_handler(accept_handler)
    add_pair_handler = CommandHandler('add_pair', add_pair)
    dispatcher.add_handler(add_pair_handler)
      help_handler = CommandHandler('help', help_command)
    dispatcher.add_handler(help_handler)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add_pair', add_pair)],
        states={
            STATE_MAIN_MENU: [
                CommandHandler('start', start),
                CommandHandler('accept', accept_user),
                CommandHandler('help', help_command),
                MessageHandler(Filters.text, handle_message)
            ],
            STATE_ADD_PAIR: [
                MessageHandler(Filters.text, add_pair_input)
            ]
        },
        fallbacks=[]
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()
if name == 'main':
    main()
