import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime

logging.basicConfig(level=logging.INFO)

API_TOKEN = "8582672174:AAE1qqXMm1oBM6qpW7lm_YehWzuTZJPsZmo"
ADMIN_GROUP_ID = -5126218596  # ID группы REMPHONE

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

requests_db = {}
request_counter = 1

class RequestForm(StatesGroup):
    city = State()
    brand = State()
    problem = State()
    phone = State()

def get_main_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📋 Заявка"), types.KeyboardButton(text="❓ FAQ")],
            [types.KeyboardButton(text="📊 Калькулятор"), types.KeyboardButton(text="🎁 Акции")],
            [types.KeyboardButton(text="📍 Карта"), types.KeyboardButton(text="⭐ Отзывы")],
            [types.KeyboardButton(text="🔍 Статус"), types.KeyboardButton(text="📞 Контакты")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_city_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Хабаровск"), types.KeyboardButton(text="Владивосток")],
            [types.KeyboardButton(text="Комсомольск-на-Амуре"), types.KeyboardButton(text="Благовещенск")],
            [types.KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_brand_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="iPhone"), types.KeyboardButton(text="Samsung")],
            [types.KeyboardButton(text="Xiaomi"), types.KeyboardButton(text="Huawei")],
            [types.KeyboardButton(text="Android"), types.KeyboardButton(text="Другой")],
            [types.KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_problem_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Разбит экран"), types.KeyboardButton(text="Батарея")],
            [types.KeyboardButton(text="Не заряжается"), types.KeyboardButton(text="Попал в воду")],
            [types.KeyboardButton(text="Нет звука"), types.KeyboardButton(text="Камера")],
            [types.KeyboardButton(text="Тормозит"), types.KeyboardButton(text="Другое")],
            [types.KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_cancel_keyboard():
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="❌ Отменить")]],
        resize_keyboard=True
    )
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = f"""👋 Привет, {message.from_user.first_name}!

🔧 Я бот REMPHONE RUSSIA

✅ Оставить заявку на ремонт
✅ Узнать цену ремонта
✅ Найти ближайший салон
✅ Получить консультацию

📲 Выбери раздел ниже!"""
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@dp.message(lambda message: message.text == "📋 Заявка")
async def start_request(message: types.Message, state: FSMContext):
    await message.answer("Выбери свой город:", reply_markup=get_city_keyboard())
    await state.set_state(RequestForm.city)

