import logging
import random

from aiogram import Bot, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from db import BotDB

from config import TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

BotDB = BotDB('database.db')

class Wait(StatesGroup):
    choosing_gender = State()
    choosing_interest = State()
    name = State()
    age = State()
    city = State()
    text = State()
    photo = State()
    menu_answer = State()
    my_anketa_answer = State()
    change_text = State()
    change_photo = State()
    delete_confirm = State()
    anketa_reaction = State()

@dp.message_handler(Command('start'))
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    btn1 = types.KeyboardButton('Contact', callback_data='Contact')
    btn2 = types.KeyboardButton('Знакомства', callback_data='Znakomstva')
    btn3 = types.KeyboardButton('', callback_data='')
    btn4 = types.KeyboardButton('', callback_data='')
    btn5 = types.KeyboardButton('', callback_data='')
    markup.add(btn1, btn2, btn3, btn4, btn5)

    await message.answer("Добро пожаловать!", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == 'Contact')
async def process_callback_contact(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('Telegram', url='https://t.me/Mancionde')
    btn2 = types.InlineKeyboardButton('Discord', url='https://discord.gg/WG6fpxzjvh')
    markup.add(btn1, btn2)

    await bot.send_message(callback_query.from_user.id, 'Мои данные', reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == 'Znakomstva')
async def znakomstva(callback_query: types.CallbackQuery):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    btn1 = types.KeyboardButton('Посмотреть профиль', callback_data='Profil')
    btn2 = types.KeyboardButton('Моя анкета', callback_data='Anketa')
    btn3 = types.KeyboardButton('Удалить анкету', callback_data='delete')
    markup.add(btn1, btn2, btn3)
    await bot.send_message(callback_query.from_user.id, 'Выберите действие', reply_markup=markup)

main_text = '1. Смотреть анкеты\n2. Моя анкета\n3. Удалить анкету'
profile_text = '1. Заполнить анкету заново\n2. Изменить текст анкеты\n3. Изменить фото\n4. Вернутся назад'


def show_profile(name, age, city, text):
    return f'{name}\n{age}\n{city}\n{text}'

def get_random_anketa(list_of_anketi):
    anketa = list_of_anketi[random.randint(0, len(list_of_anketi) - 1)]
    a = anketa
    return [show_profile(a[2], a[3], a[4], a[5]), BotDB.get_photo_id(a[1])]

@dp.callback_query_handler(lambda c: c.data == 'anketa' , state='*')
async def anketa_start(callback_query: types.CallbackQuery):
    if not BotDB.user_exists(callback_query.from_user.id):
        BotDB.add_user(callback_query.from_user.id)
    if BotDB.anketa_exists(callback_query.from_user.id):
        anketa = BotDB.get_anketa(callback_query.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])
        await bot.send_photo(photo=open(f'photos/{callback_query.from_user.id}.jpg', 'rb'), chat_id=callback_query.from_user.id, caption=caption)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3"]
        keyboard.add(*buttons)

        await message.answer(main_text, reply_markup = keyboard)
        await Wait.menu_answer.set()
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['Парень', 'Девушка']
        keyboard.add(*buttons)

        await message.answer('Заполним анкету!\nДля начала выберите свой пол', reply_markup = keyboard)
        await Wait.choosing_gender.set()

@dp.message_handler(state=choosing_gender)
async def choose_gender(message: types.Message, state=FSMContext):
    if message.text not in ['Парень', 'Девушка']:
        await message.answer('Выберите пол: ')
        return
    await state.update_data(gender = message.text.lower())

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Парни", "Девушки"]
    keyboard.add(*buttons)
    await message.answer("Кто тебя интересует?", reply_markup = keyboard)
    await Wait.choosing_interest.set()
    
    

@dp.message_hanlder(state = Wait.choosing_interest)
async def choose_interest(message: types.Message, state: FSMContext):
    if message.text == 'Парни' or message.text == 'Девушки':
        await state.update_data(interest = message.text.lower())
        await message.answer('Как вас зовут?', reply_markup= types.ReplyKeyboardRemove())
    else:
        await message.answer('Выберите вариант из кнопок ниже')
        return

@dp.message_handler(state = Wait.name)
async def name(message: types.Message, state: FSMContext):
    if len(message.text) > 30:
        await message.answer('Слишком мнго букв')
        return
        await message.answer('Сколько тебе лет?')
        await Wait.age.set()

