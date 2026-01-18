"""
Telegram-бот «Навигатор ADC» — публичный бот для канала
Версия: 1.0
Дата: 18.01.2026
ООО «МИРИНГ ГРУП»

ФУНКЦИОНАЛ:
- Информация о компании
- Категории услуг (без цен)
- Форма заявки → уведомление менеджеру
- Ссылки на сайт/портфолио

БЕЗ: ставок, калькулятора, внутренних контактов, скриптов
"""

import os
import logging
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
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
# ID менеджера для уведомлений о заявках (заменить на реальный)
MANAGER_CHAT_ID = os.environ.get("MANAGER_CHAT_ID", "")

# Ссылки
SITE_URL = "https://miringgroup.com"
PORTFOLIO_URL = "https://drive.google.com/file/d/1gj0bPzw36cJMR413GEoRHoGSUjQKD29_/view"
CHANNEL_URL = "https://t.me/ADC_Project"

# Состояния для ConversationHandler (форма заявки)
REGION, OBJECT_TYPE, AREA, STAGE, SERVICE, TIMELINE, CONTACT = range(7)


# ============== ИНФОРМАЦИЯ О КОМПАНИИ ==============
COMPANY_INFO = """🏢 **ADC Group** (ООО «МИРИНГ ГРУП»)

Федеральная инженерно-проектная группа полного цикла.

📊 **Ключевые показатели:**
• 26 лет на рынке
• 21 000+ реализованных проектов
• 80+ специалистов в штате
• 200+ партнёрских организаций
• 18+ регионов России
• BIM-технологии с 2018 года

🏆 **Знаковые заказчики:**
Лукойл, Сбербанк, Газпром, ПИК, X5 Retail, РЖД, Магнит, Правительство Москвы

🌐 Сайт: miringgroup.com
📞 Телефон: 8-800-350-13-90
📧 Email: info@arxproektstroy.ru"""


SERVICES_INFO = """📐 **УСЛУГИ ADC Group**

**1. Проектирование**
• Проектная документация (стадия П)
• Рабочая документация (стадия РД)
• Эскизное проектирование
• BIM-моделирование

**2. Сопровождение**
• Прохождение экспертизы
• Получение разрешения на строительство
• Авторский надзор
• Функции технического заказчика

**3. Инженерные изыскания**
• Геодезические
• Геологические
• Экологические

**4. Строительство**
• СМР по собственным проектам
• Комплексное строительство под ключ

📋 Для расчёта сроков и стоимости — оставьте заявку"""


OBJECT_TYPES = """🏗 **ТИПЫ ОБЪЕКТОВ**

Проектируем коммерческие объекты любого назначения:

**Промышленность и логистика:**
• Склады и логистические центры
• Производственные здания
• Заводы и фабрики

**Торговля и офисы:**
• Торговые центры
• Бизнес-центры
• Магазины и ритейл

**Социальные объекты:**
• Медицинские учреждения
• Образовательные учреждения
• Спортивные объекты

**Жильё и гостиницы:**
• Многоквартирные дома
• Гостиницы и санатории
• Апарт-отели

**Инфраструктура:**
• Наружные сети
• Благоустройство
• Дороги и площадки"""


