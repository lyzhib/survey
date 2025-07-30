import logging
import asyncio
import aiosqlite
import aiohttp
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === НАСТРОЙКИ ===
API_TOKEN = '7040636616:AAEQPcJRa7hEVDAVdFm8onRa0s4IfPiKPHo'
ADMIN_ID = 5188394092  # ← Укажи свой Telegram ID
SHEET_NAME = "Вопросы от студентов"  # Название таблицы
OPENROUTER_API_KEY = "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"  # ← Укажи актуальный ключ OpenRouter

# === ИНИЦИАЛИЗАЦИЯ БОТА ===
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# === ЛОГИРОВАНИЕ ===
logging.basicConfig(level=logging.INFO)

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

# === СОХРАНЕНИЕ В БД ===
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

# === ЗАПРОС К DEEPSEEK ЧЕРЕЗ OPENROUTER ===
async def get_deepseek_response(question: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "Referer": "https://chat.openai.com"  # Можно заменить на свой домен
    }
    data = {
        "model": "deepseek/deepseek-chat-v3-0324:free",  # ✅ исправленный ID
        "messages": [
            {"role": "system", "content": "Ты дружелюбный помощник для иностранных студентов по вопросам паспортов проектов."},
            {"role": "user", "content": question}
        ]
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as resp:
            if resp.status != 200:
                text = await resp.text()
                logging.error(f"[OpenRouter Error {resp.status}] {text}")
                return "⚠️ Не удалось получить ответ от DeepSeek. Попробуйте позже."
            result = await resp.json()
            return result["choices"][0]["message"]["content"].strip()

# === /start ===
@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Здравствуйте! Я помогу вам с вопросами по паспортам проектов. Просто напишите свой вопрос.")

# === ОБРАБОТЧИК ВОПРОСОВ ===
@router.message(F.text)
async def handle_question(message: Message):
    user_question = message.text
    user_id = message.from_user.id
    username = message.from_user.username or ""

    for keyword in faq:
        if keyword in user_question.lower():
            answer = faq[keyword]
            await save_to_db(user_id, username, user_question, answer)
            await export_to_gsheet(user_id, username, user_question, answer)
            await message.reply(answer)
            return

    answer = await get_deepseek_response(user_question)

    await save_to_db(user_id, username, user_question, answer)
    await export_to_gsheet(user_id, username, user_question, answer)
    await message.reply(answer)

    await bot.send_message(
        ADMIN_ID,
        f"📩 Вопрос от @{username or 'без_ника'}:\n{user_question}\n\n🤖 Ответ: {answer}"
    )

# === ЗАПУСК ===
async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