@dp.message_handler(state=Wait.age)
async def age(message: types.Message, state: FSMContext):
    try:
        if  int(message.text) < 18:
            await message.answer('Тебе еще нету 18 лет')
        elif int(message.text) >= 30:
            await message.answer('Ты уже старше 30 лет')
        return

    except(ValueError, TypeError):
        await message.answer('Какойто страный возраст?')
        return
    await state.update_data(age = message.text.lower())
    await message.answer('Напишете город или страну')
    await Wait.city.set()

@dp.message_handlers(state = Wait.city)
async def city(message: types.Message, state: FSMContext):
    if len(message.text) > 30:
        await message.answer('Слишком много букв')
        return

    await state.update_data(city = message.text.lower())
    await message.answer('Введите описание анкеты до 100 символов. Можно пропустить.', reply_markup = keyboard)
    await Wait.text.set()

@dp.message_handlers(state = Wait.text)
async def text(message: types.Message, state: FSMContext):
    if message.text == 'Оставить пустым':
        await state.update_data(text = '')
    else:
        if len(message.text) > 100:
            await message.answer('Описание должно быть длинной до 100 символов')
            return
        await state.update_data(text = message.text)
    await message.answer('Загрузить фото', reply_markup=types.ReplyKeyboardMarkup())
    await Wait.photo.set()

@dp.message_handler(state= Wait.photo)
async def photo(message:types.Message, state: FSMContext):
    await message.photo[-1].download(destination_file=f"photos/{message.from_user.id}.jpg")
    data = await state.get_data()
    d = list(data.values())
    print(d)

    BotDB.add_anketa(message.from_user.id, d[0], d[1], d[2], d[3], d[4], d[5])
    caption = show_profile(d[2], d[3], d[4], d[5])
    await message.answer('Так выглядит твоя анкета: ')
    await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["1", "2", "3"]
    keyboard.add(*buttons)

    await message.answer(main_text, reply_markup= keyboard)
    await Wait.menu_answer.set()

@dp.message_handler(state=Wait.menu_answer)
async def menu_answer(message: types.Message, state: FSMContext):
    if message.text == '1':
        anketa = BotDB.get_anketa(message.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])

        list_of_anketi = BotDB.find_anketi(message.from_user.id, a[7], a[4], a[3])

        try:
            get_random_anketa(list_of_anketi)
        except ValueError:
            await message.answer('Никого не могу найти. Возможно, твой город некорректный / не популярный.')
            await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            buttons = ["1", "2", "3", "4"]
            keyboard.add(*buttons)
        
            await message.answer(profile_text, reply_markup = keyboard)
            await Wait.my_anketa_answer.set()
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['❤', '⏩', '❌']
        keyboard.add(*buttons)
        anketa = get_random_anketa(list_of_anketi)
        caption = anketa[0]
        photo_id = anketa[1]
    elif message.text == '2':
        anketa = BotDB.get_anketa(message.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])
        await bot.send_photo(photo = open(f'photos/{message.from_user.id}.jpg', caption=caption, chat_id = message.from_user.id))
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3", "4"]
        keyboard.add(*buttons)
        await message.answer(profile_text, reply_markup=keyboard)
        await Wait.my_anketa_answer.set()
    elif message.text == '3':
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['Да', 'Нет']
        keyboard.add(*buttons)
        await message.answer('Вы точно хотите удалить свою анкету?', reply_markup=keyboard)
        await Wait.delete_confirm.set()
    else:
        await message.answer('Выберите вариант из кнопки')
        return

