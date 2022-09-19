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
import requests
import time
from aiogram.utils.callback_data import CallbackData
import phonenumbers
from phonenumbers import carrier, timezone, geocoder
from datetime import datetime, timedelta, timezone


password = urllib.parse.quote_plus('7ZfrNV3ifnWf2oor')
client = MongoClient('mongodb+srv://coolpoint:%s@coolpoint-cluster.5g2rs.mongodb.net/?retryWrites=true&w=majority' % (password))

base = client['base_of_peoples']
base_teachers = base['teachers']
base_students = base['students']

blanks = {'start' : 'Привет. Здесь можно записаться на бесплатный пробный урок в A3artSchool.\nПробный урок длится 30 минут.\nВ результате, мы определим уровень текущей подготовки и составим индивидуальный план для достижения целей.',
    'start_reg' : 'Для создания записи на урок мне нужно собрать некоторые данные о вас.\nДля начала, для кого хотите организовать пробный урок?\n(если не отчества, можно не указывать)'}

tz_1 = [['МСК-1','МСК+0','МСК+1'],['МСК+2','МСК+3','МСК+4'],['МСК+5','МСК+6','МСК+7'],['МСК+8','МСК+9','Другое']]
tz_2 = [['GMT+0', 'GMT+1','GMT+2'], ['GMT-1', 'GMT-2', 'GMT-3'], ['GMT-4', 'GMT-5', 'GMT-6'], ['GMT-7', 'GMT-8', 'GMT-9'], ['GMT-10','GMT-11','Назад']]
administators_ids = [676352317, 1226474188] #1226474188
subject_id = {"Русский язык":{"id_subject":"10610342","id_main_teacher":"2216972"},"Математика":{"id_subject":"10610339","id_main_teacher":"1858699"}}    
# teachers_timezone = +2 
# 'Наумова Виктория Валерьевна': 5302495
categories = {
    'Онлайн': 4714371,
    'Очное': 4714372,
    '11 класс': 4632068,
    '10 класс': 4632069,
    '9 класс': 4632070,
    '8 класс': 4714359,
    '7 класс': 4714367,
    '6 класс': 4714368,
    '5 класс': 4714369
}
    
API_TOKEN = '5174653167:AAF8i4izVuCd65VarRjaV7GgZnj6_Ai2LKs'

logging.basicConfig(level=logging.INFO)

class States(StatesGroup):
    CHOISE_FULLNAME = State()
    ONE_FULLNAME = State()
    TWO_FULLNAME = State()
    SECOND_FULLNAME = State()
    TIMEZONE = State()
    CONTACT = State()
    SUBJECT = State()
    GRADE = State()
    DAY = State()
    TIME = State()

callbakes = CallbackData('callback','action','value')
    
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands='start',state='*')
async def start_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    state = dp.current_state(user=msg.from_user.id)

    await state.reset_state()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Записаться на бесплатный урок"]
    keyboard.add(*buttons)
    await bot.send_message(user_id, blanks['start'], reply_markup=keyboard)

@dp.message_handler(text=['Записаться на бесплатный урок','записаться на бесплатный урок'])
async def func(msg: types.Message):
    user_id = str(msg.from_user.id)
    state = dp.current_state(user=msg.from_user.id)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Для себя","Для ребенка"]
    keyboard.add(*buttons)
    
    await bot.send_message(user_id, blanks['start_reg'], reply_markup=keyboard)
    await States.CHOISE_FULLNAME.set()
    
@dp.message_handler(state=States.CHOISE_FULLNAME,text=["Для себя","Для ребенка"])
async def func(msg: types.Message):
    user_id = str(msg.from_user.id)
    state = dp.current_state(user=msg.from_user.id)
    
    keyboard = types.ReplyKeyboardRemove()
    if msg.text == "Для себя":
        await bot.send_message(user_id, 'Введите свое ФИО:', reply_markup=keyboard)
        await States.ONE_FULLNAME.set()
    elif msg.text == "Для ребенка":
        await bot.send_message(user_id, 'Введите ФИО ребенка:', reply_markup=keyboard)
        await States.TWO_FULLNAME.set()
        
