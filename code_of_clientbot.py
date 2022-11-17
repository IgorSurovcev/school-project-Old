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
import traceback
import phonenumbers
from phonenumbers import carrier, timezone, geocoder
from aiogram.utils.callback_data import CallbackData
import random

from datetime import datetime, timedelta, timezone

password = urllib.parse.quote_plus('7ZfrNV3ifnWf2oor')
client = MongoClient('mongodb+srv://coolpoint:%s@coolpoint-cluster.5g2rs.mongodb.net/?retryWrites=true&w=majority' % (password))

base = client['base_of_peoples']
base_teachers = base['teachers']
base_students = base['students']

base_of_events = client['base_of_events']
promo_codes = base_of_events['promo_codes']

blanks = {
    'welcome' : 'Вы зарегистрированы! 😍\nДобро пожаловать в A3artShool! 😊\nЧто умеет этот бот?\n📌Напоминает о предстоящих занятиях\n📌Присылает домашние задания и записи уроков\n📌Обеспечивает надежность оплат\n📌Здесь можно купить абонемент\n📌Говорит сколько осталось уроков на балансе\n📌Рассказывает о важных новостях в A3artschool\n\nМы каждый день стараемся сделать нашу систему лучше, следите за новостями!',

    'not_username_in_base':'Привет! На связи A3artSchool! ✌️\nЗдесь можно записаться на бесплатный тестовый урок, чтобы познакомиться с нами поближе.\nУрок длится 30 минут, где мы вместе выясним какой текущий уровень знаний, определим главную цель занятий и составим план подготовки.\nЧтобы записаться на урок кликай кнопку ниже!'
}

tz_1 = [['МСК-1','МСК+0','МСК+1'],['МСК+2','МСК+3','МСК+4'],['МСК+5','МСК+6','МСК+7'],['МСК+8','МСК+9','Другое']]
tz_2 = [['GMT+0', 'GMT+1','GMT+2'], ['GMT-1', 'GMT-2', 'GMT-3'], ['GMT-4', 'GMT-5', 'GMT-6'], ['GMT-7', 'GMT-8', 'GMT-9'], ['GMT-10','GMT-11','Назад']]
administators_ids = [676352317, 1226474188] #1226474188

# staff_ids = {''}
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

    
API_TOKEN = '5473320366:AAEwnENs-cyjGA5pBJFA-qpeHiU-v4B2_5A'

# API_TOKEN = '5637578020:AAG9UtnefJHHZXHzs4v_9lt_7phGkt6BJC4'

from logdna import LogDNAHandler
key='d7903ac4bec957d8e8d0ab45479fdd45'
log = logging.getLogger('logdna')
log.setLevel(logging.DEBUG)
options = {  'hostname': 'hostkey17726',  'ip': '46.17.100.162',  'mac': '56:6f:ff:5b:01:24'}
options['index_meta'] = True
mezmo = LogDNAHandler(key, options)
logging.basicConfig(level=logging.INFO)
logging.basicConfig(handlers=[mezmo])

class States(StatesGroup):
    NEWSLETTER = State()
    BUY_FOR_ONE_FROM_FAMILY = State()
    CHOISE_ABONEMENT = State()

    GO_STARTBOT = State()
    
    CHOISE_FULLNAME = State()
    ONE_FULLNAME = State()
    TWO_FULLNAME = State()
    SECOND_FULLNAME = State()
    TIMEZONE = State()
    CONTACT = State()
    PROMO_CODE = State()
    SUBJECT = State()
    GRADE = State()
    DAY = State()
    TIME = State()

    TEACHER = State()
    SEND_HOMETASK = State()

    CHOISE_STUDENT = State()
    
callbakes = CallbackData('callback','action','value')

    
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

access = ['VuplesOwl', 'A3artt']

# услуга - соответствуующий абонемент. Математика, русский
item_ids = {'10937974':'22352808', '10940358':'22352794'}
subjects = ['Математика', 'Русский язык']



dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands='start')
async def start_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    username = '@'+str(msg.from_user.username)
    
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)
    with open('deleted_user_ids.txt','r') as data: 
        text = data.read()
        if text == '': deleted_user_ids = {}
        else: deleted_user_ids = json.loads(text)
        
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Следующий урок", "Купить"]
    buttons_2 = ["Баланс", "Контакты", "Остановить уведомления"]
    keyboard.add(*buttons)
    keyboard.row(*buttons_2)
    
    numbers = []
    for number in is_in_file:
        for user_id_file in is_in_file[number]:
            if user_id == user_id_file: numbers.append(number)
        
    if numbers == [] and deleted_user_ids.get(user_id) == None:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Записаться на бесплатный урок"]
        keyboard.add(*buttons)
        await bot.send_photo(user_id, photo=open('image2.png',"rb"),caption=blanks['not_username_in_base'], reply_markup=keyboard)
        for administrators_id in administators_ids:
            await bot.send_message(administrators_id, f'Новый пользователь {username}')
        # await States.GO_STARTBOT.set()

    elif numbers == [] and deleted_user_ids.get(user_id)!=None:
        for deleted_number in deleted_user_ids[user_id]:
            is_in_file[deleted_number].append(user_id)
            deleted_user_ids.update({user_id:[]})

            with open('is_in_file.txt','w') as data: 
                data.write(json.dumps(is_in_file))
            with open('deleted_user_ids.txt','w') as data: 
                data.write(json.dumps(deleted_user_ids))
            
        await bot.send_photo(user_id, photo=open('image3.png',"rb"),caption=blanks['welcome'], reply_markup=keyboard)
    else: 
        await bot.send_photo(user_id, photo=open('image3.png',"rb"),caption=blanks['welcome'], reply_markup=keyboard)
        
