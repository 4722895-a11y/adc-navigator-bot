"""
Telegram-бот «Навигатор ADC» — публичный бот для канала
Версия: 3.0 (с приветственной анкетой и розыгрышем)
Дата: 28.01.2026
ООО «МИРИНГ ГРУП»

ФУНКЦИОНАЛ:
- Приветственная анкета для новых подписчиков
- Сбор информации о проектах
- Сбор предпочтений по контенту канала
- Розыгрыш эскизного проекта
- Информация о компании
- Категории услуг
- Форма заявки с файлами
- Вопрос техническому специалисту
"""

import os
import json
import logging
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============== НАСТРОЙКИ ==============
MANAGER_CHAT_ID = os.environ.get("MANAGER_CHAT_ID", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")  # Для уведомлений о лидах

# Ссылки
SITE_URL = "https://arxproektstroy.ru"
PORTFOLIO_URL = "https://drive.google.com/file/d/1gj0bPzw36cJMR413GEoRHoGSUjQKD29_/view"
CHANNEL_URL = "https://t.me/ADC_Project"

# Файл для хранения данных пользователей
USERS_FILE = "bot_users.json"

# Состояния для ConversationHandler
# Приветственная анкета (SURVEY_*)
(SURVEY_HAS_PROJECT, SURVEY_OBJECT_TYPE, SURVEY_AREA, SURVEY_REGION, 
 SURVEY_REGION_TEXT, SURVEY_TIMELINE, SURVEY_INTERESTS, SURVEY_GIVEAWAY_CONTACT) = range(8)

# Форма заявки (REQUEST_*)
(REQUEST_REGION, REQUEST_OBJECT_TYPE, REQUEST_OBJECT_TYPE_CUSTOM, REQUEST_AREA, 
 REQUEST_STAGE, REQUEST_SERVICE, REQUEST_BIM, REQUEST_SURVEY, REQUEST_TIMELINE, 
 REQUEST_COMMENT, REQUEST_FILES, REQUEST_CONTACT, TECH_QUESTION) = range(8, 21)


# ============== ХРАНЕНИЕ ДАННЫХ ==============
def load_users() -> dict:
    """Загрузка данных пользователей"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_users(users: dict) -> None:
    """Сохранение данных пользователей"""
    try:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {e}")


def save_user_data(user_id: int, data: dict) -> None:
    """Сохранение данных одного пользователя"""
    users = load_users()
    users[str(user_id)] = data
    save_users(users)
    logger.info(f"User data saved: {user_id}")


def get_user_data(user_id: int) -> dict:
    """Получение данных пользователя"""
    users = load_users()
    return users.get(str(user_id), {})


def is_new_user(user_id: int) -> bool:
    """Проверка, новый ли пользователь"""
    users = load_users()
    return str(user_id) not in users


# ============== ИНФОРМАЦИЯ О КОМПАНИИ ==============
COMPANY_INFO = """🏢 ADC Group (ООО «МИРИНГ ГРУП»)

Федеральная инженерно-проектная группа полного цикла.

📊 Ключевые показатели:
• 26 лет на рынке
• 1500+ реализованных проектов
• 80+ специалистов в штате
• 200+ партнёрских организаций
• 18+ регионов России
• BIM-технологии с 2018 года

🏆 Знаковые заказчики:
Лукойл, Сбербанк, Газпром, ПИК, X5 Retail, РЖД, Магнит, Правительство Москвы

🌐 Сайт: arxproektstroy.ru
📞 Мобильный: +7 939 111 30 42
📞 Городской: 8 (495) 118-34-88
📧 Email: info@arxproektstroy.ru"""


SERVICES_INFO = """📐 УСЛУГИ ADC Group

1. Проектирование
• Эскизный проект
• АГР/АГО (архитектурно-градостроительный облик)
• Проектная документация (стадия П)
• Рабочая документация (стадия РД)
• BIM-моделирование

2. Сопровождение
• Прохождение экспертизы
• Получение разрешения на строительство
• Авторский надзор
• Функции технического заказчика

3. Инженерные изыскания
• Геодезические
• Геологические
• Экологические

4. Строительство
• СМР по собственным проектам
• Комплексное строительство под ключ

📋 Для расчёта сроков и стоимости — оставьте заявку"""


OBJECT_TYPES = """🏗 ТИПЫ ОБЪЕКТОВ

Проектируем коммерческие объекты любого назначения:

Промышленность и логистика:
• Склады и логистические центры
• Производственные здания
• Заводы и фабрики

Торговля и офисы:
• Торговые центры
• Бизнес-центры
• Магазины и ритейл

Социальные объекты:
• Медицинские учреждения
• Образовательные учреждения
• Спортивные объекты

Жильё и гостиницы:
• Многоквартирные дома
• Гостиницы и санатории
• Апарт-отели

Инфраструктура:
• Наружные сети
• Благоустройство
• Дороги и площадки"""


PORTFOLIO_INFO = """📁 ПОРТФОЛИО ADC Group

Более 200 объектов в активном портфолио.

🔗 Посмотреть портфолио:
{portfolio_url}

🔗 Выполненные проекты на сайте:
https://arxproektstroy.ru/proekty

📊 Статистика:
• 140+ крупных объектов
• 800+ млн руб. контрактов
• 87% экспертиз с первого раза
• Гарантия 3 года на все работы""".format(portfolio_url=PORTFOLIO_URL)


GIVEAWAY_INFO = """🎁 РОЗЫГРЫШ

Разыгрываем бесплатный эскизный проект стоимостью от 150 000 ₽.

Что получит победитель:
→ Концептуальные планировки
→ Фасадные решения
→ Предварительные ТЭП
→ 3D-визуализация

Итоги: 28 февраля 2026 года

Подробности в канале @ADC_Project"""


# ============== КЛАВИАТУРЫ ==============
def get_main_keyboard():
    """Главное меню"""
    keyboard = [
        [InlineKeyboardButton("🏢 О компании", callback_data="company")],
        [InlineKeyboardButton("📐 Услуги", callback_data="services")],
        [InlineKeyboardButton("🏗 Типы объектов", callback_data="objects")],
        [InlineKeyboardButton("📁 Портфолио", callback_data="portfolio")],
        [InlineKeyboardButton("📝 Оставить заявку", callback_data="request")],
        [InlineKeyboardButton("❓ Задать вопрос специалисту", callback_data="tech_question")],
        [InlineKeyboardButton("🎁 Розыгрыш", callback_data="giveaway_info")],
        [InlineKeyboardButton("📢 Канал ADC Group", url=CHANNEL_URL)],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard():
    """Кнопка возврата в меню"""
    keyboard = [[InlineKeyboardButton("◀️ Главное меню", callback_data="menu")]]
    return InlineKeyboardMarkup(keyboard)


def get_request_keyboard():
    """Кнопки после просмотра информации"""
    keyboard = [
        [InlineKeyboardButton("📝 Оставить заявку", callback_data="request")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_survey_start_keyboard():
    """Клавиатура для начала анкеты — есть ли проект"""
    keyboard = [
        [InlineKeyboardButton("Да, есть проект", callback_data="survey_yes")],
        [InlineKeyboardButton("Пока нет, просто смотрю", callback_data="survey_no")],
        [InlineKeyboardButton("Пропустить", callback_data="survey_skip")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_object_type_keyboard():
    """Клавиатура выбора типа объекта"""
    keyboard = [
        [InlineKeyboardButton("Склад / логистика", callback_data="obj_warehouse")],
        [InlineKeyboardButton("Производство", callback_data="obj_production")],
        [InlineKeyboardButton("Офис / БЦ", callback_data="obj_office")],
        [InlineKeyboardButton("Торговый центр", callback_data="obj_retail")],
        [InlineKeyboardButton("Гостиница / апартаменты", callback_data="obj_hotel")],
        [InlineKeyboardButton("Медицина / социальное", callback_data="obj_medical")],
        [InlineKeyboardButton("Жильё / МЖД", callback_data="obj_residential")],
        [InlineKeyboardButton("Другое", callback_data="obj_other")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_area_keyboard():
    """Клавиатура выбора площади"""
    keyboard = [
        [InlineKeyboardButton("до 1 000 м²", callback_data="area_1000")],
        [InlineKeyboardButton("1 000 – 5 000 м²", callback_data="area_5000")],
        [InlineKeyboardButton("5 000 – 10 000 м²", callback_data="area_10000")],
        [InlineKeyboardButton("10 000 – 30 000 м²", callback_data="area_30000")],
        [InlineKeyboardButton("более 30 000 м²", callback_data="area_30000plus")],
        [InlineKeyboardButton("Пока не определена", callback_data="area_unknown")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_region_keyboard():
    """Клавиатура выбора региона"""
    keyboard = [
        [InlineKeyboardButton("Москва", callback_data="region_moscow")],
        [InlineKeyboardButton("Московская область", callback_data="region_mo")],
        [InlineKeyboardButton("Санкт-Петербург / ЛО", callback_data="region_spb")],
        [InlineKeyboardButton("Другой регион", callback_data="region_other")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_timeline_keyboard():
    """Клавиатура выбора сроков"""
    keyboard = [
        [InlineKeyboardButton("Уже ищем подрядчика", callback_data="time_now")],
        [InlineKeyboardButton("В ближайшие 1-3 месяца", callback_data="time_3m")],
        [InlineKeyboardButton("В этом году", callback_data="time_year")],
        [InlineKeyboardButton("Пока изучаю вопрос", callback_data="time_later")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_interests_keyboard():
    """Клавиатура выбора интересов по каналу"""
    keyboard = [
        [InlineKeyboardButton("Изменения в законодательстве", callback_data="int_law")],
        [InlineKeyboardButton("Разборы кейсов и ошибок", callback_data="int_cases")],
        [InlineKeyboardButton("Стоимость проектирования", callback_data="int_cost")],
        [InlineKeyboardButton("BIM и цифровизация", callback_data="int_bim")],
        [InlineKeyboardButton("Экспертиза и согласования", callback_data="int_expertise")],
        [InlineKeyboardButton("Господдержка и субсидии", callback_data="int_support")],
        [InlineKeyboardButton("✅ Готово", callback_data="int_done")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_giveaway_keyboard():
    """Клавиатура участия в розыгрыше"""
    keyboard = [
        [InlineKeyboardButton("Да, участвую", callback_data="giveaway_yes")],
        [InlineKeyboardButton("Нет, спасибо", callback_data="giveaway_no")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============== УВЕДОМЛЕНИЕ АДМИНУ ==============
async def notify_admin_lead(context: ContextTypes.DEFAULT_TYPE, user_data: dict) -> None:
    """Отправка уведомления администратору о новом лиде"""
    admin_id = ADMIN_CHAT_ID or MANAGER_CHAT_ID
    if not admin_id:
        return
    
    try:
        if user_data.get('has_project'):
            message = (
                "📋 НОВАЯ ЗАЯВКА ИЗ БОТА!\n\n"
                f"👤 {user_data.get('full_name', 'Пользователь')} "
                f"(@{user_data.get('username', 'нет')})\n"
                f"🆔 ID: {user_data.get('user_id')}\n\n"
                f"📦 Объект: {user_data.get('object_type', '—')}\n"
                f"📐 Площадь: {user_data.get('area', '—')}\n"
                f"📍 Регион: {user_data.get('region', '—')}\n"
                f"⏰ Сроки: {user_data.get('timeline', '—')}\n\n"
                f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
        else:
            interests = user_data.get('interests', [])
            message = (
                "👤 НОВЫЙ ПОДПИСЧИК\n\n"
                f"👤 {user_data.get('full_name', 'Пользователь')} "
                f"(@{user_data.get('username', 'нет')})\n"
                f"🆔 ID: {user_data.get('user_id')}\n\n"
                f"📋 Проект: нет\n"
                f"📌 Интересы: {', '.join(interests) if interests else '—'}\n"
                f"🎁 Розыгрыш: {'да' if user_data.get('giveaway_participant') else 'нет'}\n\n"
                f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
        
        await context.bot.send_message(chat_id=admin_id, text=message)
        logger.info(f"Admin notified about user {user_data.get('user_id')}")
        
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")


# ============== КОМАНДА /START ==============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Команда /start — приветствие и анкета для новых пользователей"""
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name or "Здравствуйте"
    
    # Инициализируем данные пользователя в контексте
    context.user_data['user_id'] = user_id
    context.user_data['username'] = user.username or ""
    context.user_data['full_name'] = user.full_name or ""
    context.user_data['first_contact'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context.user_data['interests'] = []
    
    # Проверяем, новый ли пользователь
    if is_new_user(user_id):
        # Новый пользователь — показываем анкету
        text = f"""👋 {user_name}, добро пожаловать!

Я — навигатор канала ADC Group.

Помогу узнать о компании, услугах и оставить заявку на консультацию.

Но сначала — короткий вопрос:

Есть ли у вас планируемый объект для строительства или задача на проектирование?"""
        
        await update.message.reply_text(
            text,
            reply_markup=get_survey_start_keyboard()
        )
        return SURVEY_HAS_PROJECT
    
    else:
        # Существующий пользователь — сразу меню
        text = f"""👋 С возвращением, {user_name}!

Выберите интересующий раздел:"""
        
        await update.message.reply_text(
            text,
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help — справка"""
    text = """📚 СПРАВКА

Команды:
/start — главное меню
/help — эта справка
/request — оставить заявку
/giveaway — информация о розыгрыше

Разделы меню:
• О компании — информация об ADC Group
• Услуги — перечень услуг
• Типы объектов — что проектируем
• Портфолио — примеры работ
• Оставить заявку — форма для связи
• Розыгрыш — участие в розыгрыше эскизного проекта

Контакты:
📞 Мобильный: +7 939 111 30 42
📞 Городской: 8 (495) 118-34-88
📧 info@arxproektstroy.ru
🌐 arxproektstroy.ru"""
    
    await update.message.reply_text(text)


async def giveaway_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /giveaway — информация о розыгрыше"""
    await update.message.reply_text(
        GIVEAWAY_INFO,
        reply_markup=get_back_keyboard()
    )


# ============== ПРИВЕТСТВЕННАЯ АНКЕТА ==============
async def survey_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка кнопок приветственной анкеты"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # === Есть ли проект ===
    if data == "survey_yes":
        context.user_data['has_project'] = True
        
        await query.edit_message_text(
            "Отлично! Расскажите коротко о проекте.\n\n"
            "Какой тип объекта?",
            reply_markup=get_object_type_keyboard()
        )
        return SURVEY_OBJECT_TYPE
    
    elif data == "survey_no":
        context.user_data['has_project'] = False
        
        await query.edit_message_text(
            "Понял. Тогда один вопрос про канал:\n\n"
            "Какие темы вам интересны? Выберите и нажмите «Готово»:",
            reply_markup=get_interests_keyboard()
        )
        return SURVEY_INTERESTS
    
    elif data == "survey_skip":
        # Сохраняем минимальные данные
        user_data = {
            'user_id': context.user_data.get('user_id'),
            'username': context.user_data.get('username'),
            'full_name': context.user_data.get('full_name'),
            'first_contact': context.user_data.get('first_contact'),
            'has_project': None,
            'survey_completed': False,
            'source': 'skip'
        }
        save_user_data(context.user_data.get('user_id'), user_data)
        
        await query.edit_message_text(
            "Хорошо! Если появятся вопросы — пишите.\n\n"
            "🎁 Кстати, у нас сейчас розыгрыш бесплатного эскизного проекта "
            "(от 150 000 ₽). Итоги 28 февраля.\n\n"
            "Выберите раздел:",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    # === Тип объекта ===
    elif data.startswith("obj_"):
        obj_types = {
            "obj_warehouse": "Склад / логистика",
            "obj_production": "Производство",
            "obj_office": "Офис / БЦ",
            "obj_retail": "Торговый центр",
            "obj_hotel": "Гостиница / апартаменты",
            "obj_medical": "Медицина / социальное",
            "obj_residential": "Жильё / МЖД",
            "obj_other": "Другое"
        }
        context.user_data['object_type'] = obj_types.get(data, "Не указано")
        
        await query.edit_message_text(
            f"✅ Тип объекта: {context.user_data['object_type']}\n\n"
            "Примерная площадь объекта?",
            reply_markup=get_area_keyboard()
        )
        return SURVEY_AREA
    
    # === Площадь ===
    elif data.startswith("area_"):
        areas = {
            "area_1000": "до 1 000 м²",
            "area_5000": "1 000 – 5 000 м²",
            "area_10000": "5 000 – 10 000 м²",
            "area_30000": "10 000 – 30 000 м²",
            "area_30000plus": "более 30 000 м²",
            "area_unknown": "Пока не определена"
        }
        context.user_data['area'] = areas.get(data, "Не указано")
        
        await query.edit_message_text(
            f"✅ Площадь: {context.user_data['area']}\n\n"
            "Регион строительства?",
            reply_markup=get_region_keyboard()
        )
        return SURVEY_REGION
    
    # === Регион ===
    elif data.startswith("region_"):
        if data == "region_other":
            await query.edit_message_text(
                "Напишите регион или город:"
            )
            return SURVEY_REGION_TEXT
        
        regions = {
            "region_moscow": "Москва",
            "region_mo": "Московская область",
            "region_spb": "Санкт-Петербург / ЛО"
        }
        context.user_data['region'] = regions.get(data, "Не указано")
        
        await query.edit_message_text(
            f"✅ Регион: {context.user_data['region']}\n\n"
            "Когда планируете начать проектирование?",
            reply_markup=get_timeline_keyboard()
        )
        return SURVEY_TIMELINE
    
    # === Сроки ===
    elif data.startswith("time_"):
        timelines = {
            "time_now": "Уже ищем подрядчика",
            "time_3m": "В ближайшие 1-3 месяца",
            "time_year": "В этом году",
            "time_later": "Пока изучаю вопрос"
        }
        context.user_data['timeline'] = timelines.get(data, "Не указано")
        
        # Сохраняем данные
        user_data = {
            'user_id': context.user_data.get('user_id'),
            'username': context.user_data.get('username'),
            'full_name': context.user_data.get('full_name'),
            'first_contact': context.user_data.get('first_contact'),
            'has_project': True,
            'object_type': context.user_data.get('object_type'),
            'area': context.user_data.get('area'),
            'region': context.user_data.get('region'),
            'timeline': context.user_data.get('timeline'),
            'survey_completed': True,
            'giveaway_participant': True,  # Автоматически участвует
            'source': 'survey'
        }
        save_user_data(context.user_data.get('user_id'), user_data)
        
        # Уведомляем админа
        await notify_admin_lead(context, user_data)
        
        await query.edit_message_text(
            "✅ Спасибо! Данные сохранены.\n\n"
            f"📦 Объект: {context.user_data.get('object_type')}\n"
            f"📐 Площадь: {context.user_data.get('area')}\n"
            f"📍 Регион: {context.user_data.get('region')}\n"
            f"⏰ Сроки: {context.user_data.get('timeline')}\n\n"
            "Если нужна консультация или расчёт стоимости — "
            "нажмите «Оставить заявку» или позвоните: +7 939 111-30-42\n\n"
            "🎁 Кстати, у нас сейчас розыгрыш бесплатного эскизного проекта "
            "(от 150 000 ₽). Вы уже участвуете! Итоги 28 февраля.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    # === Интересы по каналу ===
    elif data.startswith("int_"):
        if data == "int_done":
            # Завершаем выбор интересов
            await query.edit_message_text(
                "Спасибо! Учтём ваши предпочтения.\n\n"
                "🎁 В канале сейчас проходит розыгрыш бесплатного эскизного "
                "проекта стоимостью от 150 000 ₽.\n\n"
                "Хотите участвовать?",
                reply_markup=get_giveaway_keyboard()
            )
            return SURVEY_INTERESTS
        
        interests_map = {
            "int_law": "Законодательство",
            "int_cases": "Кейсы и ошибки",
            "int_cost": "Стоимость",
            "int_bim": "BIM",
            "int_expertise": "Экспертиза",
            "int_support": "Господдержка"
        }
        
        interest = interests_map.get(data)
        if interest:
            if 'interests' not in context.user_data:
                context.user_data['interests'] = []
            
            if interest in context.user_data['interests']:
                context.user_data['interests'].remove(interest)
            else:
                context.user_data['interests'].append(interest)
        
        selected = context.user_data.get('interests', [])
        selected_text = ", ".join(selected) if selected else "ничего не выбрано"
        
        await query.edit_message_text(
            f"Какие темы вам интересны?\n\n"
            f"Выбрано: {selected_text}\n\n"
            "Выберите и нажмите «Готово»:",
            reply_markup=get_interests_keyboard()
        )
        return SURVEY_INTERESTS
    
    # === Розыгрыш ===
    elif data == "giveaway_yes":
        context.user_data['giveaway_participant'] = True
        
        await query.edit_message_text(
            "Отлично! Для участия оставьте контакт (телефон или email) — "
            "на случай победы:"
        )
        return SURVEY_GIVEAWAY_CONTACT
    
    elif data == "giveaway_no":
        # Сохраняем данные без участия в розыгрыше
        user_data = {
            'user_id': context.user_data.get('user_id'),
            'username': context.user_data.get('username'),
            'full_name': context.user_data.get('full_name'),
            'first_contact': context.user_data.get('first_contact'),
            'has_project': False,
            'interests': context.user_data.get('interests', []),
            'giveaway_participant': False,
            'survey_completed': True,
            'source': 'survey'
        }
        save_user_data(context.user_data.get('user_id'), user_data)
        
        # Уведомляем админа
        await notify_admin_lead(context, user_data)
        
        await query.edit_message_text(
            "Хорошо! Если появится проект — пишите, поможем с расчётом.\n\n"
            "Выберите раздел:",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    # === Информация о розыгрыше ===
    elif data == "giveaway_info":
        await query.edit_message_text(
            GIVEAWAY_INFO,
            reply_markup=get_back_keyboard()
        )
        return ConversationHandler.END
    
    return ConversationHandler.END


async def survey_region_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение региона текстом"""
    context.user_data['region'] = update.message.text
    
    keyboard = get_timeline_keyboard()
    
    await update.message.reply_text(
        f"✅ Регион: {context.user_data['region']}\n\n"
        "Когда планируете начать проектирование?",
        reply_markup=keyboard
    )
    return SURVEY_TIMELINE


async def survey_giveaway_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение контакта для розыгрыша"""
    contact = update.message.text
    context.user_data['contact'] = contact
    
    # Сохраняем данные
    user_data = {
        'user_id': context.user_data.get('user_id'),
        'username': context.user_data.get('username'),
        'full_name': context.user_data.get('full_name'),
        'first_contact': context.user_data.get('first_contact'),
        'has_project': False,
        'interests': context.user_data.get('interests', []),
        'giveaway_participant': True,
        'giveaway_contact': contact,
        'survey_completed': True,
        'source': 'survey'
    }
    save_user_data(context.user_data.get('user_id'), user_data)
    
    # Уведомляем админа
    await notify_admin_lead(context, user_data)
    
    await update.message.reply_text(
        "🎉 Вы зарегистрированы в розыгрыше!\n\n"
        f"Контакт: {contact}\n\n"
        "Итоги объявим 28 февраля 2026 в канале @ADC_Project\n\n"
        "Удачи! 🍀",
        reply_markup=get_main_keyboard()
    )
    return ConversationHandler.END


# ============== ОБРАБОТЧИКИ КНОПОК МЕНЮ ==============
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка нажатий на inline-кнопки меню"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "menu":
        text = """🏠 Главное меню

Выберите интересующий раздел:"""
        await query.edit_message_text(
            text,
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    elif data == "company":
        await query.edit_message_text(
            COMPANY_INFO,
            reply_markup=get_request_keyboard()
        )
    
    elif data == "services":
        await query.edit_message_text(
            SERVICES_INFO,
            reply_markup=get_request_keyboard()
        )
    
    elif data == "objects":
        await query.edit_message_text(
            OBJECT_TYPES,
            reply_markup=get_request_keyboard()
        )
    
    elif data == "portfolio":
        await query.edit_message_text(
            PORTFOLIO_INFO,
            reply_markup=get_request_keyboard()
        )
    
    elif data == "giveaway_info":
        await query.edit_message_text(
            GIVEAWAY_INFO,
            reply_markup=get_back_keyboard()
        )
    
    elif data == "request":
        await query.edit_message_text(
            "📝 Заявка на консультацию\n\n"
            "Ответьте на несколько вопросов, и наш специалист свяжется с вами.\n\n"
            "Шаг 1 из 9\n"
            "Укажите город/регион объекта:"
        )
        return REQUEST_REGION
    
    elif data == "tech_question":
        await query.edit_message_text(
            "❓ Вопрос техническому специалисту\n\n"
            "Напишите ваш вопрос — наш специалист ответит в ближайшее время.\n\n"
            "Можете спросить про:\n"
            "• Состав проектной документации\n"
            "• Требования к исходным данным\n"
            "• Сроки и этапы проектирования\n"
            "• Прохождение экспертизы\n"
            "• BIM-моделирование\n\n"
            "_Для отмены: /cancel_"
        )
        return TECH_QUESTION
    
    return ConversationHandler.END


# ============== ФОРМА ЗАЯВКИ ==============
async def request_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало формы заявки через команду /request"""
    await update.message.reply_text(
        "📝 Заявка на консультацию\n\n"
        "Ответьте на несколько вопросов, и наш специалист свяжется с вами.\n\n"
        "Шаг 1 из 9\n"
        "Укажите город/регион объекта:\n\n"
        "_Для отмены: /cancel_"
    )
    return REQUEST_REGION


async def get_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение региона"""
    context.user_data['region'] = update.message.text
    
    keyboard = ReplyKeyboardMarkup(
        [
            ["Склад / Логистический центр"],
            ["Производство / Завод"],
            ["Торговый центр / Магазин"],
            ["Офисное здание / БЦ"],
            ["Жилой дом / МКД"],
            ["Гостиница / Санаторий"],
            ["Медицинский объект"],
            ["Образовательный объект"],
            ["Спортивный объект"],
            ["🔹 Другое (указать)"]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "Шаг 2 из 9\n"
        "Выберите тип объекта:",
        reply_markup=keyboard
    )
    return REQUEST_OBJECT_TYPE


async def get_object_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение типа объекта"""
    text = update.message.text
    
    if "Другое" in text:
        await update.message.reply_text(
            "Укажите тип вашего объекта:",
            reply_markup=ReplyKeyboardRemove()
        )
        return REQUEST_OBJECT_TYPE_CUSTOM
    
    context.user_data['object_type'] = text
    
    await update.message.reply_text(
        "Шаг 3 из 9\n"
        "Укажите примерную площадь объекта (м²):",
        reply_markup=ReplyKeyboardRemove()
    )
    return REQUEST_AREA


async def get_object_type_custom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение пользовательского типа объекта"""
    context.user_data['object_type'] = update.message.text + " (указано пользователем)"
    
    await update.message.reply_text(
        "Шаг 3 из 9\n"
        "Укажите примерную площадь объекта (м²):"
    )
    return REQUEST_AREA


async def get_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение площади"""
    context.user_data['area'] = update.message.text
    
    keyboard = ReplyKeyboardMarkup(
        [
            ["Идея / концепция"],
            ["Подбор участка"],
            ["Есть участок, нужен проект"],
            ["Есть проект, нужна корректировка"],
            ["Строительство"],
            ["Эксплуатация / реконструкция"]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "Шаг 4 из 9\n"
        "На какой стадии находится проект?",
        reply_markup=keyboard
    )
    return REQUEST_STAGE


async def get_stage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение стадии"""
    context.user_data['stage'] = update.message.text
    
    keyboard = ReplyKeyboardMarkup(
        [
            ["Эскизный проект"],
            ["АГР / АГО"],
            ["Проектирование (П+РД)"],
            ["Только проектная (П)"],
            ["Только рабочая (РД)"],
            ["Строительство"],
            ["Комплекс услуг (проект + строительство)"]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "Шаг 5 из 9\n"
        "Что требуется?",
        reply_markup=keyboard
    )
    return REQUEST_SERVICE


async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение услуги"""
    context.user_data['service'] = update.message.text
    
    keyboard = ReplyKeyboardMarkup(
        [
            ["Да, нужен BIM"],
            ["Нет, без BIM"],
            ["Нужна консультация по BIM"]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "Шаг 6 из 9\n"
        "Требуется ли BIM-проектирование?",
        reply_markup=keyboard
    )
    return REQUEST_BIM


async def get_bim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение ответа про BIM"""
    context.user_data['bim'] = update.message.text
    
    keyboard = ReplyKeyboardMarkup(
        [
            ["Да, нужна смета"],
            ["Нет, без сметы"],
            ["Нужна консультация по смете"]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "Шаг 7 из 9\n"
        "Требуется ли разработка сметной документации?",
        reply_markup=keyboard
    )
    return REQUEST_SURVEY


async def get_survey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение ответа про смету"""
    context.user_data['survey'] = update.message.text
    
    keyboard = ReplyKeyboardMarkup(
        [
            ["Срочно (до 1 месяца)"],
            ["1-3 месяца"],
            ["3-6 месяцев"],
            ["Более 6 месяцев"],
            ["Пока не определились"]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "Шаг 8 из 9\n"
        "Когда планируете начать работы?",
        reply_markup=keyboard
    )
    return REQUEST_TIMELINE


async def get_timeline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение сроков"""
    context.user_data['timeline'] = update.message.text
    
    await update.message.reply_text(
        "Шаг 9 из 9\n"
        "Дополнительные комментарии или вопросы?\n\n"
        "(напишите или отправьте «—» если нет)",
        reply_markup=ReplyKeyboardRemove()
    )
    return REQUEST_COMMENT


async def get_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение комментария"""
    context.user_data['comment'] = update.message.text
    
    await update.message.reply_text(
        "📎 Хотите приложить файлы?\n\n"
        "(ГПЗУ, ТЗ, эскизы, фото участка)\n\n"
        "Отправьте файлы или напишите «Нет»"
    )
    return REQUEST_FILES


async def get_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение файлов"""
    if update.message.document:
        if 'files' not in context.user_data:
            context.user_data['files'] = []
        context.user_data['files'].append(update.message.document.file_id)
        
        await update.message.reply_text(
            f"✅ Файл получен ({len(context.user_data['files'])})\n\n"
            "Отправьте ещё файлы или напишите «Готово»"
        )
        return REQUEST_FILES
    
    elif update.message.photo:
        if 'files' not in context.user_data:
            context.user_data['files'] = []
        context.user_data['files'].append(update.message.photo[-1].file_id)
        
        await update.message.reply_text(
            f"✅ Фото получено ({len(context.user_data['files'])})\n\n"
            "Отправьте ещё файлы или напишите «Готово»"
        )
        return REQUEST_FILES
    
    else:
        context.user_data['files'] = context.user_data.get('files', [])
        
        await update.message.reply_text(
            "📞 Укажите контактные данные для связи:\n\n"
            "(телефон, email или Telegram)"
        )
        return REQUEST_CONTACT


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение контакта и отправка заявки"""
    context.user_data['contact'] = update.message.text
    user = update.effective_user
    
    # Формируем заявку
    request_text = f"""📝 НОВАЯ ЗАЯВКА

👤 {user.full_name or 'Пользователь'}
🆔 ID: {user.id}
📱 @{user.username if user.username else 'нет username'}

📍 Регион: {context.user_data.get('region', '—')}
🏗 Объект: {context.user_data.get('object_type', '—')}
📐 Площадь: {context.user_data.get('area', '—')}
📊 Стадия: {context.user_data.get('stage', '—')}
🔧 Услуга: {context.user_data.get('service', '—')}
💻 BIM: {context.user_data.get('bim', '—')}
📋 Смета: {context.user_data.get('survey', '—')}
⏰ Сроки: {context.user_data.get('timeline', '—')}
💬 Комментарий: {context.user_data.get('comment', '—')}

📞 Контакт: {context.user_data.get('contact', '—')}
📎 Файлов: {len(context.user_data.get('files', []))}

📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
    
    # Отправляем менеджеру
    if MANAGER_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=request_text
            )
            
            # Отправляем файлы
            for file_id in context.user_data.get('files', []):
                try:
                    await context.bot.send_document(
                        chat_id=MANAGER_CHAT_ID,
                        document=file_id,
                        caption=f"Файл от {user.full_name} (ID: {user.id})"
                    )
                except:
                    pass
            
            logger.info(f"Request sent from user: {user.id}")
        except Exception as e:
            logger.error(f"Failed to send request: {e}")
    
    await update.message.reply_text(
        "✅ Заявка отправлена!\n\n"
        "Наш специалист свяжется с вами в ближайшее время.\n\n"
        "Если вопрос срочный:\n"
        "📞 +7 939 111 30 42\n"
        "📞 8 (495) 118-34-88\n"
        "📧 Email: info@arxproektstroy.ru\n\n"
        "Спасибо за обращение в ADC Group!",
        reply_markup=get_main_keyboard()
    )
    
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена заявки"""
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ Действие отменено.\n\n"
        "Вы можете вернуться в главное меню: /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def get_tech_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение технического вопроса"""
    question = update.message.text
    user = update.effective_user
    
    if MANAGER_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=f"❓ ТЕХНИЧЕСКИЙ ВОПРОС\n\n"
                     f"👤 От: {user.full_name or 'Пользователь'}\n"
                     f"🆔 ID: {user.id}\n"
                     f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                     f"💬 Вопрос:\n{question}\n\n"
                     f"@{user.username if user.username else 'нет username'}"
            )
            logger.info(f"Tech question sent from user: {user.id}")
        except Exception as e:
            logger.error(f"Failed to send tech question: {e}")
    
    await update.message.reply_text(
        "✅ Вопрос отправлен!\n\n"
        "Наш технический специалист ответит в ближайшее время.\n\n"
        "Если вопрос срочный, можете позвонить:\n"
        "📞 +7 939 111 30 42\n"
        "📞 8 (495) 118-34-88",
        reply_markup=get_main_keyboard()
    )
    
    return ConversationHandler.END


# ============== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ ==============
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка произвольных сообщений"""
    text = update.message.text.lower()
    user = update.effective_user
    
    # Проверяем ключевое слово "розыгрыш"
    if "розыгрыш" in text:
        await update.message.reply_text(
            GIVEAWAY_INFO,
            reply_markup=get_back_keyboard()
        )
        return
    
    # Простые ответы на ключевые слова
    if any(word in text for word in ["привет", "здравствуй", "добрый"]):
        await update.message.reply_text(
            "Здравствуйте! 👋\n\n"
            "Я — навигатор канала ADC Group.\n"
            "Нажмите /start для просмотра меню."
        )
    
    elif any(word in text for word in ["цена", "стоимость", "сколько стоит", "прайс"]):
        await update.message.reply_text(
            "💰 Стоимость зависит от типа и площади объекта.\n\n"
            "Для расчёта оставьте заявку — наш специалист "
            "подготовит коммерческое предложение.\n\n"
            "📝 /request — оставить заявку"
        )
    
    elif any(word in text for word in ["срок", "сколько времени", "как долго"]):
        await update.message.reply_text(
            "⏰ Сроки проектирования зависят от площади и сложности объекта.\n\n"
            "Ориентировочно:\n"
            "• до 5 000 м² — от 60 дней\n"
            "• 5 000–20 000 м² — от 90 дней\n"
            "• более 20 000 м² — от 120 дней\n\n"
            "📝 Для точного расчёта: /request"
        )
    
    elif any(word in text for word in ["контакт", "телефон", "позвонить", "связаться"]):
        await update.message.reply_text(
            "📞 Контакты ADC Group:\n\n"
            "Мобильный: +7 939 111 30 42\n"
            "Городской: 8 (495) 118-34-88\n"
            "Email: info@arxproektstroy.ru\n"
            "Сайт: arxproektstroy.ru\n\n"
            "📝 Или оставьте заявку: /request"
        )
    
    elif any(word in text for word in ["bim", "бим"]):
        await update.message.reply_text(
            "💻 BIM-проектирование\n\n"
            "ADC Group работает с BIM-технологиями с 2018 года.\n\n"
            "Преимущества:\n"
            "• 3D-модель объекта\n"
            "• Автоматическая проверка коллизий\n"
            "• Точные спецификации\n"
            "• Удобство согласований\n\n"
            "📝 Для расчёта: /request"
        )
    
    elif any(word in text for word in ["экспертиза", "экспертизу"]):
        await update.message.reply_text(
            "🏛 Прохождение экспертизы\n\n"
            "Сопровождаем проекты в государственной и негосударственной экспертизе.\n\n"
            "• 87% экспертиз с первого раза\n"
            "• Устраняем замечания за свой счёт\n"
            "• Опыт работы со всеми регионами\n\n"
            "📝 Подробнее: /request"
        )
    
    else:
        await update.message.reply_text(
            "Я могу помочь с информацией о компании и услугах.\n\n"
            "Нажмите /start для просмотра меню\n"
            "или /request чтобы оставить заявку."
        )
        
        # Отправляем неотвеченный вопрос менеджеру
        if MANAGER_CHAT_ID and len(text) > 3:
            try:
                await context.bot.send_message(
                    chat_id=MANAGER_CHAT_ID,
                    text=f"❓ ВОПРОС БЕЗ ОТВЕТА\n\n"
                         f"👤 {user.full_name or 'Пользователь'} (@{user.username or user.id})\n"
                         f"💬 {update.message.text}\n\n"
                         f"_Бот не нашёл подходящий ответ_"
                )
            except Exception as e:
                logger.error(f"Failed to send unanswered question: {e}")


# ============== HEALTH CHECK ==============
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
    
    def log_message(self, format, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"Health server on port {port}")
    server.serve_forever()


# ============== MAIN ==============
def main() -> None:
    token = os.environ.get("TELEGRAM_TOKEN")
    
    if not token:
        logger.error("TELEGRAM_TOKEN not found")
        return
    
    # Health-check сервер
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # Создаём приложение
    application = Application.builder().token(token).build()
    
    # ConversationHandler для приветственной анкеты
    survey_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start)
        ],
        states={
            SURVEY_HAS_PROJECT: [CallbackQueryHandler(survey_callback)],
            SURVEY_OBJECT_TYPE: [CallbackQueryHandler(survey_callback)],
            SURVEY_AREA: [CallbackQueryHandler(survey_callback)],
            SURVEY_REGION: [CallbackQueryHandler(survey_callback)],
            SURVEY_REGION_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, survey_region_text)],
            SURVEY_TIMELINE: [CallbackQueryHandler(survey_callback)],
            SURVEY_INTERESTS: [CallbackQueryHandler(survey_callback)],
            SURVEY_GIVEAWAY_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, survey_giveaway_contact)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(button_handler, pattern="^menu$")
        ],
    )
    
    # ConversationHandler для формы заявки
    request_handler = ConversationHandler(
        entry_points=[
            CommandHandler("request", request_start),
            CallbackQueryHandler(button_handler, pattern="^request$"),
            CallbackQueryHandler(button_handler, pattern="^tech_question$")
        ],
        states={
            REQUEST_REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_region)],
            REQUEST_OBJECT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_object_type)],
            REQUEST_OBJECT_TYPE_CUSTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_object_type_custom)],
            REQUEST_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_area)],
            REQUEST_STAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_stage)],
            REQUEST_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            REQUEST_BIM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bim)],
            REQUEST_SURVEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_survey)],
            REQUEST_TIMELINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_timeline)],
            REQUEST_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_comment)],
            REQUEST_FILES: [
                MessageHandler(filters.Document.ALL, get_files),
                MessageHandler(filters.PHOTO, get_files),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_files)
            ],
            REQUEST_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            TECH_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tech_question)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(button_handler, pattern="^menu$")
        ],
    )
    
    # Регистрация обработчиков
    application.add_handler(survey_handler)
    application.add_handler(request_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("giveaway", giveaway_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot ADC Navigator v3.0 started")
    logger.info("Features: survey, giveaway, request form")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