@dp.message_handler(state=States.ONE_FULLNAME)
async def func(msg: types.Message):
    user_id = str(msg.from_user.id)
    state = dp.current_state(user=msg.from_user.id)
    
    students_full_name = msg.text
    parents_full_name = None
    if len(students_full_name.split(' ')) != 3 and len(students_full_name.split(' ')) != 2:
        await bot.send_message(user_id, 'Кажется, вы неправильно ввели ФИО, попробуйте еще раз')
        return
    
    await state.update_data(students_full_name=students_full_name,parents_full_name=parents_full_name)
    
    keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    for row in tz_1:
        keyboard.row(types.InlineKeyboardButton(row[0], callback_data=callbakes.new(action='get_timezone', value=row[0])),
                     types.InlineKeyboardButton(row[1], callback_data=callbakes.new(action='get_timezone', value=row[1])),
                     types.InlineKeyboardButton(row[2], callback_data=callbakes.new(action='get_timezone', value=row[2])))
    await bot.send_message(user_id, 'Выберите свой часовой пояс:',reply_markup=keyboard)
    await States.TIMEZONE.set()
    
@dp.message_handler(state=States.TWO_FULLNAME)
async def func(msg: types.Message):
    user_id = str(msg.from_user.id)
    state = dp.current_state(user=msg.from_user.id)
    
    students_full_name = msg.text
    if len(students_full_name.split(' ')) != 3 and len(students_full_name.split(' ')) != 2:
        await bot.send_message(user_id, 'Кажется, вы неправильно ввели ФИО, попробуйте еще раз')
        return
    await state.update_data(students_full_name=students_full_name)
    await bot.send_message(user_id, 'Введите свое ФИО:')
    await States.SECOND_FULLNAME.set()
    
@dp.message_handler(state=States.SECOND_FULLNAME)
async def func(msg: types.Message):
    user_id = str(msg.from_user.id)
    state = dp.current_state(user=msg.from_user.id)
    
    parents_full_name = msg.text
    if len(parents_full_name.split(' ')) != 3 and len(parents_full_name.split(' ')) != 2:
        await bot.send_message(user_id, 'Кажется, вы неправильно ввели ФИО, попробуйте еще раз')
        return
    await state.update_data(parents_full_name=parents_full_name)
    
    keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    for row in tz_1:
        keyboard.row(types.InlineKeyboardButton(row[0], callback_data=callbakes.new(action='get_timezone', value=row[0])),
                     types.InlineKeyboardButton(row[1], callback_data=callbakes.new(action='get_timezone', value=row[1])),
                     types.InlineKeyboardButton(row[2], callback_data=callbakes.new(action='get_timezone', value=row[2])))
    await bot.send_message(user_id, 'Выберите свой часовой пояс:',reply_markup=keyboard)
    await States.TIMEZONE.set()
    
    
@dp.callback_query_handler(callbakes.filter(action='get_timezone'),state=States.TIMEZONE)
async def process_callback(query: types.CallbackQuery, callback_data: dict):                 
    state = dp.current_state(user=query.from_user.id)
       
    value = callback_data['value']                  
    if value=='Другое':
        keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
        for row in tz_2:
            keyboard.row(types.InlineKeyboardButton(row[0], callback_data=callbakes.new(action='get_timezone_2', value=row[0])),
                         types.InlineKeyboardButton(row[1], callback_data=callbakes.new(action='get_timezone_2', value=row[1])),
                         types.InlineKeyboardButton(row[2], callback_data=callbakes.new(action='get_timezone_2', value=row[2])))        
        await bot.edit_message_text('Выберите свой часовой пояс:',
                                    query.from_user.id,
                                    query.message.message_id,
                                    reply_markup=keyboard)
        return
    
    await state.update_data(timezone=int(value[3:]))
    await bot.edit_message_text('Часовой пояс успешно введен', query.from_user.id, query.message.message_id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('Ввести номер автоматически',request_contact=True))
    await bot.send_message(query.from_user.id, 'Теперь введите свой номер телефона вручную (+7**********)) или позвольте это сделать автоматически:',reply_markup=keyboard)
    await States.CONTACT.set()
    