@dp.message(RequestForm.city)
async def process_city(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await state.clear()
        await message.answer("В главное меню", reply_markup=get_main_keyboard())
        return
    
    await state.update_data(city=message.text)
    await message.answer("Выбери бренд:", reply_markup=get_brand_keyboard())
    await state.set_state(RequestForm.brand)

@dp.message(RequestForm.brand)
async def process_brand(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await message.answer("Выбери город:", reply_markup=get_city_keyboard())
        await state.set_state(RequestForm.city)
        return
    
    await state.update_data(brand=message.text)
    await message.answer("Что случилось?", reply_markup=get_problem_keyboard())
    await state.set_state(RequestForm.problem)

@dp.message(RequestForm.problem)
async def process_problem(message: types.Message, state: FSMContext):
    if message.text == "🔙 Назад":
        await message.answer("Выбери бренд:", reply_markup=get_brand_keyboard())
        await state.set_state(RequestForm.brand)
        return
    
    await state.update_data(problem=message.text)
    await message.answer("Номер телефона:\nФормат: 89502851192", reply_markup=get_cancel_keyboard())
    await state.set_state(RequestForm.phone)

@dp.message(RequestForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    global request_counter
    
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer("❌ Отменено", reply_markup=get_main_keyboard())
        return
    
    phone = message.text.strip()
    
    if not phone.isdigit() or len(phone) < 10:
        await message.answer("❌ Неверный формат! 89502851192")
        return
    
    data = await state.get_data()
    city = data.get("city")
    brand = data.get("brand")
    problem = data.get("problem")
    
    request_id = f"REQ{request_counter:04d}"
    request_counter += 1
    
    requests_db[request_id] = {
        "user_id": message.from_user.id,
        "username": message.from_user.username or "нет",
        "full_name": message.from_user.full_name,
        "city": city,
        "brand": brand,
        "problem": problem,
        "phone": phone,
        "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "status": "Новая"
    }
    
    admin_message = f"""🔔 НОВАЯ ЗАЯВКА #{request_id}

👤 Клиент: {message.from_user.full_name}
📱 @{message.from_user.username or 'нет'}
🆔 ID: {message.from_user.id}

📍 Город: {city}
📱 Бренд: {brand}
🔧 Проблема: {problem}
📞 Тел: {phone}

⏰ {datetime.now().strftime("%d.%m.%Y %H:%M")}

💬 Написать: tg://user?id={message.from_user.id}"""
    
    try:
        await bot.send_message(ADMIN_GROUP_ID, admin_message)
        print(f"✅ Заявка {request_id} отправлена в группу")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    await message.answer(
        f"✅ ЗАЯВКА ПРИНЯТА!\n\n"
        f"📋 Номер: {request_id}\n"
        f"📍 Город: {city}\n"
        f"📱 Бренд: {brand}\n"
        f"🔧 Проблема: {problem}\n"
        f"📞 Телефон: {phone}\n\n"
        f"⏰ Ответим за 15 минут!",
        reply_markup=get_main_keyboard()
    )
    
    await state.clear()

@dp.message(lambda message: message.text == "❓ FAQ")
async def faq(message: types.Message):
    text = """❓ ЧАСТО СПРАШИВАЮТ

💔 Экран: 3500-9000₽
🔋 Батарея: 1200-2500₽
🔌 Зарядка: 1500-3500₽
💧 Влага: 2000-4000₽

⏰ Ремонт: 30-60 минут
✅ Гарантия: 1 год
🚗 Выезд: БЕСПЛАТНО от 2000₽
💳 Рассрочка: 0% на 3 месяца"""
    
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(lambda message: message.text == "📊 Калькулятор")
async def calculator(message: types.Message):
    text = """📊 ПРИМЕРНЫЕ ЦЕНЫ

💔 ЭКРАН:
• iPhone: 6500-9000₽
• Samsung: 4500-6500₽
• Xiaomi: 3500-5000₽

🔋 БАТАРЕЯ:
• iPhone: 1800-2500₽
• Samsung: 1500-2200₽
• Xiaomi: 1200-1800₽

🔌 РАЗЪЕМ: 1500-3500₽
💧 ВЛАГА: 2000-4000₽

💬 Точная цена в заявке!"""
    
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(lambda message: message.text == "🎁 Акции")
async def promotions(message: types.Message):
    text = """🎁 ФЕВРАЛЬ 2026

🔥 -10% первый ремонт
👥 -5% приведи друга
⚡ Батарея от 1200₽
🚗 Выезд бесплатно
💳 Рассрочка 0%"""
    
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(lambda message: message.text == "📍 Карта")
async def map_salons(message: types.Message):
    text = """📍 ТОП-3 САЛОНА

1️⃣ IMAG27
☎️ +7(4212)663663
📍 ул.Серышева, 46

2️⃣ Pedant.ru
☎️ +7(4212)529345
📍 7 филиалов

3️⃣ Спринтер
☎️ +7(924)2112560
📍 5 филиалов"""
    
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(lambda message: message.text == "⭐ Отзывы")
async def reviews(message: types.Message):
    text = """⭐ ОТЗЫВЫ

💬 "Спасли iPhone за 2 часа! 10/10"
— Иван, 28

💬 "Батарея за 40 минут. Как новый!"
— Мария, 35

💬 "Упал в воду, спасли. Спасибо!"
— Дмитрий, 42

📊 4.9/5 | 5000+ клиентов"""
    
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(lambda message: message.text == "🔍 Статус")
async def check_status(message: types.Message):
    user_id = message.from_user.id
    user_requests = {k: v for k, v in requests_db.items() if v["user_id"] == user_id}
    
    if not user_requests:
        await message.answer("❌ Нет заявок", reply_markup=get_main_keyboard())
        return
    
    last_req_id = list(user_requests.keys())[-1]
    req = user_requests[last_req_id]
    
    text = f"""🔍 СТАТУС

📋 Номер: {last_req_id}
📍 Город: {req['city']}
📱 Бренд: {req['brand']}
🔧 Проблема: {req['problem']}
📞 Телефон: {req['phone']}
⏰ Создана: {req['timestamp']}
📊 Статус: {req['status']}"""
    
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(lambda message: message.text == "📞 Контакты")
async def contacts(message: types.Message):
    text = """📞 КОНТАКТЫ

💬 Telegram: @REMPHONE_RUSSIA
📱 Телефон: +7(4212)663663
⏰ Работа: 9:00-22:00
🏢 Хабаровск"""
    
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message()
async def echo(message: types.Message):
    await message.answer("Используй меню ниже ↓", reply_markup=get_main_keyboard())

async def main():
    print("=" * 50)
    print("🚀 БОТ REMPHONE ЗАПУЩЕН!")
    print("=" * 50)
    print("✅ Заявки отправляются в группу")
    print("⏰ Бот работает 24/7")
    print("=" * 50)
    
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Бот остановлен")