# START FOR TEACHERS
@dp.message_handler(commands='start_teacher',state='*')
async def start_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    username = '@'+str(msg.from_user.username)

    items = base_teachers.find({'user_id':user_id})
    for item in items:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Отправить домашнее задание"]
        keyboard.add(*buttons)

        await bot.send_message(user_id, 'Добро пожаловать в бота взаимодействия с учениками.\nЗдесь вы можете отправить домашнее задание и запись урока ученику после урока. Запись урока отправится последнему ученику, с кем начался урок, то есть вы должны отправить запись до начала следующего урока, иначе уже не сможете. А домашне заданее сможете прислать потом, но не позже трех дней, после начала урока. По вопросам или уточнениям обращайтесь к администратору', reply_markup=keyboard)

        # await States.TEACHER.set()


# @dp.message_handler(content_types=types.ContentType.TEXT,state=States.TEACHER)

@dp.message_handler(lambda message: message.text[:8] == 'https://')
@dp.message_handler(text=['Отправить домашнее задание'])
async def start_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    state = dp.current_state(user=msg.from_user.id)

    if msg.text == 'Отправить домашнее задание':
        items = base_teachers.find({'user_id':user_id})
        for item in items:
            staff_id = item['staff_id']
            teachers_time_zone = item['time_zone']

            uri = "https://api.yclients.com/api/v1/records/651183"
            headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
            now = datetime.today() + timedelta(hours=3)
            start_day = now - timedelta(days=1)
            start_day_str = str(start_day.day)+'.'+str(start_day.month)+'.'+str(start_day.year)
            end_day_str = str(now.day)+'.'+str(now.month)+'.'+str(now.year)
            params = {'start_date': start_day_str, 'end_date': end_day_str, 'staff_id':staff_id}
            records_crm = json.loads(requests.get(uri, params=params, headers=headers).text)['data']

            with open('records_file.txt','r') as text: 
                data = text.read()
                if data == '': records_file = {}
                else: records_file = json.loads(data)

            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            interpretation_buttons = {}
            for record in reversed(records_crm):
                record_id = str(record['id'])
                if record['deleted']!=True and records_file.get(record_id) != None and records_file[record_id].get('got_hometask')==None and datetime.fromisoformat(record['date']) < now:
                    students_name = records_file[record_id]['students_name']
                    teachers_time_start = datetime.fromisoformat(record['date']) + timedelta(hours=int(teachers_time_zone))
                    teachers_time_start_str = str(teachers_time_start.day)+'.'+str(teachers_time_start.month)+'.'+str(teachers_time_start.year)

                    if len(str(teachers_time_start.minute)) == 1:
                        minute = '0'+str(teachers_time_start.minute)
                    else: minute = str(teachers_time_start.minute)
                    beautiful_time = str(teachers_time_start.hour)+':'+minute
                    answer = students_name+' '+teachers_time_start_str+' '+ beautiful_time
                    keyboard.add(answer)
                    interpretation_buttons.update({answer:record_id})

            keyboard.add('Отмена')
            await bot.send_message(user_id, 'Выбери ученика, по прошедшему уроку', reply_markup=keyboard)
            await state.update_data(interpretation_buttons=interpretation_buttons)
            await States.CHOISE_STUDENT.set()

    if msg.text[:8] == 'https://':
        items = base_teachers.find({'user_id':user_id})
        for item in items:
            staff_id = item['staff_id']
            teachers_time_zone = item['time_zone']

            uri = "https://api.yclients.com/api/v1/records/651183"
            headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
            now = datetime.today() + timedelta(hours=3)
            start_day_str = str(now.day)+'.'+str(now.month)+'.'+str(now.year)
            params = {'start_date': start_day_str, 'end_date':start_day_str,'staff_id':staff_id}
            records_crm = json.loads(requests.get(uri, params=params, headers=headers).text)['data']

            with open('records_file.txt','r') as text: 
                data = text.read()
                if data == '': records_file = {}
                else: records_file = json.loads(data)
            with open('is_in_file.txt','r') as data: 
                text = data.read()
                if text == '': is_in_file = {}
                else: is_in_file = json.loads(text)

            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            time_records = {}
            times = []
            for record in reversed(records_crm):
                record_id = str(record['id'])
                time_start = datetime.fromisoformat(record['date'])
                if record['deleted']!=True and records_file.get(record_id) != None and time_start < now:
                    students_name = records_file[record_id]['students_name']
                    times.append(time_start)
                    time_records.update({time_start:[students_name,records_file[record_id]['number'],records_file[record_id].get('got_record'),record_id]})
                    # answer = 'Ссылка отправлена: '+students_name+' '+teachers_time_start_str+' '+ beautiful_time
                    # keyboard.add(answer)
                    # interpretation_buttons.update({answer:record_id})
            times.sort()
            if times == []:
                await bot.send_message(user_id, 'У тебя сегодня не было уроков')
                return
            time_record = time_records[times[-1]]
            if time_record[2] != None:
                await bot.send_message(user_id, 'Прошлому ученику уже приходила ссылка', reply_markup=keyboard)
                return

            students_name = time_record[0]
            number = time_record[1]
            record_id = time_record[3]

            ids = is_in_file[number]
            for student_user_id in ids:
                try:
                    # student_user_id = 1226474188
                    await bot.send_message(student_user_id, 'Ссылка на запись урока:\n'+msg.text)
                except Exception as e:
                    print('error send link record',e, student_user_id)

            records_file[record_id].update({'got_record':True})
            with open('records_file.txt','w') as file: 
                file.write(json.dumps(records_file))

            await bot.send_message(user_id, 'Ссылка отправлена: '+students_name, reply_markup=keyboard)
            