@dp.callback_query_handler(callbakes.filter(action='get_timezone_2'),state=States.TIMEZONE)
async def process_callback(query: types.CallbackQuery, callback_data: dict):                 
    state = dp.current_state(user=query.from_user.id)
       
    value = callback_data['value']
    if value=='Назад':
        keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
        for row in tz_1:
            keyboard.row(types.InlineKeyboardButton(row[0], callback_data=callbakes.new(action='get_timezone', value=row[0])),
                         types.InlineKeyboardButton(row[1], callback_data=callbakes.new(action='get_timezone', value=row[1])),
                         types.InlineKeyboardButton(row[2], callback_data=callbakes.new(action='get_timezone', value=row[2])))        
        await bot.edit_message_text('Выберите свой часовой пояс:',
                                    query.from_user.id,
                                    query.message.message_id,
                                    reply_markup=keyboard)
        return    
    await state.update_data(timezone=int(value[3:])-3)    
    await bot.edit_message_text('Часовой пояс успешно введен',
                                query.from_user.id,
                                query.message.message_id)    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('Ввести номер автоматически',request_contact=True))
    await bot.send_message(query.from_user.id, 'Теперь введите свой номер телефона вручную (+7**********) или позвольте это сделать автоматически:',reply_markup=keyboard)
    await States.CONTACT.set()

#auto
@dp.message_handler(content_types=['contact'],state=States.CONTACT)
async def handle_location(msg: types.Message):
    state = dp.current_state(user=msg['from']['id'])
    
    data = await state.get_data()
    students_full_name = data['students_full_name']
    parents_full_name = data['parents_full_name']
    if parents_full_name == None: full_name = students_full_name
    else: full_name =  parents_full_name 
    
    number = str(msg['contact']['phone_number'])
    if number[0] != '+': number = '+'+number
    
    user_id = str(msg['from']['id'])
    if msg['from']['username'] != None:
        username = '@'+str(msg['from']['username']) 
    else: username = None
    
    try:
        for administrators_id in administators_ids:
            await bot.send_message(administrators_id, f'Пользователь c номером {number} и username {username} начал регистрацию')
    except: None
    
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)
    try:
        user_ids = is_in_file[number]
        is_in_file_flug = True 
    except: is_in_file_flug = False
        
    # is in db but not in the file
    if is_in_file_flug == False:
        number_id = {number: [user_id]}
        is_in_file.update(number_id)
        with open('is_in_file.txt','w') as data: 
            data.write(json.dumps(is_in_file))
    #is in file
    elif is_in_file_flug == True:
        user_ids = set(user_ids)
        user_ids.add(user_id)
        user_ids = list(user_ids)
        number_ids = {number: user_ids}
        
        is_in_file.update(number_ids)
        with open('is_in_file.txt','w') as data: 
            data.write(json.dumps(is_in_file))
    
    await state.update_data(number=number)
    
    keyboard = types.ReplyKeyboardRemove()
    await bot.send_message(user_id, 'Номер введен успешно', reply_markup=keyboard)
    
    try:
        mydict = {
        "_id" : number,
        "full_name" : full_name,
        "time_zone" : data['timezone']
        }

        base_students.insert_one(mydict)
    except: None      
    
    subjects = list(subject_id.keys())  
    with open('number_test_lessons.txt','r') as text: 
        data = text.read()
        if data == '': number_test_lessons = {}
        else: number_test_lessons = json.loads(data)
    
    await state.update_data(number_test_lessons=number_test_lessons)
    
    keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    
    is_lessons = False
    for subject in subjects:
        if number_test_lessons.get(number) != None:
            if number_test_lessons[number].get(subject) != None: continue
        keyboard.row(types.InlineKeyboardButton(subject, callback_data=callbakes.new(action='subject_choise', value=subject)))
        is_lessons = True
        
    if not is_lessons:
        await state.finish()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Записаться на бесплатный урок"]
        keyboard.add(*buttons)
        await bot.send_message(user_id, 'Похоже, что вы были на всех тестовых уроках. Попробуйте позже, когда у школы появятся новые предметы',reply_markup=keyboard)
        return 
    await bot.send_message(user_id, 'Выберите урок, на который хотите записаться:',reply_markup=keyboard)
    await States.SUBJECT.set() 
    
