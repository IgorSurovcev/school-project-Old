import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from pymongo import MongoClient
import urllib.parse
import json
import phonenumbers
from phonenumbers import carrier, timezone, geocoder

password = urllib.parse.quote_plus('7ZfrNV3ifnWf2oor')
client = MongoClient('mongodb+srv://coolpoint:%s@coolpoint-cluster.5g2rs.mongodb.net/?retryWrites=true&w=majority' % (password))

base = client['base_of_peoples']
base_teachers = base['teachers']
base_students = base['students']

base_of_events = client['base_of_events']
promo_codes = base_of_events['promo_codes']


samples = {
    'for_students' : '<Контактный номер, указанный в CRM (+7**********)>\n<ФИО через пробел>\n<Часовой пояс ученика по Москве, просто +чч (например, +2)><Повседневная скидка>\n<Одноразовая скидка>',
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
    
    REPLY_CHOISE = State()
    REPLY_NEW_USER = State()
    REPLY_ADD_USER_ID = State()
    
    GET_PROMO_CODE = State()
    # GET_USER_ID = State()
    
# from logdna import LogDNAHandler
# key='d7903ac4bec957d8e8d0ab45479fdd45'
# log = logging.getLogger('logdna')
# log.setLevel(logging.DEBUG)
# options = {  'hostname': 'hostkey17726',  'ip': '46.17.100.162',  'mac': '56:6f:ff:5b:01:24'}
# options['index_meta'] = True
# mezmo = LogDNAHandler(key, options)
# logging.basicConfig(handlers=[mezmo])

import datadog
from datadog_logger import DatadogLogHandler
import logging

datadog.initialize(api_key="c860bcea1999acd4362c5f8a846783c6", app_key="ba7066ae6eb26669d762d0a2108b25e825f9ba15")
datadog_handler = DatadogLogHandler(tags=["some:tag"], mentions=["@some-mention"], level=logging.ERROR)
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger()
logger.addHandler(datadog_handler)


API_TOKEN = '5505602681:AAG4wWLE4GCTYxmSmoF3LHHC43fe41Leiak'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands='start')
async def start_cmd_handler(msg: types.Message):
    
    if msg.from_user.username not in ['VuplesOwl', 'A3artt'] : return 

    state = dp.current_state(user=msg.from_user.id)

    await state.reset_state()
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Student", "Teacher", "Add_promo_code"]
    keyboard.add(*buttons)
    
    
    await msg.reply("Привет\nТебе нужно выбрать, чьи данные собираешься ввести или посмотреть, используй кнопки.\nЧтобы сбросить ввод напиши /cancel", reply_markup=keyboard)



@dp.message_handler()
async def handler(msg: types.Message):
    if msg.from_user.username not in ['VuplesOwl', 'A3artt'] : return 
    state = dp.current_state(user=msg.from_user.id)
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Put new data","Get data","/cancel"]
    keyboard.add(*buttons)
        
    if msg.text.lower() == 'student':
        await bot.send_message(msg.from_user.id, 'Выбери, что хочешь сделать:', reply_markup=keyboard)
        await States.SET_CHOICE_PUT_OR_GET.set()
        await state.update_data(choised_obj='student')
        
    elif msg.text.lower() == 'teacher': 
        await bot.send_message(msg.from_user.id, 'Выбери, что хочешь сделать:', reply_markup=keyboard)
        await States.SET_CHOICE_PUT_OR_GET.set()
        await state.update_data(choised_obj='teacher')
        
    elif msg.text.lower() == 'add_promo_code': 
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["/cancel"]
        keyboard.add(*buttons)
        await bot.send_message(msg.from_user.id, 'Введи через пробел <Промокод><Скидка (как и обычная скидка. Если указывается бесплатное занятие, то значение скидки на абонемент должно быть стандартным)><Количество использований промокда>:', reply_markup=keyboard)
        await States.GET_PROMO_CODE.set()
        
    elif dict(msg).get('forward_from') != None:
        await state.update_data(students_id=str(msg.forward_from.id))
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons_0 = ["Новый","Старый"]
        buttons = ["/cancel"]
        keyboard.row(*buttons_0)
        keyboard.add(*buttons)
        await bot.send_message(msg.from_user.id, str(msg.forward_from.id)+'\nКто это?', reply_markup=keyboard)
        await States.REPLY_CHOISE.set()
           
            
            