PORTFOLIO_INFO = """📁 **ПОРТФОЛИО ADC Group**

Более 200 объектов в активном портфолио.

🔗 **Посмотреть портфолио:**
{portfolio_url}

🔗 **Выполненные проекты на сайте:**
https://arxproektstroy.ru/proekty

📊 **Статистика:**
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

Я — навигатор канала **ADC Group**.

Помогу узнать о компании, услугах и оставить заявку на консультацию.

Выберите интересующий раздел:"""
    
    await update.message.reply_text(
        text,
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help — справка"""
    text = """📚 **СПРАВКА**

**Команды:**
/start — главное меню
/help — эта справка
/request — оставить заявку

**Разделы меню:**
• О компании — информация об ADC Group
• Услуги — перечень услуг
• Типы объектов — что проектируем
• Портфолио — примеры работ
• Оставить заявку — форма для связи

**Контакты:**
📞 8-800-350-13-90
📧 info@arxproektstroy.ru
🌐 miringgroup.com"""
    
    await update.message.reply_text(text, parse_mode="Markdown")


# ============== ОБРАБОТЧИКИ КНОПОК ==============
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатий на inline-кнопки"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "menu":
        text = """🏠 **Главное меню**

Выберите интересующий раздел:"""
        await query.edit_message_text(
            text,
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "company":
        await query.edit_message_text(
            COMPANY_INFO,
            reply_markup=get_request_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "services":
        await query.edit_message_text(
            SERVICES_INFO,
            reply_markup=get_request_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "objects":
        await query.edit_message_text(
            OBJECT_TYPES,
            reply_markup=get_request_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "portfolio":
        await query.edit_message_text(
            PORTFOLIO_INFO,
            reply_markup=get_request_keyboard(),
            parse_mode="Markdown"
        )
    
    elif data == "request":
        # Запускаем форму заявки
        await query.edit_message_text(
            "📝 **Заявка на консультацию**\n\n"
            "Ответьте на несколько вопросов, и наш специалист свяжется с вами.\n\n"
            "**Шаг 1 из 6**\n"
            "Укажите город/регион объекта:",
            parse_mode="Markdown"
        )
        return REGION


# ============== ФОРМА ЗАЯВКИ (ConversationHandler) ==============
async def request_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало формы заявки через команду /request"""
    await update.message.reply_text(
        "📝 **Заявка на консультацию**\n\n"
        "Ответьте на несколько вопросов, и наш специалист свяжется с вами.\n\n"
        "**Шаг 1 из 6**\n"
        "Укажите город/регион объекта:",
        parse_mode="Markdown"
    )
    return REGION


async def get_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение региона"""
    context.user_data['region'] = update.message.text
    
    keyboard = ReplyKeyboardMarkup(
        [
            ["Склад", "Производство"],
            ["Торговый центр", "Офис/БЦ"],
            ["Медицина", "Образование"],
            ["Жильё/МКД", "Гостиница"],
            ["Другое"]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "**Шаг 2 из 6**\n"
        "Выберите тип объекта:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return OBJECT_TYPE


async def get_object_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение типа объекта"""
    context.user_data['object_type'] = update.message.text
    
    await update.message.reply_text(
        "**Шаг 3 из 6**\n"
        "Укажите ориентировочную площадь (м²) или мощность объекта:",
        parse_mode="Markdown"
    )
    return AREA


async def get_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение площади"""
    context.user_data['area'] = update.message.text
    
    keyboard = ReplyKeyboardMarkup(
        [
            ["Идея / концепция"],
            ["Подбор участка"],
            ["Проектирование"],
            ["Строительство"],
            ["Эксплуатация"]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "**Шаг 4 из 6**\n"
        "На какой стадии находится проект?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return STAGE


async def get_stage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение стадии"""
    context.user_data['stage'] = update.message.text
    
    keyboard = ReplyKeyboardMarkup(
        [
            ["Проектирование (П+РД)"],
            ["Только проектная (П)"],
            ["Только рабочая (РД)"],
            ["Строительство"],
            ["Комплекс услуг"]
        ],
        one_time_keyboard=True,
        resize_keyboard=True
    )
    
    await update.message.reply_text(
        "**Шаг 5 из 6**\n"
        "Что требуется?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return SERVICE


async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение услуги"""
    context.user_data['service'] = update.message.text
    
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
        "**Шаг 6 из 6**\n"
        "Когда планируете начать?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return TIMELINE


async def get_timeline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение сроков"""
    context.user_data['timeline'] = update.message.text
    
    await update.message.reply_text(
        "✅ Почти готово!\n\n"
        "Оставьте контакт для связи:\n"
        "телефон или имя в Telegram",
        parse_mode="Markdown"
    )
    return CONTACT


async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получение контакта и отправка заявки"""
    context.user_data['contact'] = update.message.text
    user = update.effective_user
    
    # Формируем заявку
    request_text = f"""🔔 **НОВАЯ ЗАЯВКА С КАНАЛА**

👤 **Пользователь:** {user.full_name or user.username or 'Не указано'}
🆔 **ID:** {user.id}
📅 **Дата:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

📍 **Регион:** {context.user_data.get('region', '-')}
🏗 **Тип объекта:** {context.user_data.get('object_type', '-')}
📐 **Площадь:** {context.user_data.get('area', '-')}
📊 **Стадия:** {context.user_data.get('stage', '-')}
🔧 **Услуга:** {context.user_data.get('service', '-')}
⏰ **Сроки:** {context.user_data.get('timeline', '-')}
📞 **Контакт:** {context.user_data.get('contact', '-')}

@{user.username if user.username else 'нет username'}"""

    # Отправляем менеджеру
    if MANAGER_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=MANAGER_CHAT_ID,
                text=request_text,
                parse_mode="Markdown"
            )
            logger.info(f"Request sent to manager: {user.id}")
        except Exception as e:
            logger.error(f"Failed to send to manager: {e}")
    
    # Подтверждение пользователю
    await update.message.reply_text(
        "✅ **Заявка отправлена!**\n\n"
        "Наш специалист свяжется с вами в ближайшее время.\n\n"
        "📞 Для срочной связи: 8-800-350-13-90\n"
        "📧 Email: info@arxproektstroy.ru\n\n"
        "Спасибо за обращение в ADC Group!",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
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
        parse_mode="Markdown"
    )
    return ConversationHandler.END


# ============== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ ==============
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка произвольных сообщений"""
    text = update.message.text.lower()
    
    # Простые ответы на ключевые слова
    if any(word in text for word in ["привет", "здравствуй", "добрый"]):
        await update.message.reply_text(
            "Здравствуйте! 👋\n\n"
            "Я — навигатор канала ADC Group.\n"
            "Нажмите /start для просмотра меню.",
            parse_mode="Markdown"
        )
    
    elif any(word in text for word in ["цена", "стоимость", "сколько"]):
        await update.message.reply_text(
            "💰 Стоимость зависит от типа и площади объекта.\n\n"
            "Для расчёта оставьте заявку — наш специалист "
            "подготовит коммерческое предложение.\n\n"
            "📝 /request — оставить заявку",
            parse_mode="Markdown"
        )
    
    elif any(word in text for word in ["срок", "сколько времени", "как долго"]):
        await update.message.reply_text(
            "⏰ Сроки проектирования зависят от площади и сложности объекта.\n\n"
            "Ориентировочно:\n"
            "• до 5 000 м² — от 60 дней\n"
            "• 5 000–20 000 м² — от 90 дней\n"
            "• более 20 000 м² — от 120 дней\n\n"
            "📝 Для точного расчёта: /request",
            parse_mode="Markdown"
        )
    
    elif any(word in text for word in ["контакт", "телефон", "позвонить"]):
        await update.message.reply_text(
            "📞 **Контакты ADC Group:**\n\n"
            "Телефон: 8-800-350-13-90\n"
            "Email: info@arxproektstroy.ru\n"
            "Сайт: miringgroup.com\n\n"
            "📝 Или оставьте заявку: /request",
            parse_mode="Markdown"
        )
    
    else:
        await update.message.reply_text(
            "Я могу помочь с информацией о компании и услугах.\n\n"
            "Нажмите /start для просмотра меню\n"
            "или /request чтобы оставить заявку.",
            parse_mode="Markdown"
        )


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
            CallbackQueryHandler(button_handler, pattern="^request$")
        ],
        states={
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_region)],
            OBJECT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_object_type)],
            AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_area)],
            STAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_stage)],
            SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service)],
            TIMELINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_timeline)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot ADC Navigator v1.0 started")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