# not auto    
@dp.message_handler(state=States.CONTACT)
async def handle_location(msg: types.Message):
    state = dp.current_state(user=msg['from']['id'])
    user_id = str(msg['from']['id'])
    
    data = await state.get_data()
    students_full_name = data['students_full_name']
    parents_full_name = data['parents_full_name']
    if parents_full_name == None: full_name = students_full_name
    else: full_name =  parents_full_name 
    # if msg['text'][0] != '+': msg['text'] = '+'+msg['text']
    try:
        number_parse = phonenumbers.parse(msg['text'])
    except:
        await bot.send_message(user_id, 'Кажется, вы неправильно ввели номер. Попробуйте еще раз или позвольте ввести его автоматически')
        return
    
    if not phonenumbers.is_valid_number(number_parse):
        await bot.send_message(user_id, 'Кажется, вы неправильно ввели номер. Попробуйте еще раз или позвольте ввести его автоматически')
        return
    number = '+'+str(number_parse.country_code) + str(number_parse.national_number)
   
    if msg['from']['username'] != None:
        username = '@'+str(msg['from']['username']) 
    else: username = None
    try:
        for administrators_id in administators_ids:
            await bot.send_message(administrators_id, f'Пользователь c номером {number} и username {username} начал регистрацию')
    except: None
    
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)
    try:
        user_ids = is_in_file[number]
        is_in_file_flug = True 
    except: is_in_file_flug = False
        
    # is in db but not in the file
    if is_in_file_flug == False:
        number_id = {number: [user_id]}
        is_in_file.update(number_id)
        with open('is_in_file.txt','w') as data: 
            data.write(json.dumps(is_in_file))
    #is in file
    elif is_in_file_flug == True:
        user_ids = set(user_ids)
        user_ids.add(user_id)
        user_ids = list(user_ids)
        number_ids = {number: user_ids}
        
        is_in_file.update(number_ids)
        with open('is_in_file.txt','w') as data: 
            data.write(json.dumps(is_in_file))
           
    await state.update_data(number=number)
    
    keyboard = types.ReplyKeyboardRemove()
    await bot.send_message(user_id, 'Номер введен успешно', reply_markup=keyboard)

    try:
        mydict = {
        "_id" : number,
        "full_name" : full_name,
        "time_zone" : data['timezone']
        }
        base_students.insert_one(mydict)
    except: None
    
    subjects = list(subject_id.keys())  
    
    with open('number_test_lessons.txt','r') as text: 
        data = text.read()
        if data == '': number_test_lessons = {}
        else: number_test_lessons = json.loads(data)
    
    await state.update_data(number_test_lessons=number_test_lessons)
    
    keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    
    is_lessons = False
    for subject in subjects:
        if number_test_lessons.get(number) != None:
            if number_test_lessons[number].get(subject) != None: continue
        keyboard.row(types.InlineKeyboardButton(subject, callback_data=callbakes.new(action='subject_choise', value=subject)))
        is_lessons = True
        
    if not is_lessons:
        await state.finish()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Записаться на бесплатный урок"]
        keyboard.add(*buttons)
        await bot.send_message(user_id, 'Похоже, что вы были на всех тестовых уроках. Попробуйте позже, когда у школы появятся новые предметы',reply_markup=keyboard)
        return 
    
    await bot.send_message(user_id, 'Выберите урок, на который хотите записаться:',reply_markup=keyboard)
    await States.SUBJECT.set()
    
    