@dp.message_handler(state=States.GET_PROMO_CODE)
async def put_students_id(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)    
    if msg.text=='/cancel': 
        await state.finish()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Student", "Teacher", "Add_promo_code"]
        keyboard.add(*buttons)
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести или посмотреть", reply_markup=keyboard)
        return
    
    promo_code = msg.text.split(' ')[0]
    discounts = msg.text.split(' ')[1] + ' ' + msg.text.split(' ')[2]
    value = msg.text.split(' ')[3]
    
    mydict = {
    "_id" : promo_code,
    "discounts" : discounts,
    "value": value
    }
    promo_codes.insert_one(mydict)
    
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Student", "Teacher", "Add_promo_code"]
    keyboard.add(*buttons)
    await msg.reply("Промокод добавлен", reply_markup=keyboard)
    
    
    
        
@dp.message_handler(state=States.REPLY_CHOISE)
async def put_students_id(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)    
    if msg.text=='/cancel': 
        await state.finish()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Student", "Teacher", "Add_promo_code"]
        keyboard.add(*buttons)
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести или посмотреть", reply_markup=keyboard)
        return
    
    if msg.text == "Новый":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["/cancel"]
        keyboard.add(*buttons)
        await bot.send_message(msg.from_user.id, '<Номер телефона этого ученика ("+" в начале обазателен)>\n<ФИО>\n<Часовой пояс по Москве (+int)\n<Скидка. <скидка на абонемент> для каждого предмета (Математика, Русский язык) через пробел("10 10"), если для всех уроков стандартные, то enter>\n <Одноразовая скидка, то же самое, что в прошлом, но после первой покупки исчезнет>', reply_markup=keyboard)
        await States.REPLY_NEW_USER.set()
        
    elif msg.text == "Старый":
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["/cancel"]
        keyboard.add(*buttons)
        await bot.send_message(msg.from_user.id, '<Номер ученика, к которому нужно подключить еще один id ("+" в начале обазателен)>', reply_markup=keyboard)
        await States.REPLY_ADD_USER_ID.set()
        
        
@dp.message_handler(state=States.REPLY_NEW_USER)
async def put_students_id(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)    
    if msg.text=='/cancel': 
        await state.finish()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Student", "Teacher", "Add_promo_code"]
        keyboard.add(*buttons)
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести или посмотреть", reply_markup=keyboard)
        return
    
    number = msg.text.split('\n')[0]
    
    data = await state.get_data()
    students_id = data['students_id']
    
    try:
        number_parse = phonenumbers.parse(number)
    except:
        await bot.send_message(msg.from_user.id, 'Неправильно')
        return
    if not phonenumbers.is_valid_number(number_parse):
        await bot.send_message(msg.from_user.id, 'Неправильно')
        return
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Student", "Teacher", "Add_promo_code"]
    keyboard.add(*buttons)

    number = '+'+str(number_parse.country_code) + str(number_parse.national_number)
    
    full_name = msg.text.split('\n')[1]
    timezone = msg.text.split('\n')[2]
    discounts =  msg.text.split('\n')[3]
    try: 
        coupon_dicounts = msg.text.split('\n')[4]
    except: one_time_dicounts=''
        
    
    
    if discounts == '': discounts = '10 10'

    
    print(discounts)
    return
    
    mydict = {
    "_id" : number,
    "full_name" : full_name,
    "time_zone" : timezone,
    "discounts" : discounts,
    "one_time_dicounts" : one_time_dicounts
    }
    try:
        base_students.insert_one(mydict)
        await bot.send_message(msg.from_user.id,'Данные занесены в базу')
    except: 
        await bot.send_message(msg.from_user.id,'Такой номер уже есть в базе, перепроверьте данные и найдите ошибку', reply_markup=keyboard)
        await state.finish()

    
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)
               
    if is_in_file.get(number) == None:
        is_in_file.update({number:[]})
        user_ids = []
    else:
        # user_ids = is_in_file[number]
        await bot.send_message(msg.from_user.id,'В файле уже есть такой номер, кажется, где-то ошибка', reply_markup=keyboard)
        await state.finish()
        return

    user_ids = set(user_ids)
    user_ids.add(students_id)
    user_ids = list(user_ids)
    number_ids = {number: user_ids}
    is_in_file.update(number_ids)
    with open('is_in_file.txt','w') as data: 
        data.write(json.dumps(is_in_file))
    
    await bot.send_message(msg.from_user.id,'id ученика сохранен в файл', reply_markup=keyboard)  
    await state.finish()
    
    