@dp.message_handler(state=States.CHOISE_STUDENT)
async def start_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    state = dp.current_state(user=msg.from_user.id)
    if msg.text=='Отмена': 
        await state.finish()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Отправить домашнее задание"]
        keyboard.add(*buttons)
        await msg.reply("Отменено", reply_markup=keyboard)
        # await States.TEACHER.set()
        return

    await state.update_data(choise=msg.text)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*['Нет задания','Отмена'])
    await bot.send_message(user_id, 'Пришли домашнее задание. Что отправишь, то и придет ученику (файл, изображение, текст)\nИли сообщи, что нет домашнего задания', reply_markup=keyboard)
    await States.SEND_HOMETASK.set()

@dp.message_handler(state=States.SEND_HOMETASK,content_types=types.ContentType.ANY)
async def start_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    username = '@'+str(msg.from_user.username)
    state = dp.current_state(user=msg.from_user.id)
    if msg.text=='Отмена': 
        await state.finish()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Отправить домашнее задание"]
        keyboard.add(*buttons)
        await msg.reply("Отменено", reply_markup=keyboard)
        # await States.TEACHER.set()
        return

    data = await state.get_data()
    record_id = data['interpretation_buttons'][data['choise']]

    with open('records_file.txt','r') as text: 
        data = text.read()
        if data == '': records_file = {}
        else: records_file = json.loads(data)
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)

    if msg.text=='Нет задания': 
        records_file[record_id].update({'got_hometask':True})
        with open('records_file.txt','w') as file: 
            file.write(json.dumps(records_file))

        await state.finish()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Отправить домашнее задание"]
        keyboard.add(*buttons)
        await msg.reply("Отменено", reply_markup=keyboard)
        return

    number = records_file[record_id]['number']
    ids = is_in_file[number]
    for student_user_id in ids:
        try:
            # student_user_id = 1226474188
            time.sleep(0.1)
            if msg.photo:
                await bot.send_photo(student_user_id, photo=msg.photo[-1].file_id,caption=msg.caption)
            elif msg.video:
                await bot.send_video(student_user_id, video=msg.video.file_id,caption=msg.caption)
            elif msg.text:
                # await bot.send_message(student_user_id, msg.text)
                await bot.send_message(student_user_id, msg.text)
            elif msg.document:
                await bot.send_document(student_user_id, document=msg.document.file_id,caption=msg.caption)
        except Exception as e:
            print('error send hometask',e, student_user_id)

    records_file[record_id].update({'got_hometask':True})
    with open('records_file.txt','w') as file: 
        file.write(json.dumps(records_file))
        
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Отправить домашнее задание"]
    keyboard.add(*buttons)
    await bot.send_message(user_id, 'Домашнее задание было отправлено', reply_markup=keyboard)




# START FOR NEW STUDENTS
@dp.message_handler(text=['Записаться на бесплатный урок','записаться на бесплатный урок'])
# @dp.message_handler(text=['Записаться на бесплатный урок','записаться на бесплатный урок'])
async def func(msg: types.Message):
    user_id = str(msg.from_user.id)
    state = dp.current_state(user=msg.from_user.id)

    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)
    with open('deleted_user_ids.txt','r') as data: 
        text = data.read()
        if text == '': deleted_user_ids = {}
        else: deleted_user_ids = json.loads(text)
        
    numbers = []
    for number in is_in_file:
        for user_id_file in is_in_file[number]:
            if user_id == user_id_file: numbers.append(number)
        
    if numbers == [] and deleted_user_ids.get(user_id) == None:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Для себя","Для ребенка"]
        keyboard.add(*buttons)
        
        await bot.send_message(user_id, 'Отлично!\nВы будете заниматься сами или записываете ребенка?', reply_markup=keyboard)
        await States.CHOISE_FULLNAME.set()
    


# COMMANDS FOR STUDENTS
@dp.message_handler(text=['Купить'])
async def start_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    print(user_id)
    state = dp.current_state(user=user_id)
    
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)
    
    numbers = []
    for number in is_in_file:
        for user_id_file in is_in_file[number]:
            if user_id == user_id_file: numbers.append(number)
            
    if len(numbers) != 1:
        name_discount = {}
        buttons = []
        for number in numbers:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            base = base_students.find({'_id':number})
            for item in base:
                name = item['full_name'].split(' ')[1]
                name_for_crm = item['full_name'].split(' ')[1]+item['full_name'].split(' ')[0]
                
                one_time_discounts = item.get('one_time_discounts')
                if one_time_discounts != None:
                    discounts = one_time_discounts
                    base_students.update_one({"_id": item['_id']}, 
                                                     {"$set": {'one_time_discounts': None}})
                else:
                    discounts = item['discounts']
            name_discount.update({name:[number,discounts,name_for_crm]})
            buttons.append(name)
            
        keyboard.add(*buttons)
        await state.update_data(name_discount=name_discount)
        await bot.send_message(user_id,'Выберите ребенка, которому хотите купить абонемент', reply_markup=keyboard)
        await States.BUY_FOR_ONE_FROM_FAMILY.set()
    else:
        base = base_students.find({'_id':numbers[0]})
        for item in base:
            one_time_discounts = item.get('one_time_discounts')
            if one_time_discounts != None:
                discounts = one_time_discounts
                base_students.update_one({"_id": item['_id']}, 
                                                 {"$set": {'one_time_discounts': None}})
            else:
                discounts = item['discounts']
            name_for_crm = item['full_name'].split(' ')[1]+item['full_name'].split(' ')[0]
        await state.update_data(discounts=discounts,number=numbers[0],name_for_crm=name_for_crm)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(*[f"Абонемент Математика (x10) - {int(10000 * (100 - int(discounts.split(' ')[0]))*0.01)}₽"])
        keyboard.add(*[f"Абонемент Русский язык (x10) - {int(10000 * (100 - int(discounts.split(' ')[1]))*0.01)}₽"])
        keyboard.add(*["Назад"])
        await bot.send_message(user_id,'Выберите абонемент', reply_markup=keyboard)
        await States.CHOISE_ABONEMENT.set()
    
    
