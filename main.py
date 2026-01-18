"""
Telegram-бот «Навигатор ADC» — публичный бот для канала
Версия: 2.1
Дата: 18.01.2026
ООО «МИРИНГ ГРУП»

ФУНКЦИОНАЛ:
- Информация о компании
- Категории услуг (без цен)
- Расширенная форма заявки с файлами
- Вопрос техническому специалисту
- Сбор неотвеченных вопросов
- Ссылки на сайт/портфолио
"""

import os
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

# Ссылки
SITE_URL = "https://arxproektstroy.ru"
PORTFOLIO_URL = "https://drive.google.com/file/d/1gj0bPzw36cJMR413GEoRHoGSUjQKD29_/view"
CHANNEL_URL = "https://t.me/ADC_Project"

# Состояния для ConversationHandler (форма заявки)
(REGION, OBJECT_TYPE, OBJECT_TYPE_CUSTOM, AREA, STAGE, SERVICE, 
 BIM_QUESTION, SURVEY_QUESTION, TIMELINE, COMMENT, FILES, CONTACT, TECH_QUESTION) = range(13)


# ============== ИНФОРМАЦИЯ О КОМПАНИИ ==============
COMPANY_INFO = """🏢 ADC Group (ООО «МИРИНГ ГРУП»)

Федеральная инженерно-проектная группа полного цикла.

📊 Ключевые показатели:
• 26 лет на рынке
• 21 000+ реализованных проектов
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


# ============== ОБРАБОТЧИКИ КОМАНД ==============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start — приветствие и главное меню"""
    user_name = update.effective_user.first_name or "Здравствуйте"
    
    text = f"""👋 {user_name}, добро пожаловать!

Я — навигатор канала ADC Group.

Помогу узнать о компании, услугах и оставить заявку на консультацию.

Выберите интересующий раздел:"""
    
    await update.message.reply_text(
        text,
        reply_markup=get_main_keyboard()
        
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help — справка"""
    text = """📚 СПРАВКА

Команды:
/start — главное меню
/help — эта справка
/request — оставить заявку

Разделы меню:
• О компании — информация об ADC Group
• Услуги — перечень услуг
• Типы объектов — что проектируем
• Портфолио — примеры работ
• Оставить заявку — форма для связи

Контакты:
📞 Мобильный: +7 939 111 30 42
📞 Городской: 8 (495) 118-34-88
📧 info@arxproektstroy.ru
🌐 arxproektstroy.ru"""
    
    await update.message.reply_text(text, )


# ============== ОБРАБОТЧИКИ КНОПОК ==============
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка нажатий на inline-кнопки"""
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
    
    elif data == "request":
        await query.edit_message_text(
            "📝 Заявка на консультацию\n\n"
            "Ответьте на несколько вопросов, и наш специалист свяжется с вами.\n\n"
            "Шаг 1 из 9\n"
            "Укажите город/регион объекта:",
            
        )
        return REGION
    
    elif data == "tech_question":
        await query.edit_message_text(
            "❓ Вопрос техническому специалисту\n\n"
            "Напишите ваш вопрос — наш специалист ответит в ближайшее время.\n\n"
            "Можете спросить про:\n"
            "• Состав проектной документации\n"
            "• Требования к исходным данным\n"
            "• Сроки и этапы проектирования\n"
            "• Прохождение экспертизы\n"
            "• BIM-моделирование\n"
            "• Инженерные изыскания\n\n"
            "_Для отмены: /cancel_",
            
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
        "_Для отмены: /cancel_",
        
    )
    return REGION


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
        reply_markup=keyboard,
        
    )
    return OBJECT_TYPE