@dp.callback_query_handler(callbakes.filter(action='subject_choise'),state=States.SUBJECT)
async def process_callback(query: types.CallbackQuery, callback_data: dict):             
    state = dp.current_state(user=query.from_user.id)
    user_id = str(query.from_user.id)
     
    subject = callback_data['value']
    await state.update_data(subject=subject)
    
    keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    for grade in ['5 класс', '6 класс', '7 класс', '8 класс', '9 класс', '10 класс', '11 класс']:
        keyboard.row(types.InlineKeyboardButton(grade, callback_data=callbakes.new(action='grade_choise', value=grade)))
    await bot.edit_message_text('Укажи свой класс:', query.from_user.id, query.message.message_id, reply_markup=keyboard)
    await States.GRADE.set()
    

@dp.callback_query_handler(callbakes.filter(action='grade_choise'),state=States.GRADE)
async def process_callback(query: types.CallbackQuery, callback_data: dict):     
    state = dp.current_state(user=query.from_user.id)
    user_id = '@'+str(query.from_user.id)
    #get data
    grade = callback_data['value']
    await state.update_data(grade=grade)
    data = await state.get_data()
   
    subject = data['subject']
    number = data['number']
    timezone = int(data['timezone'])
    staff_id = subject_id[subject]['id_main_teacher']
    service_ids = [subject_id[subject]['id_subject']]
    
    if data['number_test_lessons'].get(number) != None:
        other_test_lessons = list(data['number_test_lessons'][number].values())
    else: other_test_lessons = []
    
    #get work_schedul
    now_date = (datetime.now() + timedelta(hours=timezone)).date() + timedelta(days=1) 
    # if now_date.date() < datetime.now(): now_date = datetime.now() + timedelta(hours=timezone+15) 
    now_for_path = str(now_date.day)+'.'+str(now_date.month)+'.'+str(now_date.year)
    end_for_path = str((now_date + timedelta(days=30)).day) + '.' + str((now_date + timedelta(days=30)).month) + '.' + str((now_date + timedelta(days=30)).year)
    
    uri = "https://api.yclients.com/api/v1/schedule/651183/{}/{}/{}".format(staff_id,now_for_path,end_for_path)
    headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
    work_schedul = json.loads(requests.get(uri, headers=headers).text)['data']
    
    # build seven days
    seven_days = []
    for work_day in work_schedul:
        # print(datetime.fromisoformat(day['date']))
        if work_day['is_working'] == 0: continue
        date = datetime.fromisoformat(work_day['date'])
        if len(seven_days) == 7: break
        #get simple data
        uri = "https://api.yclients.com/api/v1/book_times/651183/{}/{}".format(staff_id,str(date.day)+'.'+str(date.month)+'.'+str(date.year))
        headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
        params = {'service_ids' : service_ids}

        times_from_crm = json.loads(requests.get(uri, params=params, headers=headers).text)['data']
        time_start_day = work_day['slots'][0]['from']

        hours,minutes = time_start_day.split(':')
        if hours[0] == '0': hours = hours[1:]
        if minutes[0] == '0': minutes = minutes[1:]

        full_time_start_day = date + timedelta(hours=int(hours)+timezone,minutes=int(minutes))
        times = []
        for time in times_from_crm:
            times.append(time['time'])
        for count in range(len(times)):
            time = times[count]
            hours,minutes = time.split(':')
            if minutes[0] == '0': minutes = minutes[1:]
            full_time = date + timedelta(hours=int(hours)+timezone,minutes=int(minutes)) 
            times[count] = full_time
        # if is lesson in start
        try:
            if times[0] != full_time_start_day: times.insert(0, full_time_start_day)
        except: continue

        processed_times = times.copy()
        for count in range(1,len(times)):
            #search simple lessons
            time = times[count]
            if str(time - times[count-1]) != '0:15:00': 
                processed_times[count] = None
                processed_times[count-1] = None
            #search test lessons
            for time_other_lesson in other_test_lessons:
                time_other_lesson = datetime.fromisoformat(time_other_lesson) + timedelta(hours=timezone)
                if time_other_lesson == time: processed_times[count] = None
                elif time_other_lesson - timedelta(minutes=30) == time: processed_times[count] = None
                elif time_other_lesson - timedelta(minutes=15) == time: processed_times[count] = None
                elif time_other_lesson + timedelta(minutes=15) == time: processed_times[count] = None
                elif time_other_lesson + timedelta(minutes=30) == time: processed_times[count] = None
        # if is test lesson in start
        for time_other_lesson in other_test_lessons:
            time_other_lesson = datetime.fromisoformat(time_other_lesson) + timedelta(hours=timezone)
            if time_other_lesson == full_time_start_day: processed_times[0] = None
                
        if set(processed_times) == set([None]): continue            
                
        weekday = date.weekday()
        if weekday == 0 : weekday = 'Понедельник'
        if weekday == 1 : weekday = 'Вторник'
        if weekday == 2 : weekday = 'Среда'
        if weekday == 3 : weekday = 'Четверг'
        if weekday == 4 : weekday = 'Пятница'
        if weekday == 5 : weekday = 'Суббота'
        if weekday == 6 : weekday = 'Воскресенье'
        
        if len(str(date.day)) == 1:
            days = '0'+str(date.day)
        else: days = str(date.day)
        beautiful_date = '('+str(date.month)+'.'+days+')'
        # for time in processed_times:
        #     processed_times[processed_times.index(time)] = str(time)
        seven_days.append({'date':date,'times':processed_times,'weekday':weekday + ' ' + beautiful_date})
        
    keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    await state.update_data(seven_days=seven_days)

    for day in seven_days:        
        keyboard.row(types.InlineKeyboardButton(day['weekday'], callback_data=callbakes.new(action='weekday_choise', value=day['weekday'])))
    await bot.edit_message_text('Выберите день:', query.from_user.id, query.message.message_id, reply_markup=keyboard)
    await States.DAY.set()
    
    