@dp.message_handler(state=States.BUY_FOR_ONE_FROM_FAMILY)
async def start_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    state = dp.current_state(user=user_id)
    
    data = await state.get_data()
    discounts = data['name_discount'][msg.text][1]
    number = data['name_discount'][msg.text][0]
    name_for_crm = data['name_discount'][msg.text][2]
    
    await state.update_data(discounts=discounts,number=number,name_for_crm=name_for_crm)
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[f"Абонемент Математика (x10) - {int(10000 * (100 - int(discounts.split(' ')[0]))*0.01)}₽"])
    keyboard.add(*[f"Абонемент Русский язык (x10) - {int(10000 * (100 - int(discounts.split(' ')[1]))*0.01)}₽"])
    keyboard.add(*["Назад"])
    await bot.send_message(user_id,'Выберите абонемент', reply_markup=keyboard)
    await States.CHOISE_ABONEMENT.set()
    
    
@dp.message_handler(state=States.CHOISE_ABONEMENT)
async def start_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    print(user_id)
    state = dp.current_state(user=user_id)
    if msg.text=='Назад': 
        await state.finish()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        buttons = ["Следующий урок", "Купить"]
        buttons_2 = ["Баланс", "Контакты", "Остановить уведомления"]
        keyboard.add(*buttons)
        keyboard.row(*buttons_2)
        await bot.send_message(user_id,"Покупка отменена", reply_markup=keyboard)
        return
    
    data = await state.get_data()
    discounts = data['discounts']
    number = data['number']
    name = data['name_for_crm']
    
    subject = msg.text.split(' - ')[0]
    
    if subject == 'Абонемент Математика (x10)': 
        discount = int(discounts.split(' ')[0])
        service = '10937974'
    elif subject == 'Абонемент Русский язык (x10)':
        discount = int(discounts.split(' ')[1])
        service = '10940358'
    
    with open('number_link.txt','r') as data: 
        text = data.read()
        if text == '': number_link = {}
        else: number_link = json.loads(text)
        
    # if is other open transaction have to delite this    
    if number_link.get(number)!=None:
        is_old_link = False
        for service_in_waiting in number_link[number]:
            if service_in_waiting != service:
                is_old_link = True
                deleting_record_id = number_link[number][service_in_waiting]['record_id']
                uri = f'https://api.yclients.com/api/v1/record/651183/{deleting_record_id}'
                headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
                params = {'include_consumables':0, 'include_finance_transactions':0}
                requests.delete(uri, params=params,headers=headers)
        if is_old_link == True:        
            number_link[number].pop(service_in_waiting)
            with open('number_link.txt','w') as file: 
                file.write(json.dumps(number_link))
           
        
    do_link = False
    if number_link.get(number)==None: do_link = True
    if number_link.get(number)!=None:
        if number_link[number].get(service)==None: do_link = True
        
    if do_link == True:
        #get client id
        uri = "https://api.yclients.com/api/v1/company/651183/clients/search/"
        headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
        data = json.dumps({'fields' : ['id','phone','discount'], 'page_size': 300})
        for client in json.loads(requests.post(uri, headers=headers, data=data).text)['data']: 
            if client['phone'] == number: 
                old_discount = client['discount']
                client_id = client['id']

        #edit client discount
        # discount = 99.9
        data = json.dumps({'discount': discount})
        uri = f"https://api.yclients.com/api/v1/client/651183/{client_id}"
        headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
        params = {'name':name,'phone':number}
        response = json.loads(requests.put(uri, headers=headers, params=params, data=data).text)

        #create lesson for uri
        uri = "https://api.yclients.com/api/v1/records/651183/"
        headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
        data = json.dumps({
            "staff_id" : '1858699',
            'services' : [{'id': service}],
            'client' : {'phone': number},
            'datetime' : str(datetime(datetime.now().year,datetime.now().month,datetime.now().day,6)),
            'seance_length' : 300,
            'send_sms' : False,
            'save_if_busy' : True
        })

        #get uri
        record_id = json.loads(requests.post(uri, headers=headers, data=data).text)['data']['id']

        uri = f'https://api.yclients.com/api/v1/record/651183/{record_id}'
        headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
        params = {'short_link_token':1}
        short_link_token = json.loads(requests.get(uri, params=params,headers=headers).text)['data']['short_link_token']

        link = f'https://yclients.com/pay/{short_link_token}/'

        data = json.dumps({'discount': old_discount})
        uri = f"https://api.yclients.com/api/v1/client/651183/{client_id}"
        headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
        params = {'name':name,'phone':number}
        response = json.loads(requests.put(uri, headers=headers, params=params, data=data).text)
        
        if number_link.get(number)==None:
            number_link.update({number:{service:{'link':link, 'record_id': record_id}}})
        else:
            number_link[number].update({service:{'link':link, 'record_id': record_id}}) 

        with open('number_link.txt','w') as file: 
            file.write(json.dumps(number_link))

    else:
        link = number_link[number][service]['link']
    
    await state.finish()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Следующий урок", "Купить"]
    buttons_2 = ["Баланс", "Контакты", "Остановить уведомления"]
    keyboard.add(*buttons)
    keyboard.row(*buttons_2)
    await bot.send_message(user_id,"*Ссылка на оплату:* "+link+"\n_\rПосле перевода абонемент автоматически зачислится на ваш баланс, обработка транзакции занимает около минуты_\r", reply_markup=keyboard, parse_mode=types.ParseMode.MARKDOWN)
    
    
    

