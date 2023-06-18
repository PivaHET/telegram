import os
from telegram import Bot
from telegram import Update
from telegram.ext import Updater
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.utils.request import Request

request = Request(con_pool_size=8)
bot = Bot(token=telegram_bot_token, request=request)
update_queue = Queue()  # Use Queue from queue or multiprocessing if needed
update = Update(update_id=0, message=None)  # Create an Update object to be put in the queue
update_queue.put(update)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello World')

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

updater = Updater(bot=bot, update_queue=update_queue, use_context=True)
updater.start_polling()

# Загрузка переменных окружения из файла .env
load_dotenv('APA.env')

# Получение переменных окружения
telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
admin_user_id = os.getenv('ADMIN_USER_ID')

# Проверка наличия переменных окружения
if not telegram_bot_token or not admin_user_id:
    raise ValueError("Отсутствуют необходимые переменные окружения")

# Преобразование admin_user_id в int
admin_user_id = int(admin_user_id)

# Инициализация списков пользователей
registered_users = []
pending_users = []
chat_pairs = []

# Определение состояний беседы
STATE_MAIN_MENU = 1
STATE_ADD_PAIR = 2

# Обработка входящих сообщений
def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    if user_id in registered_users:
        text = update.message.text
        context.bot.send_message(chat_id=user_id, text=f"Вы сказали: {text}")
    else:
        context.bot.send_message(chat_id=user_id, text="Вы не зарегистрированы.")

# Команда start
def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    if user_id == admin_user_id:
        context.bot.send_message(chat_id=user_id, text="Привет, админ!")
    else:
        context.bot.send_message(chat_id=user_id, text="Вы не зарегистрированы. Запрос на регистрацию отправлен админу.")
        pending_users.append(user_id)

# Команда принятия пользователя
def accept_user(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    if user_id == admin_user_id:
        if len(pending_users) > 0:
            accepted_user_id = pending_users.pop(0)
            registered_users.append(accepted_user_id)
            context.bot.send_message(chat_id=accepted_user_id, text="Вы теперь зарегистрированы.")
            context.bot.send_message(chat_id=user_id, text="Пользователь был зарегистрирован.")
        else:
            context.bot.send_message(chat_id=user_id, text="Нет пользователей для регистрации.")
    else:
        context.bot.send_message(chat_id=user_id, text="Вы не админ.")

# Команда добавления пары
def add_pair(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id

    if user_id in registered_users:
        context.bot.send_message(chat_id=user_id, text="Пожалуйста, введите пару чатов в формате:\nWhatsApp Чат\nTelegram Чат")
        return STATE_ADD_PAIR
    else:
        context.bot.send_message(chat_id=user_id, text="Вы не зарегистрированы.")

# Ввод пары
def add_pair_input(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    text = update.message.text

    pair = text.split('\n', 1)

    if len(pair) == 2:
        whatsapp_chat = pair[0].strip()
        telegram_chat = pair[1].strip()

        chat_pairs.append((whatsapp_chat, telegram_chat))

        response = f"Пара чатов добавлена:\nWhatsApp: {whatsapp_chat}\nTelegram: {telegram_chat}"
        context.bot.send_message(chat_id=user_id, text=response)
    else:
        context.bot.send_message(chat_id=user_id, text="Неверный формат. Введите пару чатов в формате:\nWhatsApp Чат\nTelegram Чат")

    return STATE_MAIN_MENU

# Основная функция
def main() -> None:
    load_dotenv('APA.env')

    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    admin_user_id_env = os.getenv('ADMIN_USER_ID')
    admin_user_id = int(admin_user_id_env)

    updater = Updater(telegram_bot_token, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    accept_handler = CommandHandler('accept', accept_user)
    dispatcher.add_handler(accept_handler)

    add_pair_handler = CommandHandler('add_pair', add_pair)
    dispatcher.add_handler(add_pair_handler)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add_pair', add_pair)],
        states={
            STATE_MAIN_MENU: [
                CommandHandler('start', start),
                CommandHandler('accept', accept_user),
                MessageHandler(Filters.text & ~Filters.command, handle_message)
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

if __name__ == '__main__':
    main()