@dp.callback_query_handler(callbakes.filter(action='weekday_choise'),state=States.DAY)
async def process_callback(query: types.CallbackQuery, callback_data: dict):                 
    state = dp.current_state(user=query.from_user.id)
    user_id = str(query.from_user.id)
    
    weekday = callback_data['value']
    await state.update_data(weekday=weekday)
    
    data = await state.get_data()
    seven_days = data['seven_days']
    
    for choised_day in seven_days:
        if choised_day['weekday'] == weekday: break
    await state.update_data(choised_day=choised_day)
    
    keyboard = types.InlineKeyboardMarkup(resize_keyboard=True, row_width=4)
    buttons = []
    for time in choised_day['times']:
        if time == None: continue
        if len(str(time.minute)) == 1:
            minute = '0'+str(time.minute)
        else: minute = str(time.minute)
        beautiful_time = str(time.hour)+':'+minute
        buttons.append(types.InlineKeyboardButton(beautiful_time, callback_data=callbakes.new(action='time_choise', value=beautiful_time.replace(':','-'))))
        
    keyboard.add(*buttons)
    keyboard.row(types.InlineKeyboardButton('Назад', callback_data=callbakes.new(action='time_choise', value='Назад')))
    await bot.edit_message_text('Выберите время:', query.from_user.id, query.message.message_id, reply_markup=keyboard)
    await States.TIME.set()
    
    