@dp.message_handler(text=['Баланс','баланс'])
async def start_handler(msg: types.Message):

    user_id = str(msg.from_user.id)
    print(user_id)
    
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)

    numbers = []
    for number in is_in_file:
        for user_id_file in is_in_file[number]:
            if user_id == user_id_file: numbers.append(number)
                
    # print(numbers)            
    # number = +79512572202
    balences = {}
    for number in numbers:
        uri = 'https://api.yclients.com/api/v1/loyalty/abonements/'
        headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
        params = {'company_id' : '651183','phone' : number}
        response = json.loads(requests.get(uri, params=params,headers=headers).text)['data']
        
        if response == []:
            balences.update({number:None})
        else:
            balences.update({number:{}})
            for subject in subjects:
                balences[number].update({subject:0})
                
            for balance in response:
                subject = balance['balance_string'].split(',')[0]
                balences[number].update({subject:balences[number][subject]+balance['united_balance_services_count']})
                
    if len(numbers) == 1:
        if balences[number] != None:
            answer = 'Cписок ваших абонементов и оставшиеся занятия по абонементу:\n'
            for balance_of_subject in balences[number]:
                if balences[number][balance_of_subject] != 0:
                    answer += balance_of_subject+': '+str(balences[number][balance_of_subject])+'\n'
        else:
            answer = 'Абонемент не подключен'

    else:
        answer = '*Список абонементов*\n'
        for number in numbers:
            item_student = base_students.find({'_id':number})
            name = ''
            for item in item_student:
                name += item['full_name'].split(' ')[1]
            answer += '*'+name+'*:\n'
            
            if balences[number] != None:
                for balance_of_subject in balences[number]:
                    if balences[number][balance_of_subject] != 0:
                        answer += '*·* '+balance_of_subject+': '+str(balences[number][balance_of_subject])+'\n'
            else:
                answer += '  Абонемент не подключен\n'
    await bot.send_message(user_id,answer,parse_mode=types.ParseMode.MARKDOWN)
                    

@dp.message_handler(text=['Контакты','контакты'])
async def start_handler(msg: types.Message):

    user_id = str(msg.from_user.id)
    print(user_id)
    answer = "Контакты администратора для любых вопросов:\n@A3artt\n+79080905277"
    
    await bot.send_message(user_id,answer)
    
@dp.message_handler(text=['Остановить уведомления','остановить уведомления'])
async def start_handler(msg: types.Message):

    user_id = str(msg.from_user.id)
    print(user_id)
    
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)
        
    with open('deleted_user_ids.txt','r') as data: 
        text = data.read()
        if text == '': deleted_user_ids = {}
        else: deleted_user_ids = json.loads(text)
        
    deleted_user_ids.update({user_id:[]})
    for number in is_in_file:
        user_ids = is_in_file[number]

        for user_id_file in user_ids:
            if user_id_file == str(user_id): 
                deleted_user_ids[user_id].append(number)
                # deleted_numbers.append(number)
  
                user_ids.pop(user_ids.index(user_id_file))
                is_in_file.update({number:user_ids})
                with open('is_in_file.txt','w') as data: 
                    data.write(json.dumps(is_in_file))
                    
    with open('deleted_user_ids.txt','w') as data: 
        data.write(json.dumps(deleted_user_ids))
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["/start"]
    keyboard.add(*buttons)

    answer='Уведомления вам были остановлены.\nЕсли захотите их возобновить, то просто напишите /start'    
    await bot.send_message(user_id,answer, reply_markup=keyboard)
                

                
