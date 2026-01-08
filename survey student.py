import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State

API_TOKEN = "7040636616:AAEQPcJRa7hEVDAVdFm8onRa0s4IfPiKPHo"

# -------------------------------
# Настройка бота
# -------------------------------
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# -------------------------------
# FSM состояния
# -------------------------------
class Survey(StatesGroup):
    q0_country = State()
    q0_institute = State()
    q0_direction = State()
    q0_level = State()
    q0_age = State()
    qid = State()

# -------------------------------
# Вопросы (id: (текст, [варианты]))
# -------------------------------
survey_questions = {
    "1": ("Какой у вас уровень владения русским языком?/What is your level of Russian language proficiency?/您的俄语水平如何？", ["Свободно/Free/流利地", "Базовый/Base/基础的", "Очень слабый/Very weak/非常低", "Не владею/I don't speak it/没有水平"]),
    "2": ("На каком языке чаще всего проводятся проектные занятия?/What language are the project-based activities you participate in most often conducted in?/您参与的项目活动中最常使用什么语言？", ["Только на русском/Only in Russian/只用俄语", "Только на английском/English only/只用英语", "Смешанно/In Russian and English (mixed)/俄语英语混合", "На другом языке/In another language/其他语言"]),
    "3": ("Чувствуете ли вы себя комфортно при общении в мультикультурной проектной группе?/Do you feel comfortable communicating in a multicultural project group?/您是否觉得在多元文化项目小组中交流舒适？", ["Да, всегда/Yes, always/是的，总是", "Иногда/Sometimes/有时候", "Редко/Rarely/很少", "Нет/No, I'm not comfortable/不，我不舒适"]),
    "4": ("С какими трудностями вы чаще всего сталкиваетесь?/What challenges do you most often encounter in project work? (You can choose several)/在项目工作中最常遇到的困难是什么？（可以多选）", ["Языковой барьер/Language barrier (difficulty expressing thoughts)/语言障碍", "Разные стили работы/Different work styles (for example, some are late, some do everything themselves)/不同的工作风格", "Непонимание задания/Misunderstanding of the assignment or assessment criteria/对任务或评估标准的误解", "Нет поддержки от преподавателя/Lack of support from the teacher/缺乏老师的支持", "Сложности с ролями/Difficulties with distributing roles in a group/团队中角色分配困难", "Другое/Other (specify)/其他（请说明）"]),
    "5": ("Получаете ли вы чёткие инструкции и критерии оценки для проектов?/Do you receive clear instructions and evaluation criteria for projects?/您是否收到明确的项目指示和评估标准？", ["Да, всегда/Yes, always/是的，总是", "Иногда/Sometimes/有时候", "Редко/Rarely/很少", "Никогда/Never/从不"]),
    "6": ("Есть ли возможность получить помощь при работе над проектом?/Do you have access to assistance (mentor, teacher, senior student) while working on your project?/在进行项目时，您是否可以获得帮助（导师、老师、学长）？", ["Да, всегда/Yes, always available/是的，随时可用", "Иногда/Sometimes I can get help/有时候我能获得帮助", "Нет/No, there is no help/不，没有帮助", "Не знаю/I don't know where to look for her/我不知道在哪寻求帮助"]),
    "7": ("Как вы оцениваете уровень межкультурного взаимодействия?/How do you rate the level of intercultural interaction in your project team?/您如何评价您的项目团队的跨文化互动水平？", ["Очень высокий/Very high - we discuss cultural differences and take them into account/非常高 - 我们讨论文化差异并将其考虑在内", "Умеренный/Moderate - we work, but rarely talk about culture/中等——我们工作，但很少谈论文化", "Низкий/Low - we try to avoid cultural topics/低 - 我们尽量避免文化话题", "Не замечаю/I don't notice any intercultural aspect/我没有注意到任何跨文化方面"]),
    "8": ("Хотели бы вы участвовать в проектах с международными вузами?/Would you like to participate in projects with international universities (e.g. virtual exchanges, joint assignments)?/您想参与国际大学的项目（例如虚拟交流、联合作业）吗？", ["Да/Yes, very interesting/是的，非常感兴趣", "Возможно/Perhaps, if there is support/也许，如果有支持", "Нет/No, it will make the job more difficult/不，这会使工作更加困难", "Не знаю/Don't know/我不知道"]),
    "9": ("Какой формат проектного обучения наиболее удобен?/Which project-based learning format do you find most convenient?/您认为哪种基于项目的学习形式最方便？", ["Групповой/Group project with international and local students/与国际和本地学生的小组项目", "Только с иностранцами/A project with only international students/仅限外国学生的项目", "Индивидуальный/Individual project with teacher support/教师支持下的个人项目", "Междисциплинарный модуль/An interdisciplinary modular course with step-by-step assignments/跨学科模块化课程，包含分步作业"]),
    "10": ("Какие меры поддержки наиболее полезны?/What support measures do you find most useful for international students in project-based learning? (You can select more than one)/您认为哪些支持措施对国际学生在项目式学习中最有帮助？（可多选）", ["Языковые воркшопы/Language workshops (Russian/English for academic communication)/语言研讨会（俄语/英语用于学术交流）", "Культурные брифинги/Cultural briefings before the start of the project/项目开始前的文化简报", "Наставник/Assigning a mentor (teacher or student)/指定导师（老师或学生）", "Чёткие rubrics/Clear rubrics (rating scales) in understandable language/用易懂的语言明确评分标准（评分量表）", "Часть работы на английском/Possibility to submit part of the work in English/可以提交部分英文作品", "Другое/Other (specify)/其他（请说明）"]),
    "11": ("Какие технологии искусственного интеллекта вы используете для поддержки своей проектной работы?/What AI tools do you use (or could you use) to support your project work? (You can choose more than one)/您使用（或可以使用）哪些AI工具来支持您的项目工作？（您可以选择多个）", ["Переводчики/AI-based translators (e.g. DeepL, Google Translate)/基于人工智能的翻译器（例如 DeepL、谷歌翻译）", "Ассистенты для текстов/AI copywriting assistants (e.g., ChatGPT, DeepSeek, Gemini)/AI 文案助手（例如 ChatGPT、DeepSeek、Gemini）", "Презентации с поддержкой технологий искусственного интеллекта/AI-powered presentation tools (e.g., Gamma, Canva AI)/AI 演示工具（例如 Gamma、Canva AI）", "Грамматические корректоры/Grammar proofreaders (e.g. Grammarly)/语法校对员（例如 Grammarly）", "Не использую/I don't use AI tools/我不用人工智能工具", "Другое/Other (specify)/其他（请说明）"]),
    "12": ("Могут ли технологии искусственного интеллекта помочь вам преодолеть языковые и культурные барьеры в проектном обучении?/Do you think AI technologies can help overcome language and cultural barriers in project-based learning?/您认为人工智能技术可以帮助您克服基于项目学习中的语言和文化障碍吗？", ["Да, значительно помогают/Yes, they help significantly—for example, through instant translation and adaptation of content/是的，它们提供了很大帮助——例如，通过即时翻译和调整内容", "Отчасти/AI helps with language, but not with cultural nuances/部分原因——人工智能有助于语言理解，但无助于文化差异", "Нет/No, AI doesn't understand cultural context and can be misleading/不——人工智能不理解文化背景，可能会产生误导", "Затрудняюсь/I find it difficult to answer/我觉得很难回答"]),
}

