import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from pymongo import MongoClient
import urllib.parse

password = urllib.parse.quote_plus('7ZfrNV3ifnWf2oor')
client = MongoClient('mongodb+srv://coolpoint:%s@coolpoint-cluster.5g2rs.mongodb.net/?retryWrites=true&w=majority' % (password))

base = client['base_of_peoples']
base_teachers = base['teachers']
base_students = base['students']

samples = {
    'for_students' : '<Контактный номер, указанный в CRM (+79999999999)>\n<ФИО через пробел>\n<Username ученика в телеграм>\n<Username родителя (если надо)\n<Часовой пояс ученика по Москве, просто +чч (например, +2)>',
    'for_teachers' : '<ФИО через пробел>\n<Токен доступа к Google API>\n<Часовой пояс (+чч)>\n<Любой контактный номер или ссылка на Telegram>'
}

access = ['VuplesOwl', 'A3artt']


class States(StatesGroup):

    STUDENT = State()
    TEACHER = State()
    CONFIRM_TEACHER = State()
    CONFIRM_STUDENT = State()
    SET_CHOICE_PUT_OR_GET = State()
    GET_DATA = State()
    CHANGE_DATA = State()
    
    
    
API_TOKEN = '5505602681:AAG4wWLE4GCTYxmSmoF3LHHC43fe41Leiak'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands='start')
async def start_cmd_handler(msg: types.Message):
    
    if msg.from_user.username not in ['VuplesOwl', 'A3artt'] : return 

    state = dp.current_state(user=msg.from_user.id)

    await state.reset_state()
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Student", "Teacher"]
    keyboard.add(*buttons)

    await msg.reply("Привет\nТебе нужно выбрать, чьи данные собираешься ввести или посмотреть, используй кнопки.\nЧтобы сбросить ввод напиши /cancel", reply_markup=keyboard)



@dp.message_handler()
async def handler(msg: types.Message):
    
    if msg.from_user.username not in ['VuplesOwl', 'A3artt'] : return 

    
    state = dp.current_state(user=msg.from_user.id)
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Put new data","Get data","/cancel"]
    keyboard.add(*buttons)
    
    if msg.text.lower() != 'student' and msg.text.lower() != 'teacher':
        await bot.send_message(msg.from_user.id, 'Не понимаю, используй кнопки')
        
    elif msg.text.lower() == 'student':
        await bot.send_message(msg.from_user.id, 'Выбери, что хочешь сделать:', reply_markup=keyboard)
        # await bot.send_message(msg.from_user.id, 'Введи данные ученика по шаблону через перенос строки:\n'+samples['for_students'], reply_markup=keyboard)
        await States.SET_CHOICE_PUT_OR_GET.set()
        await state.update_data(choised_obj='student')
        
    elif msg.text.lower() == 'teacher': 
        await bot.send_message(msg.from_user.id, 'Выбери, что хочешь сделать:', reply_markup=keyboard)
        # await bot.send_message(msg.from_user.id, 'Введи данные учителя по шаблону через перенос строки:\n'+samples['for_teachers'], reply_markup=keyboard)
        await States.SET_CHOICE_PUT_OR_GET.set()
        await state.update_data(choised_obj='teacher')
        