@dp.message_handler(state= Wait.anketa_reaction)
async def anketa_reaction(message: types.Message, state = FSMContext):
    if message.text == '❤':
        data = await state.get_data()
        d = list(data.values())

        anketa = BotDB.get_anketa(message.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])
        list_of_anketi = BotDB.find_anketi(message.from_user.id, data['interest'], data['city'], data['age'])
        like_id = data['like_id']

        await bot.send_message(text = "Вы понравились этому человеку: ", chat_id = liked_id)
        await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), chat_id = liked_id, caption = caption)
        await bot.send_message(text = f"Начинай общатся, если понравлися(лась) - @{message.from_user.username}", chat_id = liked_id)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['❤', '⏩', '❌']
        keyboard.add(*buttons)
        anketa = get_random_anketa(list_of_anketi)
        caption = anketa[0]
        photo_id = anketa[1]
        await bot.send_photo(photo = open(f"photos/{photo_id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)
        await Wait.anketa_reaction.set()
    elif message.text == "⏩":

        data = await state.get_data()
        list_of_anketi = BotDB.find_anketi(message.from_user.id, data["interest"], data["city"], data["age"])

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ['❤', '⏩', '❌']
        keyboard.add(*buttons)

        caption = get_random_anketa(list_of_anketi)[0]
        photo_id = get_random_anketa(list_of_anketi)[1]
        await bot.send_photo(photo = open(f"photos/{photo_id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)

        await Wait.anketa_reaction.set()

    elif message.text == "❌":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3"]
        keyboard.add(*buttons)

        await message.answer(main_text, reply_markup = keyboard)
        await Wait.menu_answer.set()
    else:
        await message.answer("Выберите вариант из кнопок")
        return
@dp.callback_query_handler(lambda c: c.data == 'delete',state=Wait.delete_confirm)
async def delete(message:types.Message, state: FSMContext):
    if message.text == 'Да':
        BotDB.delete_anketa(message.from_user.id)
        BotDB.delete_user(message.from_user.id)
        await message.answer("Ваша анкета удалена!\nВы можете вернутся сюда в любое время по команде /start", reply_markup = types.ReplyKeyboardRemove())
    elif message.text == 'Нет':
        anketa = BotDB.get_anketa(message.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])
        await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["1", "2", "3", "4"]
        keyboard.add(*buttons)

        await message.answer(profile_text, reply_markup = keyboard)
        await Wait.my_anketa_answer.set()
    else:
        await message.answer("Выберите вариант из кнопок ниже")
        return        
@dp.callback_query_handler(lambda c: c.data == 'Anketa', state = Wait.my_anketa_answer )
async def Anketa(message: types.Message, state:FSMContext):
    if message.text == '1':
        BotDB.delete_anketa(messga.from_user.id)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True) 
        buttons = ["Парень", "Девушка"]
        buttons.add(*buttons)

        await message.answer('Для начала выберите свой пол', reply_markup=keyboard)
        await Wait.choosing_gender.set()
    elif message.text == "2":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add('Оставь пустым')
        await message.answer('Введите новый текст анкеты', reply_markup=keyboard)
        await Wait.change_text.set()
    elif message.photo == '3':
        await message.answer('Загрузить новое фото', reply_markup=types.ReplyKeyboardMarkup())
        await Wait.change_photo.set()
    elif message.text == '4':
        anketa = BotDB.get_anketa(message.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])

        await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=keyboard)
        buttons = ["1", "2", "3", "4"]
        buttons.add(*buttons)

        await message.answer(profile_text, reply_markup=keyboard)
        await Wait.my_anketa_answer.set()
    else:
        if len(message) > 100:
            await message.answer('Описание должно быть длинной до 100 символов')
            return
        BotDB.update_data(message.from_user.id, message.text)
        anketa = BotDB.get_anketa(message.from_user.id)
        a = anketa[0]
        caption = show_profile(a[2], a[3], a[4], a[5])

        await bot.send_photo(photo=open(f'photos/{message.from_user.id}.jpg', 'rb'), caption=caption, chat_id=message.from_user.id)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=keyboard)
        buttons = ['1', '2', '3', '4']
        buttons.add(*buttons)

        await message.answer(main_text, reply_markup=keyboard)
        await Wait.menu_answer.set()
@dp.message_handler(state = Wait.change_photo, content_types = ["photo"])
async def change_photo(message: types.Message, state: FSMContext):
    await message.photo[-1].download(destination_file=f"photos/{message.from_user.id}.jpg")

    anketa = BotDB.get_anketa(message.from_user.id)
    a = anketa[0]
    caption = show_profile(a[2], a[3], a[4], a[5])   

    await message.answer("Вот ваша анкета: ")
    await bot.send_photo(photo = open(f"photos/{message.from_user.id}.jpg", "rb"), caption = caption, chat_id = message.from_user.id)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["1", "2", "3"]
    keyboard.add(*buttons)

    await message.answer(main_text, reply_markup = keyboard)
    await Wait.menu_answer.set()





if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)