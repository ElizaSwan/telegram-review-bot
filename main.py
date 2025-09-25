import os
import logging
import asyncio
import sqlite3
import json
from dotenv import load_dotenv

# Загрузка .env файла
load_dotenv()

# Получение переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')

# Проверка переменных
print("=" * 60)
print("🔍 ЗАГРУЖЕННЫЕ ПЕРЕМЕННЫЕ ИЗ .env:")
print(f"✅ TELEGRAM_BOT_TOKEN: {TELEGRAM_BOT_TOKEN}")
print(f"✅ YANDEX_API_KEY: {YANDEX_API_KEY}")
print(f"✅ YANDEX_FOLDER_ID: {YANDEX_FOLDER_ID}")
print("=" * 60)

# Теперь импорты из telegram (ПОСЛЕ переменных!)
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from yagpt_client import yagpt_client
import keyboards as kb

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния разговора
GENDER, SERVICE, LIKES, COMMENT, RECOMMENDATION, FINAL_CONFIRMATION = range(6)

# База данных
class DatabaseManager:
    def __init__(self, db_path='reviews.db'):
        self.db_path = db_path
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_name TEXT,
                gender TEXT,
                service TEXT,
                likes TEXT,
                recommendation TEXT,
                comment TEXT,
                generated_review TEXT,
                date_created DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def save_review(self, user_id, user_name, gender, service, likes, recommendation, comment, generated_review):
        likes_json = json.dumps(likes, ensure_ascii=False)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reviews (user_id, user_name, gender, service, likes, recommendation, comment, generated_review)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, user_name, gender, service, likes_json, recommendation, comment, generated_review))
        conn.commit()
        conn.close()

db_manager = DatabaseManager()

# Обработчики команд
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    # Вступительное сообщение
    welcome_text = (
        "*Добро пожаловать в сервис отзывов! 💖*\n\n"
    "Спасибо, что нашли время оставить отзыв о нашей работе. Это займет всего 2 минуты.\n\n"
    "Если захотите прервать опрос, просто напишите /cancel"
    )

    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )

    # Ждем немного и задаем первый вопрос
    await asyncio.sleep(1)
    await update.message.reply_text(
        "👥 Какого вы пола?",
        reply_markup=kb.get_gender_keyboard()
    )
    return GENDER

async def handle_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text
    valid_genders = ['👩 Женский', '👨 Мужской', 'Женский', 'Мужской']

    if user_answer not in valid_genders:
        await update.message.reply_text(
            "Пожалуйста, выберите пол с помощью кнопок 👇",
            reply_markup=kb.get_gender_keyboard()
        )
        return GENDER

    context.user_data['gender'] = user_answer
    await update.message.reply_text(
        "🏢 Какую услугу вы получили?",
        reply_markup=kb.get_service_keyboard()
    )
    return SERVICE

async def handle_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text
    valid_services = ['Сдача квартиры в аренду', 'Съём квартиры', 'Покупка квартиры', 
                     'Покупка дома', 'Продажа квартиры', 'Продажа дома', 
                     'Флиппинг', 'Хоумстейджинг', 'Финансовые услуги']

    if user_answer not in valid_services:
        await update.message.reply_text(
            "Пожалуйста, выберите услугу с помощью кнопок 👇",
            reply_markup=kb.get_service_keyboard()
        )
        return SERVICE

    context.user_data['service'] = user_answer
    context.user_data['likes'] = []

    await update.message.reply_text(
        "⭐ Что вам понравилось в работе с нашим агентством?\n\n"
        "Можно выбрать несколько вариантов. Нажмите '✅ Завершить выбор' когда закончите.",
        reply_markup=kb.get_likes_keyboard()
    )
    return LIKES

async def handle_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text
    valid_likes = ['Скорость', 'Вежливость менеджера', 'Прозрачность договора', 
                  'Цена', 'Стиль работы', '✅ Завершить выбор']

    if user_answer not in valid_likes:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки для выбора 👇",
            reply_markup=kb.get_likes_keyboard()
        )
        return LIKES

    if user_answer == '✅ Завершить выбор':
        if not context.user_data['likes']:
            await update.message.reply_text(
                "Пожалуйста, выберите хотя бы один вариант перед завершением 👇",
                reply_markup=kb.get_likes_keyboard()
            )
            return LIKES

        await update.message.reply_text(
            "💬 Хотите добавить комментарий или уточнение к отзыву?\n\n"
            "Напишите ваш комментарий или нажмите 'Пропустить'",
            reply_markup=kb.get_skip_keyboard()
        )
        return COMMENT

    if user_answer in context.user_data['likes']:
        context.user_data['likes'].remove(user_answer)
        action = "убрано"
    else:
        context.user_data['likes'].append(user_answer)
        action = "добавлено"

    selected_text = ", ".join(context.user_data['likes']) if context.user_data['likes'] else "пока ничего не выбрано"

    await update.message.reply_text(
        f"{user_answer} {action} ✅\n\n"
        f"Выбрано: {selected_text}\n\n"
        "Продолжайте выбирать или нажмите '✅ Завершить выбор'",
        reply_markup=kb.get_likes_keyboard()
    )
    return LIKES

async def handle_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text

    if user_answer == 'Пропустить':
        context.user_data['comment'] = ""
    else:
        context.user_data['comment'] = user_answer

    await update.message.reply_text(
        "🤝 Посоветуете своим знакомым наше агентство?",
        reply_markup=kb.get_recommendation_keyboard()
    )
    return RECOMMENDATION