@dp.message_handler(state=States.SET_CHOICE_PUT_OR_GET)
async def get_info_student(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    if msg.text=='/cancel': 
        await state.finish()
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Student", "Teacher"]
        keyboard.add(*buttons)
        
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести или посмотреть", reply_markup=keyboard)
        return
    
    data = await state.get_data()
    choise = data['choised_obj']
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["/cancel"]
    keyboard.add(*buttons)
    
    if msg.text.lower() != 'put new data' and msg.text.lower() != 'get data':
        await bot.send_message(msg.from_user.id, 'Не понимаю, используй кнопки')
        
    elif msg.text.lower() == 'put new data':
        if choise == 'teacher':
            await States.TEACHER.set()
            await bot.send_message(msg.from_user.id, 'Введи данные учителя по шаблону через перенос строки:\n'+samples['for_teachers'], reply_markup=keyboard)
        elif choise == 'student':
            await States.STUDENT.set()
            await bot.send_message(msg.from_user.id, 'Введи данные ученика по шаблону через перенос строки:\n'+samples['for_students'], reply_markup=keyboard)
            
    elif msg.text.lower() == 'get data':
        await States.GET_DATA.set()
        if choise == 'teacher':
            await States.GET_DATA.set()
            await bot.send_message(msg.from_user.id, 'Введи ФИО учителя', reply_markup=keyboard)
        elif choise == 'student':
            await States.GET_DATA.set()
            await bot.send_message(msg.from_user.id, 'Введи номер ученика из CRM (+79999999999)', reply_markup=keyboard)
            
@dp.message_handler(state=States.GET_DATA)
async def get_info_student(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    if msg.text=='/cancel': 
        await state.finish()
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Student", "Teacher"]
        keyboard.add(*buttons)
        
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести", reply_markup=keyboard)
        return
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["/cancel"]
    keyboard.add(*buttons)

    data = await state.get_data()
    choise = data['choised_obj']
    
    _id = msg.text
    
    if choise == 'teacher':
        # States.GET_DATA.set()
        # await bot.send_message(msg.from_user.id, 'Введи ФИО учителя', reply_markup=keyboard)
        base = base_teachers.find({'_id':_id})
        is_id = False
        for item in base:
            is_id = True
            await bot.send_message(msg.from_user.id, str(item)+'\n ---------- \n Если нужно что-то изменить, то введи название парfметра и через ":" его значение (number:+799999999), если нужно ввести новые значения, то просто сделай то же самое, если их несколько, то через enter', reply_markup=keyboard)
            await States.CHANGE_DATA.set()
            await state.update_data(item=item)
            
        if is_id == False:
            await bot.send_message(msg.from_user.id, 'Кажется ты ввел неверные данные или такого человека еще нет в базе данных, нажми /cancel или попробуй еще раз', reply_markup=keyboard)
            await States.GET_DATA.set()
                
    elif choise == 'student':
        base = base_students.find({'_id':_id})
        is_id = False
        for item in base:
            is_id = True
            await bot.send_message(msg.from_user.id, str(item)+'\n ---------- \n Если нужно что-то изменить, то введи название парfметра и через ":"" его значение (number:+799999999), если нужно ввести новые значения, то просто сделай то же самое, если их несколько, то через enter', reply_markup=keyboard)
            await States.CHANGE_DATA.set()
            await state.update_data(item=item)
            
        if is_id == False:
            await bot.send_message(msg.from_user.id, 'Кажется ты ввел неверные данные или такого человека еще нет в базе данных, нажми /cancel или попробуй еще раз', reply_markup=keyboard)
            await States.GET_DATA.set()
            

@dp.message_handler(state=States.CHANGE_DATA)
async def get_info_student(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    if msg.text=='/cancel': 
        await state.finish()
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Student", "Teacher"]
        keyboard.add(*buttons)
        
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести или показать", reply_markup=keyboard)
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Student", "Teacher"]
    keyboard.add(*buttons)
    
    changed_items = msg.text
    
    data = await state.get_data()
    choise = data['choised_obj']
    item = data['item']

    if choise == 'teacher':
        for key_item in changed_items.split('\n'):
            key = key_item.split(':')[0]
            if key=='token':
                value = key_item[6:]
            else: value = key_item.split(':')[1]

            base_teachers.update_one({"_id": item['_id']}, 
                                             {"$set": {key: value}})
            
            
        
        
    elif choise == 'student':
        for key_item in changed_items.split('\n'):
            key = key_item.split(':')[0]
            value = key_item.split(':')[1]

            base_students.update_one({"_id": item['_id']}, 
                                             {"$set": {key: value}})
            
    await bot.send_message(msg.from_user.id, 'Данные обновлены, можешь снова выбрать, чьи данные нужно ввести или показать', reply_markup=keyboard)

    await state.finish()

    

@dp.message_handler(state=States.STUDENT)
async def get_info_student(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    if msg.text=='/cancel': 
        await state.finish()
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Student", "Teacher"]
        keyboard.add(*buttons)
        
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести или показатm", reply_markup=keyboard)
        return

    number = msg.text.split('\n')[0]
    full_name = msg.text.split('\n')[1]
    username = msg.text.split('\n')[2]
    parents_username = msg.text.split('\n')[3]
    time_zone = msg.text.split('\n')[4]
    
    await state.update_data(number=number,full_name=full_name,username=username,parents_username=parents_username,time_zone=time_zone)
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Да","/cancel"]
    keyboard.add(*buttons)

    await bot.send_message(msg.from_user.id, 'Все верно?\n{}\n{}\n{}\n{}\n{}'.format(number,full_name,username,parents_username,time_zone), reply_markup=keyboard)
    
    await States.CONFIRM_STUDENT.set()
    
    
    
    
    
    
    
@dp.message_handler(state=States.TEACHER)
async def get_info_teacher(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    if msg.text=='/cancel': 
        await state.finish()
        
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Student", "Teacher"]
        keyboard.add(*buttons)
        
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести или показатm", reply_markup=keyboard)
        return

    full_name = msg.text.split('\n')[0]
    token = msg.text.split('\n')[1]
    time_zone = msg.text.split('\n')[2]
    number = msg.text.split('\n')[3]
    
    await state.update_data(full_name=full_name,token=token,time_zone=time_zone,number=number)
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Да","/cancel"]
    keyboard.add(*buttons)
    
    await bot.send_message(msg.from_user.id, 'Все верно?\n{}\n{}\n{}\n{}'.format(full_name,token,time_zone,number), reply_markup=keyboard)
    
    await States.CONFIRM_TEACHER.set()
        

@dp.message_handler(state=States.CONFIRM_STUDENT)
async def get_info_teacher(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Student", "Teacher"]
    keyboard.add(*buttons)
    if msg.text=='/cancel': 
        await state.finish()
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести или показатm", reply_markup=keyboard)
        return
    
    if msg.text.lower()=='да':
        data = await state.get_data()
        
        mydict = {
        "_id" : data['number'],
        "full_name" : data['full_name'],
        "username" : data['username'],
        "parents_username" : data['parents_username'],
        "time_zone" : data['time_zone']
        }

        base_students.insert_one(mydict)
        
        await bot.send_message(msg.from_user.id, 'Данные ученика занесены в систему\nЕсли они окажутся неверными и система сломается, я вас найду и разберусь лично', reply_markup=keyboard)
        await state.finish()
    else:
        await bot.send_message(msg.from_user.id, 'Напиши Да или нажми команду /cancel')
        
@dp.message_handler(state=States.CONFIRM_TEACHER)
async def get_info_teacher(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Student", "Teacher"]
    keyboard.add(*buttons)
    if msg.text=='/cancel': 
        await state.finish()
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести или показатm", reply_markup=keyboard)
        return
    
    if msg.text.lower()=='да':
        data = await state.get_data()
        
        mydict = {
        "_id" : data['full_name'],
        "token" : data['token'],
        "time_zone" : data['time_zone'],
        "number" : data['number']
        }

        base_teachers.insert_one(mydict)
        
        await bot.send_message(msg.from_user.id, 'Данные преподавателя занесены в систему\nЕсли они окажутся неверными и система сломается, я вас найду и разберусь лично', reply_markup=keyboard)
        await state.finish()
    else:
        await bot.send_message(msg.from_user.id, 'Напиши Да или нажми команду /cancel')
        

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
