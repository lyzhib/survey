import asyncio
import gspread
from google.oauth2.service_account import Credentials
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ================== НАСТРОЙКИ ==================
API_TOKEN = "7040636616:AAEQPcJRa7hEVDAVdFm8onRa0s4IfPiKPHo"  # ← замените на токен вашего бота
SHEET_NAME = "survey results"  # ← название вашей таблицы
SERVICE_FILE = "credentials.json"  # ← путь к JSON-файлу сервисного аккаунта

# подключение к Google Sheets
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file(SERVICE_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open(SHEET_NAME).sheet1

# инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

user_data = {}

# ================== ВОПРОСЫ ==================
questions = [
    ("1️⃣ должность и место работы", None, False),
    ("2️⃣ Сколько лет вы работаете в вузе?",
     ["Менее 3 лет", "3–5 лет", "6–10 лет", "Более 10 лет"], False),
    ("3️⃣ Есть ли у вас опыт участия в проектном обучении?",
     ["Да", "Нет"], False),
    ("4️⃣ В каких форматах проектного обучения вы участвовали? (можно выбрать несколько)",
     ["Курсовые задания", "Междисциплинарные проекты", "Хакатоны / интенсивы",
      "Капстоуны / выпускные проекты", "Проекты с внешними заказчиками"], True),
    ("5️⃣ Какова была ваша роль в проекте?",
     ["Руководитель проекта", "Наставник / куратор команды", "Координатор программы", "Эксперт / оценщик"], False),
    ("6️⃣ Как вы оцениваете эффективность проектного обучения?",
     ["Очень высокая", "Скорее высокая", "Средняя", "Низкая"], False),
    ("7️⃣ Какие ключевые навыки, по вашему мнению, развивает проектная деятельность у студентов?", None, False),
    ("8️⃣ С какими основными трудностями вы сталкивались при организации или сопровождении проектов?", None, False),
    ("9️⃣ Как часто вы работаете с командами из нескольких образовательных направлений?",
     ["Часто", "Иногда", "Редко", "Никогда"], False),
    ("🔟 Какие факторы, на ваш взгляд, наиболее важны для успешной работы проектной команды? (можно выбрать несколько)",
     ["Чёткое распределение ролей", "Мотивация участников", "Поддержка наставника",
      "Эффективная коммуникация", "Управление временем", "Понимание целей проекта"], True),
    ("11️⃣ Какие инструменты или методы вы используете для сопровождения проектных команд?", None, False),
    ("12️⃣ Есть ли у вас опыт участия иностранных студентов в ваших проектах?",
     ["Да, регулярно", "Да, иногда", "Нет"], False),
    ("13️⃣ Какие сложности чаще всего возникают при работе с иностранными студентами в проектных командах? (можно выбрать несколько)",
     ["Языковой барьер", "Различия в академических культурах", "Разные подходы к командной работе",
      "Проблемы с вовлечённостью", "Трудности с коммуникацией внутри команды"], True),
    ("14️⃣ Что помогает преодолевать эти сложности?", None, False),
    ("15️⃣ Какие меры, по вашему мнению, могли бы повысить эффективность участия иностранных студентов в проектном обучении?", None, False),
    ("16️⃣ Что, на ваш взгляд, следует улучшить в организации проектного обучения в вашем вузе?", None, False),
    ("17️⃣ Используете ли вы технологии искусственного интеллекта (например, генеративные модели, чат-боты, аналитические ИИ-инструменты) в своей преподавательской или проектной деятельности?",
     ["Да, регулярно", "Да, иногда", "Нет, но планирую", "Нет и не планирую"], False),
    ("18️⃣ В каких аспектах своей работы вы применяете ИИ-инструменты? (можно выбрать несколько)",
     ["Подготовка учебных материалов", "Оценка студенческих работ", "Обратная связь студентам",
      "Организация проектной деятельности", "Поддержка командной коммуникации",
      "Анализ данных проектов", "Другое (укажите)"], True),
    ("19️⃣ Использовали ли вы ИИ-инструменты при работе с международными или мультикультурными студенческими командами?",
     ["Да", "Нет", "Не уверен(а)"], False),
    ("20️⃣ Какие преимущества или проблемы, по вашему мнению, ИИ может дать в контексте проектного обучения?", None, False),
    ("21️⃣ Какие риски или трудности вы видите в использовании ИИ в образовательных проектах?", None, False),
    ("22️⃣ Нуждаетесь ли вы в дополнительной поддержке или обучении для эффективного использования ИИ в преподавании и проектной работе?",
     ["Да", "Нет", "Затрудняюсь ответить"], False),
]


# ================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==================
def make_inline_keyboard(options, selected=None, multiple=False):
    kb = InlineKeyboardBuilder()
    selected = selected or []
    for i, opt in enumerate(options):
        text = f"✅ {opt}" if opt in selected else opt
        kb.button(text=text, callback_data=f"select:{i}")  # короткие callback_data
    if multiple:
        kb.button(text="➡️ Далее", callback_data="next")
    kb.adjust(1)
    return kb.as_markup()


async def send_question(uid, message_or_call):
    step = user_data[uid]["step"]
    q_text, options, multiple = questions[step]
    progress = f"\n\n📊 Вопрос {step + 1} из {len(questions)}"
    text = q_text + progress

    if options:
        markup = make_inline_keyboard(options, user_data[uid].get("selected", []), multiple)
        if isinstance(message_or_call, CallbackQuery):
            await message_or_call.message.edit_text(text, reply_markup=markup)
        else:
            await message_or_call.answer(text, reply_markup=markup)
    else:
        if isinstance(message_or_call, CallbackQuery):
            await message_or_call.message.edit_text(text)
        else:
            await message_or_call.answer(text)


# ================== ХЭНДЛЕРЫ ==================
@dp.message(Command("start"))
async def start(message: Message):
    uid = message.from_user.id
    user_data[uid] = {"step": 0, "answers": [], "selected": []}
    await message.answer("Здравствуйте! 👋 Давайте пройдём короткий опрос преподавателей.")
    await send_question(uid, message)


@dp.callback_query(lambda c: c.data.startswith("select:"))
async def handle_select(call: CallbackQuery):
    uid = call.from_user.id
    step = user_data[uid]["step"]
    _, options, multiple = questions[step]

    value_index = int(call.data.split("select:")[1])
    selected_value = options[value_index]

    if multiple:
        selected = user_data[uid].get("selected", [])
        if selected_value in selected:
            selected.remove(selected_value)
        else:
            selected.append(selected_value)
        user_data[uid]["selected"] = selected
        markup = make_inline_keyboard(options, selected, multiple)
        await call.message.edit_reply_markup(reply_markup=markup)
        await call.answer()
    else:
        user_data[uid]["answers"].append(selected_value)

        # 🟩 Условие: если вопрос 12 и ответ "Нет" → перескочить к 16
        if step == 11 and selected_value == "Нет":
            user_data[uid]["step"] = 15  # индекс вопроса №16
        else:
            user_data[uid]["step"] += 1

        if user_data[uid]["step"] < len(questions):
            await send_question(uid, call)
        else:
            save_to_gsheets(call.from_user.full_name, user_data[uid]["answers"])
            await call.message.edit_text("Спасибо большое за помощь в проведении исследований!")
            del user_data[uid]


@dp.callback_query(lambda c: c.data == "next")
async def handle_next(call: CallbackQuery):
    uid = call.from_user.id
    selected = user_data[uid].get("selected", [])
    user_data[uid]["answers"].append(", ".join(selected))
    user_data[uid]["selected"] = []
    user_data[uid]["step"] += 1
    if user_data[uid]["step"] < len(questions):
        await send_question(uid, call)
    else:
        save_to_gsheets(call.from_user.full_name, user_data[uid]["answers"])
        await call.message.edit_text("Спасибо большое за помощь в проведении исследований!")
        del user_data[uid]


@dp.message()
async def handle_text(message: Message):
    uid = message.from_user.id
    if uid not in user_data:
        return await message.answer("Введите /start, чтобы начать опрос.")
    step = user_data[uid]["step"]
    q_text, options, multiple = questions[step]
    if options:
        return await message.answer("Выберите вариант с помощью кнопок ниже 👇")

    user_data[uid]["answers"].append(message.text)
    user_data[uid]["step"] += 1
    if user_data[uid]["step"] < len(questions):
        await send_question(uid, message)
    else:
        save_to_gsheets(message.from_user.full_name, user_data[uid]["answers"])
        await message.answer("Спасибо большое за помощь в проведении исследований!")
        del user_data[uid]


# ================== СОХРАНЕНИЕ В GOOGLE SHEETS ==================
def save_to_gsheets(name, answers):
    row = [name] + [a if a else "" for a in answers]
    sheet.append_row(row)


# ================== ЗАПУСК ==================
async def main():
    print("🤖 Бот запущен и сохраняет ответы в Google Sheets...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