multi_choice = {"4", "10", "11"}

# -------------------------------
# База данных
# -------------------------------
conn = sqlite3.connect("survey.db")
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS answers (
    user_id INTEGER,
    question TEXT,
    answer TEXT
)""")
conn.commit()

def save_answer(user_id, qid, qtext, ans):
    cur.execute("INSERT INTO answers VALUES (?, ?, ?)", (user_id, qtext, ans))
    conn.commit()

# -------------------------------
# Вопросы с кнопками
# -------------------------------
async def ask_question(message, state, qid):
    qtext, options = survey_questions[qid]
    if options:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=opt, callback_data=f"{qid}:{i}")]
                for i, opt in enumerate(options)
            ]
        )
        if qid in multi_choice:
            kb.inline_keyboard.append([InlineKeyboardButton(text="✅ Завершить выбор/✅ Complete your selection/✅ 完成选择", callback_data=f"{qid}:done")])
        await message.answer(f"Вопрос {qid} из 12:\n{qtext}", reply_markup=kb)
    else:
        await message.answer(f"Вопрос {qid} из 12:\n{qtext}")

async def next_question(message, state):
    data = await state.get_data()
    current_q = data.get("current_q", 1)
    if int(current_q) > len(survey_questions):
        await message.answer("Спасибо за участие! 🙏 Ваши ответы сохранены./Thank you for participating! 🙏 Your answers have been saved./感谢您的参与！🙏 您的答案已保存。")
        await state.clear()
    else:
        await ask_question(message, state, str(current_q))

# -------------------------------
# Обработчики
# -------------------------------
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    welcome_text = (
        "👋 Всем привет! Hi everyone! 大家好！\n\n"
        "Меня зовут Лю Юаньчжи, я аспирант ИРИТ-РТФ УрФУ. My name is Liu Yuanzhi. I'm a PHD student at UrFU's IRIT-RTF. 我叫刘远之，我是乌拉尔联邦大学无线电和信息技术学院博士。\n\n"
        "Сам как иностранный студент, знаю, как непросто бывает в проектной работе: язык, культура, разные стили учёбы. As a foreign student myself, I know how difficult project work can be: language, culture, different learning styles. 作为一名外国学生，我知道项目工作有多么困难：语言、文化、不同的学习风格。\n\n"
        "Провожу исследование по проектному обучению в международной среде. I am conducting research on project-based learning in an international environment. 我正在国际环境中进行基于项目的学习研究。"
        "Хочу понять, какие практики реально помогают. I want to understand which practices really help. 我想了解哪些做法真正有帮助。\n\n"
        "Пройдите короткий опрос (12 вопросов, 5 минут). Take a short survey (12 questions, 5 minutes). 参加一个简短的调查（12 个问题，5 分钟）。"
        "Ваши ответы помогут сделать обучение удобнее для всех иностранных студентов. Your answers will help make learning more convenient for all international students. 您的回答将有助于所有国际学生更加方便地学习。\n\n"
        "Особенно интересно ваше мнение о технологиях искусственного интеллекта в учёбе — могут ли они помочь преодолеть барьеры? I'm particularly interested in your opinion on artificial intelligence technologies in education—can they help overcome barriers? 我特别感兴趣的是您对教育领域人工智能技术的看法——它们能帮助克服障碍吗？\n\n"
        "🌍 Из какой вы страны? What country are you from? 您来自哪个国家？"
    )
    await message.answer(welcome_text)
    await state.set_state(Survey.q0_country)

@dp.message(Survey.q0_country)
async def process_country(message: types.Message, state: FSMContext):
    save_answer(message.from_user.id, "0.1", "Страна", message.text)
    await message.answer("В каком институте вы учитесь? What institute do you attend? (Hint: Podfak, IRIT-RTF, UGI, etc.) 您在大学的哪个学院学习？")
    await state.set_state(Survey.q0_institute)

@dp.message(Survey.q0_institute)
async def process_institute(message: types.Message, state: FSMContext):
    save_answer(message.from_user.id, "0.2", "Институт", message.text)
    await message.answer("В каком направлении вы учитесь? What field are you studying? (Hints: Russian as a Foreign Language, Software Engineering, etc.) 您是哪个专业方向的？")
    await state.set_state(Survey.q0_direction)

@dp.message(Survey.q0_direction)
async def process_direction(message: types.Message, state: FSMContext):
    save_answer(message.from_user.id, "0.3", "Направление", message.text)
    await message.answer("На каком уровне образования вы обучаетесь? What level of education are you studying at? (bachelor's, specialist, master's, PHD) 您读哪个学历？（本科，专家，硕士，博士）")
    await state.set_state(Survey.q0_level)

@dp.message(Survey.q0_level)
async def process_level(message: types.Message, state: FSMContext):
    save_answer(message.from_user.id, "0.4", "Уровень", message.text)
    await message.answer("Сколько вам полных лет? How old are you (number)? 您多大（数字）？")
    await state.set_state(Survey.q0_age)

@dp.message(Survey.q0_age)
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число (ваш возраст). Please enter a number (your age). 请输入数字（您的年龄）。")
        return
    save_answer(message.from_user.id, "0.5", "Возраст", message.text)
    await state.update_data(current_q=1)
    await next_question(message, state)

@dp.callback_query(F.data)
async def callbacks(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data
    qid, ans_idx = data.split(":", 1)
    qtext, options = survey_questions[qid]

    if ans_idx == "done":
        user_data = await state.get_data()
        answers = user_data.get(f"answers_{qid}", [])
        save_answer(callback.from_user.id, qid, qtext, "; ".join(answers))
        await callback.message.answer("Ответ сохранён ✅ Answer saved 答案已保存")
        await state.update_data(current_q=int(qid) + 1)
        await next_question(callback.message, state)
        await callback.answer()
        return

    ans = options[int(ans_idx)]

    if qid in multi_choice:
        user_data = await state.get_data()
        answers = user_data.get(f"answers_{qid}", [])
        if ans not in answers:
            answers.append(ans)
        await state.update_data(**{f"answers_{qid}": answers})
        await callback.answer("Добавлено ✅ Added 已添加")
    else:
        save_answer(callback.from_user.id, qid, qtext, ans)
        await state.update_data(current_q=int(qid) + 1)
        await next_question(callback.message, state)
        await callback.answer()

# -------------------------------
# Запуск
# -------------------------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