async def handle_recommendation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text

    if user_answer not in ['✅ Да', '❌ Нет']:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки для ответа 👇",
            reply_markup=kb.get_recommendation_keyboard()
        )
        return RECOMMENDATION

    context.user_data['recommendation'] = user_answer

    # Показываем сводку
    summary_text = "📋 Проверьте ваши ответы:\n\n"
    summary_text += f"👥 Пол: {context.user_data['gender']}\n"
    summary_text += f"🏢 Услуга: {context.user_data['service']}\n"
    summary_text += f"⭐ Понравилось: {', '.join(context.user_data['likes'])}\n"
    if context.user_data.get('comment'):
        summary_text += f"💬 Комментарий: {context.user_data['comment']}\n"
    summary_text += f"🤝 Рекомендация: {context.user_data['recommendation']}\n\n"
    summary_text += "Всё верно?"

    await update.message.reply_text(
        summary_text,
        reply_markup=kb.get_confirmation_keyboard()
    )
    return FINAL_CONFIRMATION

async def handle_final_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text

    if user_answer not in ['✅ Да, все верно', '❌ Нет, исправить']:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки для ответа 👇",
            reply_markup=kb.get_confirmation_keyboard()
        )
        return FINAL_CONFIRMATION

    if user_answer == '✅ Да, все верно':
        await update.message.reply_text(
            "✨ Генерируем ваш отзыв с помощью AI...\n\nЭто займет 10-15 секунд.",
            reply_markup=ReplyKeyboardRemove()
        )

        # Генерируем отзыв с помощью YaGPT
        generated_review = await yagpt_client.generate_review(
            context.user_data['gender'],
            context.user_data['service'],
            context.user_data['likes'],
            context.user_data['recommendation'],
            context.user_data.get('comment', '')
        )

        # Fallback если YaGPT не сработал
        if not generated_review:
            generated_review = (
                f"Хочу поблагодарить Demyanov realty за {context.user_data['service'].lower()}! "
                f"Особенно понравилось: {', '.join(context.user_data['likes'])}. "
                f"{'Обязательно порекомендую ваше агентство!' if context.user_data['recommendation'] == '✅ Да' else 'Спасибо за работу!'}"
            )

        # Сохраняем в базу
        user_id = update.message.from_user.id
        user_name = update.message.from_user.username or update.message.from_user.first_name

        db_manager.save_review(
            user_id, user_name,
            context.user_data['gender'],
            context.user_data['service'],
            context.user_data['likes'],
            context.user_data['recommendation'],
            context.user_data.get('comment', ''),
            generated_review
        )

        # Финальное сообщение с инструкциями
        final_message = (
            f"🎉 Готово! Вот ваш отзыв:\n\n"
            f"`{generated_review}`\n\n"
            f"💖 Большое спасибо! Ваше мнение очень важно для нас.\n\n"
            f"**🚀 А теперь отзыв нужно непременно опубликовать!** 😊\n\n"
            f"📋 *Как это сделать:*\n\n"
            f"1. 🏢 Выберите площадку, на которой состоялась сделка\n"
            f"2. 🔍 Найдите на странице кнопку \"Написать отзыв\"\n"  
            f"3. 🔐 Войдите в аккаунт, если требуется\n"
            f"4. 📋 Скопируйте получившийся текст (просто нажмите на него в этом сообщении), вставьте в соответствующее окошко и опубликуйте отзыв\n\n"
            f"**⭐️ Ещё раз благодарим вас!** 🙏"
        )

        await update.message.reply_text(
            final_message,
            parse_mode='Markdown',
            reply_markup=kb.get_platform_keyboard()
        )

        await update.message.reply_text(
            "Хотите оставить еще один отзыв? Напишите /start"
        )

    else:
        await update.message.reply_text(
            "Хорошо, давайте начнем заново.",
            reply_markup=ReplyKeyboardRemove()
        )
        await update.message.reply_text("Напишите /start")

    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Опрос прерван. Если у вас есть время оставить отзыв позже, просто напишите /start",
        reply_markup=ReplyKeyboardRemove()
    )
    context.user_data.clear()
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text(
            "⚠️ Произошла ошибка. Давайте начнем заново. Напишите /start",
            reply_markup=ReplyKeyboardRemove()
        )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Тестовая команда для проверки YaGPT"""
    test_review = await yagpt_client.generate_review(
        "👩 Женский", "Покупка квартиры", ["Скорость"], "✅ Да", "Тестовый комментарий"
    )

    if test_review:
        await update.message.reply_text(f"✅ YaGPT работает! Тестовый отзыв:\n\n{test_review}")
    else:
        await update.message.reply_text("❌ YaGPT не отвечает. Проверьте настройки.")

# Основная функция
def main():
    # Проверка переменных
    if not all([TELEGRAM_BOT_TOKEN, YANDEX_API_KEY, YANDEX_FOLDER_ID]):
        logger.error("Не все переменные окружения установлены!")
        logger.error(f"Telegram Token: {'SET' if TELEGRAM_BOT_TOKEN else 'MISSING'}")
        logger.error(f"Yandex API Key: {'SET' if YANDEX_API_KEY else 'MISSING'}")
        logger.error(f"Yandex Folder ID: {'SET' if YANDEX_FOLDER_ID else 'MISSING'}")
        return

    # Инициализация базы данных
    db_manager.init_database()

    # Создаем приложение
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Добавляем обработчики
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_gender)],
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_service)],
            LIKES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_likes)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_comment)],
            RECOMMENDATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_recommendation)],
            FINAL_CONFIRMATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_final_confirmation)]
        },
        fallbacks=[CommandHandler('cancel', cancel), CommandHandler('test', test_command)]
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    # Запускаем бота
    logger.info("🚀 Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    main()