@dp.message_handler(text=['Следующий урок','cледующий урок'])
async def start_handler(msg: types.Message):

    user_id = str(msg.from_user.id)
    print(user_id)     
    
    # get number
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)

    numbers = []
    for number in is_in_file:
        for user_id_file in is_in_file[number]:
            if user_id == user_id_file: numbers.append(number)
                
    # number = '+79124091315' 
    users_records = {}
    for number in numbers:
        # find the recent record   
        uri = "https://api.yclients.com/api/v1/records/651183"
        headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
        params = {'start_date' :  str(datetime.today().day)+'.'+str(datetime.today().month)+'.'+str(datetime.today().year), 'phone' : number}

        records_crm = json.loads(requests.get(uri, params=params, headers=headers).text)['data']

        with open('records_file.txt','r') as text: 
            data = text.read()
            if data == '': records_file = {}
            else: records_file = json.loads(data)
            
        users_records.update({number:{}})    
        for subject in subjects:
            is_record = False
            for record in reversed(records_crm):
                record_id = str(record['id'])
                if '+'+str(record['client']['phone']) == number and record['services'][0]['title'].find(subject) != -1 and record['deleted']!=True and record['attendance']==0 and records_file.get(record_id) != None:
                    record_file = records_file[record_id]
                    students_time_zone = record_file['students_time_zone']
                    students_time_start = datetime.fromisoformat(record['date']) + timedelta(hours=int(students_time_zone))
                    now = datetime.now() + timedelta(hours=int(students_time_zone)+3)
                    if students_time_start > now:
                        is_record = True
                        break
                        
            if is_record == False:
                users_records[number].update({subject:None})
                continue

            # print(students_time_start)
            # beuty time and weekday
            if len(str(students_time_start.minute)) == 1:
                minute = '0'+str(students_time_start.minute)
            else: minute = str(students_time_start.minute)
            beautiful_time = str(students_time_start.hour)+':'+minute

            date = str(students_time_start.day) + '.' + str(students_time_start.month)

            if len(str(students_time_start.month)) == 1:
                month = '0'+str(students_time_start.month)
            else: month = str(students_time_start.month)

            date = str(students_time_start.day) + '.' + month

            if students_time_start.day - now.day == 0: recent = 'сегодня'
            elif students_time_start.day - now.day == 1: recent = 'завтра'
            elif students_time_start.day - now.day == 2: recent = 'послезавтра'
            else: recent = False

            weekday = students_time_start.weekday()
            if weekday == 0 : weekday = 'в Понедельник'
            if weekday == 1 : weekday = 'во Вторник'
            if weekday == 2 : weekday = 'в Среду'
            if weekday == 3 : weekday = 'в Четверг'
            if weekday == 4 : weekday = 'в Пятницу'
            if weekday == 5 : weekday = 'в Субботу'
            if weekday == 6 : weekday = 'в Воскресенье'

            # answer = 'Следующий урок по расписанию '
            beuty_fulltime = ''
            if recent==False:
                beuty_fulltime += weekday + ', ' + date + ' в ' + beautiful_time 
            else:
                beuty_fulltime += recent + ' в ' + beautiful_time
                
            users_records[number].update({subject:beuty_fulltime})
            # await bot.send_message(user_id,answer)
    
    answer = ''
    if len(numbers) != 1:
        for number in users_records:
            item_student = base_students.find({'_id':number})
            name = ''
            for item in item_student:
                name += item['full_name'].split(' ')[1]
                
            answer += '*'+name+'*:\n'
            is_lesson = False
            for subject in users_records[number]:
                if users_records[number][subject] != None:
                    is_lesson = True
                    answer += '*·* '+subject+' '+users_records[number][subject]+'\n'
            if is_lesson==False:
                answer += '*·* Урок еще не запланирован\n'
    else:
        for number in users_records:
            is_lesson = False
            for subject in users_records[number]:
                if users_records[number][subject] != None:
                    is_lesson = True
                    answer += subject+' '+users_records[number][subject]+'\n'
            if is_lesson==False:
                answer += 'Урок еще не запланирован\n'

    await bot.send_message(user_id,answer,parse_mode=types.ParseMode.MARKDOWN)
        
        
###############################################
################ START_BOT ####################
###############################################


@dp.message_handler(state=States.CHOISE_FULLNAME,text=["Для себя","Для ребенка"])
async def func(msg: types.Message):
    user_id = str(msg.from_user.id)
    state = dp.current_state(user=msg.from_user.id)
    
    keyboard = types.ReplyKeyboardRemove()
    if msg.text == "Для себя":
        await bot.send_message(user_id, 'Как Вас зовут? Если нет отчества - можно не указывать', reply_markup=keyboard)
        await States.ONE_FULLNAME.set()
    elif msg.text == "Для ребенка":
        await bot.send_message(user_id, 'Как зовут ученика(-цу)? Если нет отчества - можно не указывать', reply_markup=keyboard)
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
    await bot.send_message(user_id, 'А как можно обращаться к Вам?')
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
        await bot.edit_message_text('Выберите часовой пояс.\nНапример, для москвы: МСК+0',
                                    query.from_user.id,
                                    query.message.message_id,
                                    reply_markup=keyboard)
        return
    
    await state.update_data(timezone=int(value[3:]))
    await bot.edit_message_text('Часовой пояс успешно введен', query.from_user.id, query.message.message_id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton('Ввести номер автоматически',request_contact=True))
    await bot.send_message(query.from_user.id, 'Как и всегда номер телефона. (+7 000 000 00 00)\nЕго можно ввести автоматически, нажав на кнопку ниже',reply_markup=keyboard)
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
    await bot.send_message(query.from_user.id, 'Как и всегда номер телефона. (+7 000 000 00 00)\nЕго можно ввести автоматически, нажав на кнопку ниже',reply_markup=keyboard)
    await States.CONTACT.set()

#auto
@dp.message_handler(content_types=['contact'],state=States.CONTACT)
async def handle_location(msg: types.Message):
    state = dp.current_state(user=msg['from']['id'])
    
    data = await state.get_data()
    students_full_name = data['students_full_name']
    parents_full_name = data['parents_full_name']
    if data['timezone'] < 0 : timezone = str(data['timezone'])
    elif data['timezone'] >= 0 : timezone = '+'+str(data['timezone'])
    
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
        "time_zone" : timezone,
        "discounts" : '10 10'
        }
        base_students.insert_one(mydict)
    except: None
            
        
    subjects = list(subject_id.keys())  
    
    await state.update_data(subjects_buttons=subjects)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Нет промокода"]
    keyboard.add(*buttons)
    await bot.send_message(user_id, 'Введите промокод (если есть):',reply_markup=keyboard)
    await States.PROMO_CODE.set()
    
# not auto    
@dp.message_handler(state=States.CONTACT)
async def handle_location(msg: types.Message):
    state = dp.current_state(user=msg['from']['id'])
    user_id = str(msg['from']['id'])
    
    data = await state.get_data()
    students_full_name = data['students_full_name']
    parents_full_name = data['parents_full_name']
    if data['timezone'] < 0 : timezone = str(data['timezone'])
    elif data['timezone'] >= 0 : timezone = '+'+str(data['timezone'])

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
    
    #create number_id
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
        "time_zone" : timezone,
        "discounts" : '10 10'
        }
        base_students.insert_one(mydict)
    except: None
        
    subjects = list(subject_id.keys())  
    
    await state.update_data(subjects_buttons=subjects)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Нет промокода"]
    keyboard.add(*buttons)
    await bot.send_message(user_id, 'Введите промокод (если есть):',reply_markup=keyboard)
    await States.PROMO_CODE.set()
    
    