async def get_object_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение типа объекта"""
    text = update.message.text
    
    if "Другое" in text:
        await update.message.reply_text(
            "Укажите тип вашего объекта:",
            reply_markup=ReplyKeyboardRemove(),
            
        )
        return OBJECT_TYPE_CUSTOM
    
    context.user_data['object_type'] = text
    
    await update.message.reply_text(
        "Шаг 3 из 9\n"
        "Укажите примерную площадь объекта (м²):",
        reply_markup=ReplyKeyboardRemove(),
        
    )
    return AREA


async def get_object_type_custom(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение пользовательского типа объекта"""
    context.user_data['object_type'] = update.message.text + " (указано пользователем)"
    
    await update.message.reply_text(
        "Шаг 3 из 9\n"
        "Укажите примерную площадь объекта (м²):",
        
    )
    return AREA


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
        reply_markup=keyboard,
        
    )
    return STAGE


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
        reply_markup=keyboard,
        
    )
    return SERVICE


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
        reply_markup=keyboard,
        
    )
    return BIM_QUESTION


async def get_bim(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение ответа про BIM"""
    context.user_data['bim'] = update.message.text
    
    keyboard = ReplyKeyboardMarkup(
        [
            ["Да, нужны изыскания"],
            ["Нет, изыскания есть"],
            ["Нужна консультация"]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "Шаг 7 из 9\n"
        "Требуются ли инженерные изыскания\n(геодезия, геология, экология)?",
        reply_markup=keyboard,
        
    )
    return SURVEY_QUESTION


async def get_survey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение ответа про изыскания"""
    context.user_data['survey'] = update.message.text
    
    keyboard = ReplyKeyboardMarkup(
        [
            ["Срочно (в течение месяца)"],
            ["В ближайшие 3 месяца"],
            ["В течение полугода"],
            ["Пока изучаем рынок"]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "Шаг 8 из 9\n"
        "Когда планируете начать?",
        reply_markup=keyboard,
        
    )
    return TIMELINE


async def get_timeline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение сроков"""
    context.user_data['timeline'] = update.message.text
    
    keyboard = ReplyKeyboardMarkup(
        [["Пропустить"]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "Шаг 9 из 9\n"
        "Добавьте комментарий или дополнительную информацию:\n"
        "(или нажмите «Пропустить»)",
        reply_markup=keyboard,
        
    )
    return COMMENT


async def get_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение комментария"""
    text = update.message.text
    if text.lower() != "пропустить":
        context.user_data['comment'] = text
    else:
        context.user_data['comment'] = "-"
    
    keyboard = ReplyKeyboardMarkup(
        [["Пропустить файлы"]],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "📎 Если есть файлы (ТЗ, ГПЗУ, чертежи), можете прикрепить их сейчас.\n\n"
        "Отправьте файл(ы) или нажмите «Пропустить файлы».",
        reply_markup=keyboard,
        
    )
    return FILES


async def get_files(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение файлов"""
    if update.message.document:
        if 'files' not in context.user_data:
            context.user_data['files'] = []
        context.user_data['files'].append(update.message.document.file_id)
        
        await update.message.reply_text(
            f"✅ Файл получен: {update.message.document.file_name}\n\n"
            "Отправьте ещё файл или нажмите «Пропустить файлы» для продолжения.",
            
        )
        return FILES
    
    elif update.message.photo:
        if 'files' not in context.user_data:
            context.user_data['files'] = []
        context.user_data['files'].append(update.message.photo[-1].file_id)
        
        await update.message.reply_text(
            "✅ Фото получено.\n\n"
            "Отправьте ещё файл или нажмите «Пропустить файлы» для продолжения.",
            
        )
        return FILES
    
    else:
        # Текстовое сообщение — переходим к контакту
        await update.message.reply_text(
            "✅ Почти готово!\n\n"
            "Оставьте контакт для связи:\n"
            "телефон или имя в Telegram",
            reply_markup=ReplyKeyboardRemove(),
            
        )
        return CONTACT


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение контакта и отправка заявки"""
    context.user_data['contact'] = update.message.text
    user = update.effective_user
    
    # Формируем заявку
    files_info = ""
    if context.user_data.get('files'):
        files_info = f"\n📎 Файлов прикреплено: {len(context.user_data['files'])}"
    
    request_text = f"""🔔 НОВАЯ ЗАЯВКА С КАНАЛА

👤 Пользователь: {user.full_name or user.username or 'Не указано'}
🆔 ID: {user.id}
📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}

📍 Регион: {context.user_data.get('region', '-')}
🏗 Тип объекта: {context.user_data.get('object_type', '-')}
📐 Площадь: {context.user_data.get('area', '-')}
📊 Стадия: {context.user_data.get('stage', '-')}
🔧 Услуга: {context.user_data.get('service', '-')}
💻 BIM: {context.user_data.get('bim', '-')}
🔬 Изыскания: {context.user_data.get('survey', '-')}
⏰ Сроки: {context.user_data.get('timeline', '-')}
💬 Комментарий: {context.user_data.get('comment', '-')}
📞 Контакт: {context.user_data.get('contact', '-')}{files_info}

@{user.username if user.username else 'нет username'}"""

    # Отправляем менеджеру
    if MANAGER_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=request_text,
                
            )
            
            # Отправляем файлы менеджеру
            if context.user_data.get('files'):
                for file_id in context.user_data['files']:
                    try:
                        await context.bot.send_document(
                            chat_id=MANAGER_CHAT_ID,
                            document=file_id,
                            caption=f"📎 Файл к заявке от {user.full_name or user.username}"
                        )
                    except:
                        try:
                            await context.bot.send_photo(
                                chat_id=MANAGER_CHAT_ID,
                                photo=file_id,
                                caption=f"📎 Фото к заявке от {user.full_name or user.username}"
                            )
                        except Exception as e:
                            logger.error(f"Failed to send file: {e}")
            
            logger.info(f"Request sent to manager: {user.id}")
        except Exception as e:
            logger.error(f"Failed to send to manager: {e}")
    
    # Подтверждение пользователю
    await update.message.reply_text(
        "✅ Заявка отправлена!\n\n"
        "Наш специалист свяжется с вами в ближайшее время.\n\n"
        "📞 Мобильный: +7 939 111 30 42\n"
        "📞 Городской: 8 (495) 118-34-88\n"
        "📧 Email: info@arxproektstroy.ru\n\n"
        "Спасибо за обращение в ADC Group!",
        reply_markup=get_main_keyboard()
        
    )
    
    # Очищаем данные
    context.user_data.clear()
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена заявки"""
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ Заявка отменена.\n\n"
        "Вы можете вернуться в главное меню: /start",
        reply_markup=ReplyKeyboardRemove(),
        
    )
    return ConversationHandler.END


async def get_tech_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение технического вопроса и отправка специалисту"""
    question = update.message.text
    user = update.effective_user
    
    # Отправляем вопрос менеджеру
    if MANAGER_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=f"❓ ТЕХНИЧЕСКИЙ ВОПРОС\n\n"
                     f"👤 От: {user.full_name or 'Пользователь'}\n"
                     f"🆔 ID: {user.id}\n"
                     f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                     f"💬 Вопрос:\n{question}\n\n"
                     f"@{user.username if user.username else 'нет username'}",
                
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
    answered = False
    
    # Простые ответы на ключевые слова
    if any(word in text for word in ["привет", "здравствуй", "добрый"]):
        await update.message.reply_text(
            "Здравствуйте! 👋\n\n"
            "Я — навигатор канала ADC Group.\n"
            "Нажмите /start для просмотра меню.",
            
        )
        answered = True
    
    elif any(word in text for word in ["цена", "стоимость", "сколько стоит", "прайс"]):
        await update.message.reply_text(
            "💰 Стоимость зависит от типа и площади объекта.\n\n"
            "Для расчёта оставьте заявку — наш специалист "
            "подготовит коммерческое предложение.\n\n"
            "📝 /request — оставить заявку",
            
        )
        answered = True
    
    elif any(word in text for word in ["срок", "сколько времени", "как долго", "когда"]):
        await update.message.reply_text(
            "⏰ Сроки проектирования зависят от площади и сложности объекта.\n\n"
            "Ориентировочно:\n"
            "• до 5 000 м² — от 60 дней\n"
            "• 5 000–20 000 м² — от 90 дней\n"
            "• более 20 000 м² — от 120 дней\n\n"
            "📝 Для точного расчёта: /request",
            
        )
        answered = True
    
    elif any(word in text for word in ["контакт", "телефон", "позвонить", "связаться"]):
        await update.message.reply_text(
            "📞 Контакты ADC Group:\n\n"
            "Мобильный: +7 939 111 30 42\n"
            "Городской: 8 (495) 118-34-88\n"
            "Email: info@arxproektstroy.ru\n"
            "Сайт: arxproektstroy.ru\n\n"
            "📝 Или оставьте заявку: /request",
            
        )
        answered = True
    
    elif any(word in text for word in ["bim", "бим"]):
        await update.message.reply_text(
            "💻 BIM-проектирование\n\n"
            "ADC Group работает с BIM-технологиями с 2018 года.\n\n"
            "Преимущества:\n"
            "• 3D-модель объекта\n"
            "• Автоматическая проверка коллизий\n"
            "• Точные спецификации\n"
            "• Удобство согласований\n\n"
            "📝 Для расчёта: /request",
            
        )
        answered = True
    
    elif any(word in text for word in ["экспертиза", "экспертизу"]):
        await update.message.reply_text(
            "🏛 Прохождение экспертизы\n\n"
            "Сопровождаем проекты в государственной и негосударственной экспертизе.\n\n"
            "• 87% экспертиз с первого раза\n"
            "• Устраняем замечания за свой счёт\n"
            "• Опыт работы со всеми регионами\n\n"
            "📝 Подробнее: /request",
            
        )
        answered = True
    
    elif any(word in text for word in ["изыскания", "геология", "геодезия"]):
        await update.message.reply_text(
            "🔬 Инженерные изыскания\n\n"
            "Выполняем полный комплекс:\n"
            "• Геодезические изыскания\n"
            "• Инженерно-геологические изыскания\n"
            "• Экологические изыскания\n\n"
            "📝 Заказать: /request",
            
        )
        answered = True
    
    else:
        await update.message.reply_text(
            "Я могу помочь с информацией о компании и услугах.\n\n"
            "Нажмите /start для просмотра меню\n"
            "или /request чтобы оставить заявку.",
            
        )
        
        # Отправляем неотвеченный вопрос менеджеру
        if MANAGER_CHAT_ID and len(text) > 3:
            try:
                await context.bot.send_message(
                    chat_id=MANAGER_CHAT_ID,
                    text=f"❓ ВОПРОС БЕЗ ОТВЕТА\n\n"
                         f"👤 {user.full_name or 'Пользователь'} (@{user.username or user.id})\n"
                         f"💬 {update.message.text}\n\n"
                         f"_Бот не нашёл подходящий ответ_",
                    
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
    
    # ConversationHandler для формы заявки
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("request", request_start),
            CallbackQueryHandler(button_handler, pattern="^request$"),
            CallbackQueryHandler(button_handler, pattern="^tech_question$")
        ],
        states={
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_region)],
            OBJECT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_object_type)],
            OBJECT_TYPE_CUSTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_object_type_custom)],
            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_area)],
            STAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_stage)],
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            BIM_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bim)],
            SURVEY_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_survey)],
            TIMELINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_timeline)],
            COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_comment)],
            FILES: [
                MessageHandler(filters.Document.ALL, get_files),
                MessageHandler(filters.PHOTO, get_files),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_files)
            ],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            TECH_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tech_question)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(button_handler, pattern="^menu$")
        ],
    )
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot ADC Navigator v2.1 started")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
