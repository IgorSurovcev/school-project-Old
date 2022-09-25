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

from datetime import datetime, timedelta, timezone

password = urllib.parse.quote_plus('7ZfrNV3ifnWf2oor')
client = MongoClient('mongodb+srv://coolpoint:%s@coolpoint-cluster.5g2rs.mongodb.net/?retryWrites=true&w=majority' % (password))

base = client['base_of_peoples']
base_teachers = base['teachers']
base_students = base['students']

blanks = {
    'welcome' : 'Кратко обо мне.\nЗдравствуйте! 😊\nЯ бот-помощник школы CoolPoint.\nЗачем я Вам нужен? 🤔\nКонцепция школы CoolPoint - "Учиться легко!".\nСоответственно, я вношу небольшой, но очень важный вклад в удобства уроков. Коротко говоря, я помощник, который связывает преподавателя с его учениками!)\nЧто я умею? ☝️\nНапоминаю о предстоящих уроках;\nПрисылаю все необходимые ссылки для начала занятия;\nСлежу за остатком уроков на балансе абонемента;\nРассказываю о новостях школы и не только;\nЯ тоже постоянно учусь, а значит список моих функций будет постоянно пополняться. Следите за новостями! 😌',
    'plug' : 'Добрый день!☺️\n\nВы попали на бота-помощника школы A3artSchool. \nЕсли вы читаете это сообщение, значит Вы одни из первых, кто был приглашен в эту систему. \nСейчас идёт этап тестирования, если Вы сталкнетесь с любыми неисправностями или неточностями, обязательно пишите Владиславу (@A3artt). \nСпасибо Вам за участие в тестовом периоде! \n\nЧто я умею? ☝️\n📌Напоминаю о предстоящих уроках;\n📌Присылаю все необходимые ссылки для начала занятия;\n📌Слежу за остатком уроков на балансе абонемента;\n📌Рассказываю о новостях школы и не только;\n\nДо встречи! 😉',
    'not_username_in_base':'Добрый день! Я бот школы A3artSchool. ☺️\nМы вроде ещё не знакомы) \nЕсли у вас уже назначен урок, значит это какая-то ошибка, обязательно напишите Владиславу об этой проблеме. \n\nЕсли же с Вами поделились этим ботом, то у Вас есть секретная возможность записаться на урок со скидкой 10%! 😉\nЧтобы записаться на урок напишите Владиславу: @A3artt\nИли позвоните по номеру: +79080905277'
}



    
API_TOKEN = '5473320366:AAEwnENs-cyjGA5pBJFA-qpeHiU-v4B2_5A'

logging.basicConfig(level=logging.INFO)

class States(StatesGroup):
    NEWSLETTER = State()

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

access = ['VuplesOwl', 'A3artt']




dp.middleware.setup(LoggingMiddleware())


@dp.message_handler(commands='start',state='*')
async def start_handler(msg: types.Message):

    user_id = str(msg.from_user.id)
    username = '@'+str(msg.from_user.username)
    
    print(user_id)
    print(username)
    
#     item_student_username = base_students.find({'username':username})
#     item_student_parents_username = base_students.find({'parents_username':username})
    
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)
    with open('deleted_user_ids.txt','r') as data: 
        text = data.read()
        if text == '': deleted_user_ids = {}
        else: deleted_user_ids = json.loads(text)
        
    # for item in item_student_username:
    #     number = item['_id']
    # for item in item_student_parents_username:
    #     number = item['_id']
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["Следующий урок"]
    buttons_2 = ["Баланс", "Контакты", "Остановить уведомления"]
    keyboard.add(*buttons)
    keyboard.row(*buttons_2)
    
    numbers = []
    for number in is_in_file:
        for user_id_file in is_in_file[number]:
            if user_id == user_id_file: numbers.append(number)
        
    if numbers == [] and deleted_user_ids.get(user_id) == None:
        await bot.send_message(user_id,blanks['not_username_in_base'])
        return
    elif numbers == [] and deleted_user_ids.get(user_id)!=None:
        for deleted_number in deleted_user_ids[user_id]:
            is_in_file[deleted_number].append(user_id)
            deleted_user_ids.update({user_id:[]})

            with open('is_in_file.txt','w') as data: 
                data.write(json.dumps(is_in_file))
            with open('deleted_user_ids.txt','w') as data: 
                data.write(json.dumps(deleted_user_ids))
            
        
        await bot.send_message(user_id,blanks['plug'], reply_markup=keyboard)  
    else: 
        await bot.send_message(user_id,blanks['plug'], reply_markup=keyboard)  
    
    
    #not_username_in_base
    # try: print(number)
    # except:
    #     await bot.send_message(user_id,blanks['not_username_in_base'])
    #     print(number)
        
        
#     try:
#         user_ids = is_in_file[number]
#         is_in_file_flug = True 
#     except: is_in_file_flug = False
    
#     keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     buttons = ["Следующий урок"]
#     buttons_2 = ["Баланс", "Контакты", "Остановить уведомления"]
#     keyboard.add(*buttons)
#     keyboard.row(*buttons_2)
    
#     # is in db but not in the file
#     if is_in_file_flug == False:
#         number_id = {number: [user_id]}
#         is_in_file.update(number_id)
#         with open('is_in_file.txt','w') as data: 
#             data.write(json.dumps(is_in_file))
#         await bot.send_message(user_id,blanks['plug'], reply_markup=keyboard)  
        
#     #is in file
#     elif is_in_file_flug == True:
#         user_ids = set(user_ids)
#         user_ids.add(user_id)
#         user_ids = list(user_ids)
#         number_ids = {number: user_ids}
        