@dp.callback_query_handler(callbakes.filter(action='time_choise'),state=States.TIME)
async def process_callback(query: types.CallbackQuery, callback_data: dict):           
    state = dp.current_state(user=query.from_user.id)
    user_id = str(query.from_user.id)
    username = '@'+query.from_user.username
    
    data = await state.get_data()
    simple_time = callback_data['value'].replace('-',':')
    seven_days = data['seven_days']
    # await state.update_data(value=value)
    if simple_time == 'Назад':
        keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
        for day in seven_days:        
            keyboard.row(types.InlineKeyboardButton(day['weekday'], callback_data=callbakes.new(action='weekday_choise', value=day['weekday'])))
        await bot.edit_message_text('Выберите день:', query.from_user.id, query.message.message_id, reply_markup=keyboard)
        await States.DAY.set()
        return
    #get data
    data = await state.get_data()
    grade = data['grade']
    subject = data['subject']
    number = data['number']
    # full_name = data['full_name']
    timezone = int(data['timezone'])
    staff_id = subject_id[subject]['id_main_teacher']
    service_ids = subject_id[subject]['id_subject']
    weekday = data['weekday']
    choised_day = data['choised_day']
    
    students_full_name = data['students_full_name']
    parents_full_name = data['parents_full_name']
    if parents_full_name == None: full_name = students_full_name
    else: full_name =  parents_full_name 
    
    if data['number_test_lessons'].get(number) != None:
        other_test_lessons = list(data['number_test_lessons'][number].values())
    else: other_test_lessons = []
    
    time_start_for_crm = choised_day['date'] + timedelta(hours=int(simple_time.split(':')[0])-timezone,minutes=int(simple_time.split(':')[1]))    
    #create lesson
    data = json.dumps({
        "staff_id" : staff_id,
        'services' : [{'id':subject_id[subject]['id_subject']}],
        'client' : {'phone':number,'name':full_name.split(' ')[1]},
        'datetime' : str(time_start_for_crm),
        'seance_length' : 1800,
        'send_sms' : False,
        'save_if_busy' : True
    })
    uri = "https://api.yclients.com/api/v1/records/651183/"
    headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
    response = json.loads(requests.post(uri, headers=headers, data=data).text)
    success = response['success']
    client_id = response['data']['client']['id']

    #edit client
    data = json.dumps({'labels': [categories[grade]], 'comment':f'Ученик: {students_full_name}'})
    uri = f"https://api.yclients.com/api/v1/client/651183/{client_id}"
    headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
    params = {'name': full_name.replace(' ',''), 'phone':number}
    response = json.loads(requests.put(uri, headers=headers, params=params, data=data).text)

    #edit number_test_lessons.txt
    with open('number_test_lessons.txt','r') as text: 
        data = text.read()
        if data == '': number_test_lessons = {}
        else: number_test_lessons = json.loads(data)
        
    if number_test_lessons.get(number)!= None:
        number_test_lessons[number].update({subject:str(time_start_for_crm)})
    else:
        number_test_lessons.update({number:{subject:str(time_start_for_crm)}})
    
    with open('number_test_lessons.txt','w') as data: 
        data.write(json.dumps(number_test_lessons))
        
    if weekday.split(' ')[0] == 'Понедельник': weekday = 'в Понедельник ' + weekday.split(' ')[1]
    if weekday.split(' ')[0] == 'Вторник': weekday = 'во Вторник ' + weekday.split(' ')[1]
    if weekday.split(' ')[0] == 'Среда': weekday = 'в Среду ' + weekday.split(' ')[1]
    if weekday.split(' ')[0] == 'Четверг': weekday = 'в Четверг ' + weekday.split(' ')[1]
    if weekday.split(' ')[0] == 'Пятница': weekday = 'в Пятницу ' + weekday.split(' ')[1]
    if weekday.split(' ')[0] == 'Суббота': weekday = 'в Субботу ' + weekday.split(' ')[1]
    if weekday.split(' ')[0] == 'Воскресенье': weekday = 'в Воскресенье ' + weekday.split(' ')[1]
        
    # try:
    if len(str(time_start_for_crm.minute))==1: minutes='0'+str(time_start_for_crm.minute)
    else: minutes = str(time_start_for_crm.minute)
    for administrators_id in administators_ids:
        await bot.send_message(administrators_id, f'Пользователь (ФИО опекуна: {parents_full_name}, ФИО ученика: {students_full_name}) c номером {number} и username {username} закончил регистрацию\nЗаписан {weekday} на {time_start_for_crm.hour}:{minutes} на пробный урок по предмету {subject}')
    # except: None
    # keyboard = types.InlineKeyboardMarkup(resize_keyboard=True, row_width=4)
    # keyboard.row(types.InlineKeyboardButton('Назад', callback_data=callbakes.new(action='time_choise', value='Назад')))
        
    await bot.edit_message_text(f'Вы были записаны на пробный урок по предмету {subject} {weekday} на {simple_time}\nЧтобы получить уведомление об уроке за 6 часов перейдите к основному боту школы @A3artShool_bot и нажмите /start.\nТакже в скором времени с вами свяжется администратор школы, чтобы познакомиться)', query.from_user.id, query.message.message_id)
    
 
    
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)