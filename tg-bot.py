import logging
from os import environ

import psycopg2
from telegram import Update, MenuButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

TELEGRAM_TOKEN = environ.get('TELEGRAM_TOKEN')

DB_HOST = environ.get('DB_HOST')
DB_NAME = environ.get('DB_NAME')
DB_USER = environ.get('DB_USER')
DB_PASS = environ.get('DB_PASS')

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Функция для подключения к базе данных
def get_db_connection():
    return psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f'Добро пожаловать в Vadimka_coin, {user.username}! Нажмите play для начала тыкания).')

# Команда /click
async def click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT \"ID\", \"score\" FROM \"score\" WHERE \"ID_user\" = %s", (user_id,))
                result = cursor.fetchone()


                if result is None:
                    cursor.execute("INSERT INTO \"score\" (\"ID_user\", \"score\") VALUES (%s, %s)", (user_id, 1))
                    click_count = 1
                else:
                    click_count = result[0] + 1
                    cursor.execute("UPDATE score SET \"score\" = \"score\" WHERE \"ID_user\" = %s", (click_count, user_id,))

                conn.commit()

        await update.message.reply_text(f'Вы кликнули! Общее количество кликов: {click_count}')
    except Exception as e:
        logger.error(f"Ошибка при обработке клика: {e}")
        await update.message.reply_text('Произошла ошибка. Попробуйте позже.')

# Команда /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT \"score\" FROM \"score\" WHERE \"ID_user\" = %s", (user_id,))
                result = cursor.fetchone()

                if result is None:
                    await update.message.reply_text('У вас пока нет кликов.')
                else:
                    click_count = result[0]
                    await update.message.reply_text(f'Ваше общее количество кликов: {click_count}')
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await update.message.reply_text('Произошла ошибка. Попробуйте позже.')

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('click', click))
    application.add_handler(CommandHandler('stats', stats))

    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()