@dp.message_handler(state=States.REPLY_ADD_USER_ID)
async def put_students_id(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)    
    if msg.text=='/cancel': 
        await state.finish()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Student", "Teacher", "Add_promo_code"]
        keyboard.add(*buttons)
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести или посмотреть", reply_markup=keyboard)
        return
    
    number = msg.text.split('\n')[0]
    try:
        number_parse = phonenumbers.parse(number)
    except:
        await bot.send_message(msg.from_user.id, 'Неправильно')
        return
    if not phonenumbers.is_valid_number(number_parse):
        await bot.send_message(msg.from_user.id, 'Неправильно')
        return
    number = '+'+str(number_parse.country_code) + str(number_parse.national_number)
    
    data = await state.get_data()
    students_id = data['students_id']
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Student", "Teacher", "Add_promo_code"]
    keyboard.add(*buttons)
    
    
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)
               
    if is_in_file.get(number) == None:
        # is_in_file.update({number:[]})
        # user_ids = []
        await bot.send_message(msg.from_user.id,'Такого ученика еще нет в файле, видимо где-то ошибка, проверь все данные', reply_markup=keyboard) 
        await state.finish()
        return
    else:
        user_ids = is_in_file[number]

    user_ids = set(user_ids)
    user_ids.add(students_id)
    user_ids = list(user_ids)
    number_ids = {number: user_ids}
    is_in_file.update(number_ids)
    with open('is_in_file.txt','w') as data: 
        data.write(json.dumps(is_in_file))
    
    await bot.send_message(msg.from_user.id,'id ученика сохранен в файл', reply_markup=keyboard)  
    await state.finish()
    

        

