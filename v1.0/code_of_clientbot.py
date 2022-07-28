import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from pymongo import MongoClient
import urllib.parsea
import json

password = urllib.parse.quote_plus('7ZfrNV3ifnWf2oor')
client = MongoClient('mongodb+srv://coolpoint:%s@coolpoint-cluster.5g2rs.mongodb.net/?retryWrites=true&w=majority' % (password))

base = client['base_of_peoples']
base_teachers = base['teachers']
base_students = base['students']

blanks = {
    'welcome' : 'Кратко обо мне.\nЗдравствуйте! 😊\nЯ бот-помощник школы CoolPoint.\nЗачем я Вам нужен? 🤔\nКонцепция школы CoolPoint - "Учиться легко!".\nСоответственно, я вношу небольшой, но очень важный вклад в удобства уроков. Коротко говоря, я помощник, который связывает преподавателя с его учениками!)\nЧто я умею? ☝️\nНапоминаю о предстоящих уроках;\nПрисылаю все необходимые ссылки для начала занятия;\nСлежу за остатком уроков на балансе абонемента;\nРассказываю о новостях школы и не только;\nЯ тоже постоянно учусь, а значит список моих функций будет постоянно пополняться. Следите за новостями! 😌',
    'plug' : 'Добрый день!☺️\n\nВы попали на бота-помощника школы A3artSchool. \nЕсли вы читаете это сообщение, значит Вы одни из первых, кто был приглашен в эту систему. \nСейчас идёт этап тестирования, если Вы сталкнетесь с любыми неисправностями или неточностями, обязательно пишите Владиславу (@A3artt). \nСпасибо Вам за участие в тестовом периоде! \n\nЧто я умею? ☝️\n📌Напоминаю о предстоящих уроках;\n📌Присылаю все необходимые ссылки для начала занятия;\n📌Слежу за остатком уроков на балансе абонемента;\n📌Рассказываю о новостях школы и не только;\n\nДо встречи! 😉'
}



    
API_TOKEN = '5473320366:AAEwnENs-cyjGA5pBJFA-qpeHiU-v4B2_5A'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands='start')
async def start_handler(msg: types.Message):

    user_id = msg.from_user.id
    username = '@'+msg.from_user.username
    
    print(user_id)
    print(username)
    
    item_student = base_students.find({'username':username})
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)
        
    if is_in_file.get(user_id) == None:
        for item in item_student:
            number = item['_id']
            id_number = {user_id: number}
            is_in_file.update(id_number)
            with open('is_in_file.txt','w') as data: 
                data.write(json.dumps(is_in_file))
    else:
        number = is_in_file[user_id]
        
    print(number)    
    
#     keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     buttons = ["Контакты", "Следующий урок", "Баланс"]
#     keyboard.add(*buttons)

    # await msg.reply(blanks['plug'], reply_markup=keyboard)
    await msg.reply(blanks['plug'])


    
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