#         is_in_file.update(number_ids)
#         with open('is_in_file.txt','w') as data: 
#             data.write(json.dumps(is_in_file))
#         await bot.send_message(user_id,blanks['plug'], reply_markup=keyboard)  
        


    # await msg.reply(blanks['plug'], reply_markup=keyboard)

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
            # anwser = 'Кажется, у вас не подключено ни одного абонимента.\nОчень советую сделать это!\nВедь так вы получите скидку 10% на все занятия\nДля оформления обратитесь к Владиславу: @A3artt'
            # await bot.send_message(user_id,answer)
        else:
            balences.update({number:{}})
    #         answer = 'Вот список ваших абонементов:\n'
            for balance in response:
                subject = balance['balance_string'].split(',')[0]
                balance_of_subject = str(balance['united_balance_services_count'])
                
                # balences.update({number: {subject:balance_of_subject}})

                balences[number].update({subject:balance_of_subject})

                # answer += subject+': '+balance_of_subject+'\n'
    # #         await bot.send_message(user_id,answer)
    #         print(balences[number][subject])
    # print(balences)
    if len(numbers) == 1:
        answer = 'Вот список ваших абонементов:\n'
        for balance_of_subject in balences[number]:
            answer += balance_of_subject+': '+balences[number][balance_of_subject]+'\n'
    else:
        answer = '*Список абонементов*\n'
        for number in numbers:
            item_student = base_students.find({'_id':number})
            name = ''
            for item in item_student:
                name += item['full_name'].split(' ')[1]
            answer += name+':\n'
            
            if balences[number] != None:
                for balance_of_subject in balences[number]:
                    answer += '· '+balance_of_subject+': '+balences[number][balance_of_subject]+'\n'
            else:
                answer += '  Абонемент не подключен'
    await bot.send_message(user_id,answer,parse_mode='Markdown')
                    

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
        password = urllib.parse.quote_plus('7ZfrNV3ifnWf2oor')
        client = MongoClient('mongodb+srv://coolpoint:%s@coolpoint-cluster.5g2rs.mongodb.net/?retryWrites=true&w=majority' % (password))

        uri = "https://api.yclients.com/api/v1/records/651183"
        headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
        params = {'start_date' :  str(datetime.today().day)+'.'+str(datetime.today().month)+'.'+str(datetime.today().year)}

        records_crm = json.loads(requests.get(uri, params=params, headers=headers).text)['data']

        with open('records_file.txt','r') as text: 
            data = text.read()
            if data == '': records_file = {}
            else: records_file = json.loads(data)

        is_record = False
        for record in reversed(records_crm):
            record_id = str(record['id'])

            if '+'+str(record['client']['phone']) == number:
                if record['attendance'] == 0:
                    is_record = True
                    break

        if records_file.get(record_id) == None:
            users_records.update({number:None})
            # answer = 'Сейчас посмотрел расписание, не нашел запланированных занятий 😶\nЕсли это ошибка, обязательно напиши своему преподавателю!'
            # await bot.send_message(user_id,answer)
            continue

        record_file = records_file[record_id]
        crm_time_start = datetime.fromisoformat(record_file['crm_time_start'])
        students_time_zone = record_file['students_time_zone']
        # crm_timezone = int(record_file['crm_timezone'])

        students_time_start = crm_time_start + timedelta(hours=int(students_time_zone))

        now = datetime.now() + timedelta(hours=int(students_time_zone))

        print(students_time_start,now)

        if students_time_start < now or record_file['is_deleted'] or is_record == False:
            users_records.update({number:None})
            # answer = 'Сейчас посмотрел расписание, не нашел запланированных занятий 😶\nЕсли это ошибка, обязательно напиши своему преподавателю!'
            # await bot.send_message(user_id,answer)
            continue

        if len(str(students_time_start.minute)) == 1:
            minute = '0'+str(students_time_start.minute)
        else: minute = str(students_time_start.minute)

        beautiful_time = str(students_time_start.hour)+':'+minute

        date = str(students_time_start.day) + '.' + str(students_time_start.month)

        if len(str(students_time_start.month)) == 1:
            month = '0'+str(students_time_start.month)
        else: month = str(students_time_start.month)

        date = str(students_time_start.day) + '.' + month

        #send messege
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

        answer = 'Следующий урок по расписанию '
        if recent==False:
            answer += weekday + ', ' + date + ' в ' + beautiful_time 
        else:
            answer += recent + ' в ' + beautiful_time
            
        users_records.update({number:answer})
        # await bot.send_message(user_id,answer)
    answer = ''
    if len(numbers) != 1:
        for number in users_records:
            item_student = base_students.find({'_id':number})
            name = ''
            for item in item_student:
                name += item['full_name'].split(' ')[1]
            answer += name+':\n'
            
            if users_records[number] != None:
                answer += '· '+users_records[number]+'\n'
            else:
                answer += '· Урок еще не запланирован\n'
    else:
        for number in users_records:
            answer = users_records[number]
    await bot.send_message(user_id,answer,parse_mode='Markdown')
        
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
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
    buttons = ["Следующий урок"]
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
        time.sleep(0.1)
        if msg.photo:
            await bot.send_photo(user_id, photo=msg.photo[-1].file_id,caption=msg.caption)
        elif msg.video:
            await bot.send_video(user_id, video=msg.video.file_id,caption=msg.caption)
        elif msg.text:
            await bot.send_message(user_id, msg.text)
    

    await bot.send_message(msg.from_user.id, 'Сообщение было разослано всем ученикам, кто нажал /start', reply_markup=keyboard)
    
    await state.finish()
    
    
    
    
    
    
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
