from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

def get_gender_keyboard():
    return ReplyKeyboardMarkup([['👩 Женский', '👨 Мужской']], 
                              resize_keyboard=True, one_time_keyboard=True)

def get_service_keyboard():
    return ReplyKeyboardMarkup([
        ['Сдача квартиры в аренду'],
        ['Съём квартиры'], 
        ['Покупка квартиры'],
        ['Покупка дома'],
        ['Продажа квартиры'],
        ['Продажа дома'],
        ['Флиппинг'],
        ['Хоумстейджинг'],
        ['Финансовые услуги']
    ], resize_keyboard=True, one_time_keyboard=True)

def get_likes_keyboard():
    return ReplyKeyboardMarkup([
        ['Скорость', 'Вежливость менеджера'],
        ['Прозрачность договора', 'Цена'],
        ['Стиль работы', '✅ Завершить выбор']
    ], resize_keyboard=True)

def get_recommendation_keyboard():
    return ReplyKeyboardMarkup([['✅ Да', '❌ Нет']], 
                              resize_keyboard=True, one_time_keyboard=True)

def get_confirmation_keyboard():
    return ReplyKeyboardMarkup([['✅ Да, все верно', '❌ Нет, исправить']], 
                              resize_keyboard=True, one_time_keyboard=True)

def get_skip_keyboard():
    return ReplyKeyboardMarkup([['Пропустить']], 
                              resize_keyboard=True, one_time_keyboard=True)

def get_platform_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🏢 Cian", url="https://spb.cian.ru/agents/74067131/#new"),
            InlineKeyboardButton("🏠 Domclick", url="https://agencies.domclick.ru/agent/8752?region_id=44eeae98-63fd-4b9d-9ba2-c7806d6b8d6e?utm_content=offers.agent")
        ],
        [
            InlineKeyboardButton("📬 Telegram", url="t.me/demyanov_agency"),
            InlineKeyboardButton("🔗 ВК", url="https://vk.com/ipoteka9367573")
        ]
    ])
    ])