@dp.message_handler(state=States.SET_CHOICE_PUT_OR_GET)
async def get_info_student(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    if msg.text=='/cancel': 
        await state.finish()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Student", "Teacher", "Add_promo_code"]
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
        buttons = ["Student", "Teacher", "Add_promo_code"]
        keyboard.add(*buttons)
        
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести", reply_markup=keyboard)
        return
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["/cancel"]
    keyboard.add(*buttons)

    data = await state.get_data()
    choise = data['choised_obj']

    # try:
    #     _id = '+'+str(phonenumbers.parse(msg.text.split('\n')[0]).country_code) + str(phonenumbers.parse(msg.text.split('\n')[0]).national_number)
    # except:  _id = msg.text
    
    if choise == 'teacher':
        _id = msg.text.split('\n')[0]
        # States.GET_DATA.set()
        # await bot.send_message(msg.from_user.id, 'Введи ФИО учителя', reply_markup=keyboard)
        base = base_teachers.find({'_id':_id})
        is_id = False
        for item in base:
            is_id = True
            await bot.send_message(msg.from_user.id, str(item)+'\n ---------- \n Если нужно что-то изменить, то введи название парfметра и через ": " его значение (_id: +799999999), если нужно ввести новые значения, то просто сделай то же самое, если их несколько, то через enter (НИКАКИХ ЛИШНИХ СИМВОЛОВ, ИСКЛЮЧИТЕЛЬНО ПО ИНСТРУКЦИИ И ПО ПРИМЕРУ, а то костей не соберете)', reply_markup=keyboard)
            await States.CHANGE_DATA.set()
            await state.update_data(item=item)
            
        if is_id == False:
            await bot.send_message(msg.from_user.id, 'Кажется ты ввел неверные данные или такого человека еще нет в базе данных, нажми /cancel или попробуй еще раз', reply_markup=keyboard)
            await States.GET_DATA.set()
                
    elif choise == 'student':
        number_parse = phonenumbers.parse(msg.text.split('\n')[0])
        _id = '+'+str(number_parse.country_code) + str(number_parse.national_number)
        base = base_students.find({'_id':_id})
        is_id = False
        for item in base:
            is_id = True
            await bot.send_message(msg.from_user.id, str(item)+'\n ---------- \n Если нужно что-то изменить, то введи название парfметра и через ": "" его значение (timezone: +2), если нужно ввести новые значения, то просто сделай то же самое, если их несколько, то через enter', reply_markup=keyboard)
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
        buttons = ["Student", "Teacher", "Add_promo_code"]
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
                value = key_item[7:]
            else: value = key_item.split(':')[1][1:]

            base_teachers.update_one({"_id": item['_id']}, 
                                             {"$set": {key: value}})
        
    elif choise == 'student':
        for key_item in changed_items.split('\n'):
            key = key_item.split(':')[0]
            if key == 'number':
                number_parse = phonenumbers.parse(key_item.split(':')[1][1:].split('\n')[0])
                value = '+'+str(number_parse.country_code) + str(number_parse.national_number)
                # value = '+'+str(phonenumbers.parse(key_item.split(':')[1][1:]).country_code) + str(phonenumbers.parse(key_item.split(':')[1][1:]).national_number)
            value = key_item.split(':')[1][1:]
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
        buttons = ["Student", "Teacher", "Add_promo_code"]
        keyboard.add(*buttons)
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести или показатm", reply_markup=keyboard)
        return
    
    # number = '+'+str(phonenumbers.parse(msg.text.split('\n')[0]).country_code) + str(phonenumbers.parse(msg.text.split('\n')[0]).national_number)
    number_parse = phonenumbers.parse(msg.text.split('\n')[0])
    number = '+'+str(number_parse.country_code) + str(number_parse.national_number)
    
    full_name = msg.text.split('\n')[1]
    time_zone = msg.text.split('\n')[2]
    discounts = msg.text.split('\n')[3]
    try: 
        coupon_dicounts = msg.text.split('\n')[4]
    except: one_time_dicounts=''
    
    await state.update_data(number=number,full_name=full_name,time_zone=time_zone,discounts=discounts,one_time_dicounts=one_time_dicounts)
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Да","/cancel"]
    keyboard.add(*buttons)

    await bot.send_message(msg.from_user.id, 'Все верно?\n{}\n{}\n{}'.format(number,full_name,time_zone), reply_markup=keyboard)
    await States.CONFIRM_STUDENT.set()
    
    
@dp.message_handler(state=States.TEACHER)
async def get_info_teacher(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    if msg.text=='/cancel': 
        await state.finish()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Student", "Teacher", "Add_promo_code"]
        keyboard.add(*buttons)
        await msg.reply("Ввод сброшен, можешь снова выбрать, чьи данные нужно ввести или показатm", reply_markup=keyboard)
        return

    full_name = msg.text.split('\n')[0]
    token = msg.text.split('\n')[1]
    time_zone = msg.text.split('\n')[2]
    staff_id = msg.text.split('\n')[3]
    user_id = msg.text.split('\n')[4]
    
    await state.update_data(full_name=full_name,token=token,time_zone=time_zone,staff_id=staff_id,user_id=user_id)
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Да","/cancel"]
    keyboard.add(*buttons)
    
    await bot.send_message(msg.from_user.id, 'Все верно?\n{}\n{}\n{}\n{}\n{}'.format(full_name,token,time_zone,staff_id,user_id), reply_markup=keyboard)
    await States.CONFIRM_TEACHER.set()
        

@dp.message_handler(state=States.CONFIRM_STUDENT)
async def get_info_teacher(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Student", "Teacher", "Add_promo_code"]
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
        "time_zone" : data['time_zone'],
        "discounts" : data['discounts'],
        "one_time_dicounts" : data['one_time_dicounts']
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
    buttons = ["Student", "Teacher", "Add_promo_code"]
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
        "staff_id" : data['staff_id'],
        "user_id" : data['user_id']
        }
        base_teachers.insert_one(mydict)
        await bot.send_message(msg.from_user.id, 'Данные преподавателя занесены в систему\nЕсли они окажутся неверными и система сломается, я вас найду и разберусь лично', reply_markup=keyboard)
        await state.finish()
    else:
        await bot.send_message(msg.from_user.id, 'Напиши Да или нажми команду /cancel')
        
        
        
        
# @dp.message_handler()
# async def get_info_teacher(msg: types.Message):
    
#     # message.reply_to_message is a types.Message object too
#         # msg = message.reply_to_message.text # if replied
#     print(msg)
    
    
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
