import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message
from aiogram.filters import CommandStart
import asyncio
import aiosqlite
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# === НАСТРОЙКИ ===
API_TOKEN = '7040636616:AAEQPcJRa7hEVDAVdFm8onRa0s4IfPiKPHo'
ADMIN_ID = 5188394092  # ← Укажи свой Telegram ID
SHEET_NAME = "Вопросы от студентов"  # Название Google таблицы

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(level=logging.INFO)

# === ИНИЦИАЛИЗАЦИЯ БОТА ===
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# === GOOGLE SHEETS ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
gs_client = gspread.authorize(creds)
sheet = gs_client.open(SHEET_NAME).sheet1

# === ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ ===
faq = {
    "паспорт проекта": "Паспорт проекта — это документ, в котором описаны цели, задачи, сроки реализации и т.д.",
    "сроки": "Актуальные сроки подачи паспортов можно найти на сайте вуза или уточнить у координатора.",
    "цель проекта": "Цель проекта — это основная идея, которую вы реализуете. Опишите её кратко и понятно."
}

# === ИНИЦИАЛИЗАЦИЯ БД ===
async def init_db():
    async with aiosqlite.connect("questions.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                question TEXT,
                answer TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

# === СОХРАНЕНИЕ ВОПРОСА В БД ===
async def save_to_db(user_id, username, question, answer):
    async with aiosqlite.connect("questions.db") as db:
        await db.execute("""
            INSERT INTO questions (user_id, username, question, answer)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, question, answer))
        await db.commit()

# === ЭКСПОРТ В GOOGLE SHEETS ===
async def export_to_gsheet(user_id, username, question, answer):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [timestamp, user_id, username or "", question, answer or ""]
    sheet.append_row(row)

# === ОБРАБОТЧИК КОМАНДЫ /start ===
@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Здравствуйте! Я помогу вам с вопросами по паспортам проектов. Просто напишите свой вопрос.")

# === ОБРАБОТЧИК ВСЕХ ВОПРОСОВ ===
@router.message(F.text)
async def handle_question(message: Message):
    user_question = message.text.lower()
    user_id = message.from_user.id
    username = message.from_user.username

    # Проверка по FAQ
    for keyword in faq:
        if keyword in user_question:
            answer = faq[keyword]
            await save_to_db(user_id, username, message.text, answer)
            await export_to_gsheet(user_id, username, message.text, answer)
            await message.reply(answer)
            return

    # Если нет готового ответа
    fallback = "Спасибо! Ваш вопрос передан куратору. Ожидайте ответа."
    await save_to_db(user_id, username, message.text, None)
    await export_to_gsheet(user_id, username, message.text, None)
    await message.reply(fallback)

    await bot.send_message(ADMIN_ID, f"❓ Новый вопрос от @{username or 'без_ника'}:\n\n{message.text}")

# === ТОЧКА ВХОДА ===
async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