@dp.message_handler(state=States.PROMO_CODE)
async def handle_location(msg: types.Message):
    state = dp.current_state(user=msg['from']['id'])
    user_id = str(msg['from']['id'])
    
    data = await state.get_data()
    
    subjects_buttons = data['subjects_buttons']
    
    if msg['text'] == 'Нет промокода':
        await state.update_data(promo_code=None)
        keyboard = types.ReplyKeyboardRemove()
        await bot.send_message(user_id, 'Нет промокода',reply_markup=keyboard)

        keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
        for subject in subjects_buttons:
            keyboard.row(types.InlineKeyboardButton(subject, callback_data=callbakes.new(action='subject_choise', value=subject)))
        await bot.send_message(user_id, 'Выберите предмет.\n☝️Внимательно, перевыбрать возможности не будет😄:',reply_markup=keyboard)
        await States.SUBJECT.set()
        return
        
    promo_code = msg['text']
    
    items = promo_codes.find()
    right_promo = False
    for item in items:
        if item['_id'] == promo_code:
            if int(item['value']) == 0:
                await bot.send_message(user_id, 'Данная акция закончилась')
                return
            else:
                right_promo = True
                await state.update_data(promo_code=[item['_id'],item['discounts'],item['value']])
                
                keyboard = types.ReplyKeyboardRemove()
                await bot.send_message(user_id, 'Промокод применен, при первой покупке скидка автоматически применится',reply_markup=keyboard)
                keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
                for subject in subjects_buttons:
                    keyboard.row(types.InlineKeyboardButton(subject, callback_data=callbakes.new(action='subject_choise', value=subject)))
                await bot.send_message(user_id, 'Выберите предмет.\n☝️Внимательно, перевыбрать возможности не будет😄:',reply_markup=keyboard)
                await States.SUBJECT.set()
                
    if right_promo == False:
        await bot.send_message(user_id, 'Проверьте правильность написания')
        return
   
    
@dp.callback_query_handler(callbakes.filter(action='subject_choise'),state=States.SUBJECT)
async def process_callback(query: types.CallbackQuery, callback_data: dict):             
    state = dp.current_state(user=query.from_user.id)
    user_id = str(query.from_user.id)
     
    subject = callback_data['value']
    await state.update_data(subject=subject)
    
    keyboard = types.InlineKeyboardMarkup(resize_keyboard=True)
    for grade in ['5 класс', '6 класс', '7 класс', '8 класс', '9 класс', '10 класс', '11 класс']:
        keyboard.row(types.InlineKeyboardButton(grade, callback_data=callbakes.new(action='grade_choise', value=grade)))
    await bot.edit_message_text('Осталось пара шагов. Укажите класс:', query.from_user.id, query.message.message_id, reply_markup=keyboard)
    await States.GRADE.set()
    

@dp.callback_query_handler(callbakes.filter(action='grade_choise'),state=States.GRADE)
async def process_callback(query: types.CallbackQuery, callback_data: dict):     
    state = dp.current_state(user=query.from_user.id)
    user_id = str(query.from_user.id)
    #get data
    grade = callback_data['value']
    await state.update_data(grade=grade)
    data = await state.get_data()
   
    subject = data['subject']
    number = data['number']
    timezone = int(data['timezone'])
    staff_id = subject_id[subject]['id_main_teacher']
    service_ids = [subject_id[subject]['id_subject']]
    
    # if data['number_test_lessons'].get(number) != None:
    #     other_test_lessons = list(data['number_test_lessons'][number].values())
    # else: other_test_lessons = []
    
    #get work_schedul
    now_date = (datetime.now() + timedelta(hours=timezone+3)).date() + timedelta(days=1) 
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
        time_end_day = work_day['slots'][0]['to']

        hours,minutes = time_start_day.split(':')
        if hours[0] == '0': hours = hours[1:]
        if minutes[0] == '0': minutes = minutes[1:]
        full_time_start_day = date + timedelta(hours=int(hours)+timezone,minutes=int(minutes))

        hours,minutes = time_end_day.split(':')
        if hours[0] == '0': hours = hours[1:]
        if minutes[0] == '0': minutes = minutes[1:]
        full_time_end_day = date + timedelta(hours=int(hours)+timezone,minutes=int(minutes))

        times = []
        for time in times_from_crm:
            times.append(time['time'])
        for count in range(len(times)):
            time = times[count]
            hours,minutes = time.split(':')
            if minutes[0] == '0': minutes = minutes[1:]
            full_time = date + timedelta(hours=int(hours)+timezone,minutes=int(minutes)) 
            times[count] = full_time
        # if is lesson in start and end
        try:
            if times[0] != full_time_start_day: times.insert(0, full_time_start_day)
        except: continue
        try:
            if times[-1] != full_time_end_day: times.insert(len(times), full_time_end_day)
        except: continue

        processed_times = times.copy()
        for count in range(1,len(times)):
            #search simple lessons
            time = times[count]
            if str(time - times[count-1]) != '0:15:00' and str(time - times[count-1]) != '0:30:00': 
                processed_times[count] = None
                processed_times[count-1] = None

        if processed_times[-1] == full_time_end_day: processed_times[-1] = None

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
    await bot.edit_message_text('Осталось подумать над временем тестового урока:', query.from_user.id, query.message.message_id, reply_markup=keyboard)
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
    if query.from_user.username != None:
        username = '@'+str(query.from_user.username) 
    else: username = None
    
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
    promo_code = data['promo_code']
    
        
    students_full_name = data['students_full_name']
    parents_full_name = data['parents_full_name']
    if parents_full_name == None: full_name = students_full_name
    else: full_name =  parents_full_name 
    
    # if data['number_test_lessons'].get(number) != None:
    #     other_test_lessons = list(data['number_test_lessons'][number].values())
    # else: other_test_lessons = []
    
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
    client_id = response['data']['client']['id']

    #edit client
    if parents_full_name == None:
        data = json.dumps({'labels': [categories[grade]], 'comment':f'Ученик: {students_full_name}'})
    else:
        data = json.dumps({'labels': [categories[grade]], 'comment':f'Ученик: {students_full_name}'+f'\nРодитель: {parents_full_name}'})
    uri = f"https://api.yclients.com/api/v1/client/651183/{client_id}"
    headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
    params = {'name': full_name.replace(' ',''), 'phone':number}
    response = json.loads(requests.put(uri, headers=headers, params=params, data=data).text)
    
    
    if promo_code != None:
        if promo_code[1].split(' ')[0].split('/')[1] != '0' or promo_code[1].split(' ')[1].split('/')[1] != '0':
            abonement_id = '23250729'
                
            uri = "https://api.yclients.com/api/v1/storage_operations/operation/651183/"
            headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
            data = json.dumps({
                'type_id' : 1,
                'create_date' : str(datetime.today().day)+'.'+str(datetime.today().month)+'.'+str(datetime.today().year),
                'storage_id': 1298829,
                'master_id' : 1858699,
                'client_id': client_id,
                'goods_transactions' : [{
                    'amount': 1,
                    'client_id': client_id,
                    'cost_per_unit': 10000,
                    'discount' : 100,
                    'cost' : 1000,
                    'master_id' : 1858699,
                    'operation_unit_type': 1,
                    'good_id': abonement_id,
                    'good_special_number': str(random.randint(1000000000,9999999999))}]}
            )
            response = json.loads(requests.post(uri, headers=headers, data=data).text)
        
        base_students.update_one({"_id": number}, 
                                         {"$set": {'one_time_discounts': promo_code[1].split(' ')[0].split('/')[0]+' '+promo_code[1].split(' ')[1].split('/')[0]}})
        promo_codes.update_one({"_id": promo_code[0]}, 
                                         {"$set": {'value': int(promo_code[2])-1}})


    #edit number_test_lessons.txt
#     with open('number_test_lessons.txt','r') as text: 
#         data = text.read()
#         if data == '': number_test_lessons = {}
#         else: number_test_lessons = json.loads(data)
        
#     if number_test_lessons.get(number)!= None:
#         number_test_lessons[number].update({subject:str(time_start_for_crm)})
#     else:
#         number_test_lessons.update({number:{subject:str(time_start_for_crm)}})
    
#     with open('number_test_lessons.txt','w') as data: 
#         data.write(json.dumps(number_test_lessons))
        
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
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Следующий урок", "Купить"]
    buttons_2 = ["Баланс", "Контакты", "Остановить уведомления"]
    keyboard.add(*buttons)
    keyboard.row(*buttons_2)
    
    await bot.edit_message_text('На этом все! Урок запланирован. 🎉\nДалеко этого бота не откладывайте, он Вам еще понадобится.\nЗдесь же Вам придет за 6 часов до начала урока напоминание и ссылка для подключения к уроку',query.from_user.id, query.message.message_id)

    await bot.send_photo(user_id, photo=open('image3.png',"rb"),caption=blanks['welcome'], reply_markup=keyboard)
    
    await state.finish()
    
    
    
    
    
    
    
    
    
    
    
    
@dp.message_handler(text=['newsletter','Newsletter'])
async def newsletter(msg: types.Message):

    user_id = str(msg.from_user.id)
    
    if msg.from_user.username not in access : return 

    state = dp.current_state(user=user_id)
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["/cancel"]
    keyboard.add(*buttons)
    await bot.send_message(msg.from_user.id, 'Пришли сообщение для рассылки. В точно таком же виде оно будет отправлено всем пользователям.', reply_markup=keyboard)
    await States.NEWSLETTER.set()
    


    
@dp.message_handler(state=States.NEWSLETTER,content_types=types.ContentType.ANY)
async def newsletter_2(msg: types.Message):
    state = dp.current_state(user=msg.from_user.id)
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Следующий урок", "Купить"]
    buttons_2 = ["Баланс", "Контакты", "Остановить уведомления"]
    keyboard.add(*buttons)
    keyboard.row(*buttons_2)
    
    if msg.text=='/cancel': 
        await state.finish()
        await msg.reply("Ввод сброшен, можешь расслабиться", reply_markup=keyboard)
        return
    
    
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)

        
        
    ids = []    
    for number in is_in_file:
        user_ids = is_in_file[number]

        for user_id in user_ids:
            ids.append(user_id)
 
    for user_id in ids:
        try:
            time.sleep(0.1)
            if msg.photo:
                await bot.send_photo(user_id, photo=msg.photo[-1].file_id,caption=msg.caption)
            elif msg.video:
                await bot.send_video(user_id, video=msg.video.file_id,caption=msg.caption)
            elif msg.text:
                # await bot.send_message(user_id, msg.text)
                await bot.send_message(user_id, msg.text, reply_markup=keyboard, disable_notification=True)
        except Exception as e:
            print('errore send letters',e, user_id)
    

    await bot.send_message(msg.from_user.id, 'Сообщение было разослано всем ученикам, кто нажал /start', reply_markup=keyboard)
    
    await state.finish()
    
    
    
    
    
    
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
