import logging
from pymongo import MongoClient
import urllib.parse
import requests
import json
import numpy as np
from datetime import datetime, timedelta, timezone
import random
import sys
import time
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.helper import Helper, HelperMode, ListItem
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import asyncio
import json
import pytz
import traceback

def do_log(text):
    with open('log.txt','r') as file: 
        log = file.read()
    with open('log.txt','w') as file: 
        file.write(log+'\n'+str(datetime.now())+' '+str(text)) 
        
        
def do_linkpay(record_id):
    uri = f'https://api.yclients.com/api/v1/record/651183/{record_id}'
    headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
    params = {'short_link_token':1}
    short_link_token = json.loads(requests.get(uri, params=params,headers=headers).text)['data']['short_link_token']
    link = f'https://yclients.com/pay/{short_link_token}/'
    return link


bot_token = '5473320366:AAEwnENs-cyjGA5pBJFA-qpeHiU-v4B2_5A'

def send_first_notice(user_id,bot_message):
    url = "https://api.telegram.org/bot"+bot_token+"/sendphoto"
    data = {
        "chat_id": user_id,
        'caption' : bot_message,
        'parse_mode':'Markdown'}
    with open('image.png', "rb") as image_file:
        requests.post(url,data=data,files={"photo": image_file})
        
    if user_id == str(676352317): bot_message = 'Сервер не нашел ученика'
    data = {
        "chat_id": str(676352317),
        'caption' : bot_message,
        'parse_mode':'Markdown'}
    with open('image.png', "rb") as image_file:
        requests.post(url,data=data,files={"photo": image_file})
        
    data = {
        "chat_id": str(1226474188),
        'caption' : bot_message,
        'parse_mode':'Markdown'}
    with open('image.png', "rb") as image_file:
        requests.post(url,data=data,files={"photo": image_file})      
    
        

def send_second_notice(user_id,bot_message):
    url = "https://api.telegram.org/bot"+bot_token+"/sendMessage"
    data = {
        "chat_id": user_id,
        'text' : bot_message,
        'parse_mode':'Markdown'}
    requests.post(url,data=data)
    
    if user_id == str(676352317): bot_message = 'Сервер не нашел ученика'
    data = {
        "chat_id": str(676352317),
        'text' : bot_message,
        'parse_mode':'Markdown'}
    requests.post(url,data=data)
    
    data = {
        "chat_id": str(1226474188),
        'text' : bot_message,
        'parse_mode':'Markdown'}
    requests.post(url,data=data)



blanks = {
    'notice_1' : '*Уведомление*\nДобрый день! 😊\nСегодня в {} запланировано занятие по предмету {}.\nСсылка для подключения:\n{}',
    
    'notice_1_with_ending_balance' : '*Уведомление*\nДобрый день! 😊\nСегодня в {} запланировано занятие по предмету {}.\nСсылка для подключения:\n{}\n-------------------\nНа балансе абонемента осталось: {} занятие(-я). Не забудьте продлить абонемент',
    'notice_1_internally' : '*Уведомление*\nДобрый день! 😊\nСегодня в {} запланировано занятие по предмету {}.',
    
    'notice_1_with_ending_balance_internally' : '*Уведомление*\nДобрый день! 😊\nСегодня в {} запланировано занятие по предмету {}.\n-------------------\nНа балансе абонемента осталось: {} занятие(-я). Не забудьте продлить абонемент',
    
    'notice_2' : '*Урок окончен!*\nОстаток занятий по абонементу {}: {}',
    
    'notice_1_parents' : '*Уведомление*\nДобрый день! 😊\nСегодня у ученика ({}) в {} запланировано занятие по предмету {}.\nСсылка для подключения:\n{}',
    
    'notice_1_with_ending_balance_parents' : '*Уведомление*\nДобрый день! 😊\nСегодня у ученика ({}) в {} запланировано занятие по предмету {}.\nСсылка для подключения:\n{}\n-------------------\nНа балансе абонемента осталось: {} занятие(-я). Не забудьте продлить абонемент',
    
    'notice_1_internally_parents' : '*Уведомление*\nДобрый день! 😊\nСегодня у ученика ({}) в {} запланировано занятие по предмету {}.',
    
    'notice_1_with_ending_balance_internally_parents' : '*Уведомление*\nДобрый день! 😊\nСегодня у ученика ({}) в {} запланировано занятие по предмету {}.\n-------------------\nНа балансе абонемента осталось: {} занятие(-я). Не забудьте продлить абонемент',
    
    'notice_2_parents' : '*Урок окончен!*\nОстаток занятий у ученика ({}) по абонементу {}: {}',
    
    'notice_1_not_balance' : '*Уведомление*\nДобрый день! 😊\nСегодня в {} запланировано занятие по предмету {}.\nСсылка для подключения:\n{}\n-------------------\nУрок все еще не оплачен. Оплатите по ссылке: {}\nЛибо приобретите абонемент (рекомендуется)',
    
    'notice_1_internally_not_balance' : '*Уведомление*\nДобрый день! 😊\nСегодня в {} запланировано занятие по предмету {}.\n-------------------\nУрок все еще не оплачен. Оплатите по ссылке: {}\nЛибо приобретите абонемент (рекомендуется)',
    
    'notice_1_not_balance_parents' : '*Уведомление*\nДобрый день! 😊\nСегодня у ученика ({}) в {} запланировано занятие по предмету {}.\nСсылка для подключения:\n{}\n-------------------\nУрок все еще не оплачен. Оплатите по ссылке: {}\nЛибо приобретите абонемент (рекомендуется)',
    
    'notice_1_internally_not_balance_parents' : '*Уведомление*\nДобрый день! 😊\nСегодня у ученика ({}) в {} запланировано занятие по предмету {}.\n-------------------\nУрок все еще не оплачен. Оплатите по ссылке: {}\nЛибо приобретите абонемент (рекомендуется)'
}
    
API_TOKEN = '5504384147:AAFRfM4v1cxShj30PIdqFrgZM_0aAHhSY2c'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


while True:
    time_start = time.process_time() 
    with open('records_file.txt','r') as data: 
        text = data.read()
        if text == '': records_file = {}
        else: records_file = json.loads(text)
    with open('is_in_file.txt','r') as data: 
        text = data.read()
        if text == '': is_in_file = {}
        else: is_in_file = json.loads(text)
        
    now_for_server = datetime.now()
    
    for record_id in records_file:
        time_start_2 = time.process_time() 
        
        record = records_file[record_id]

        if record['is_deleted']: continue

        crm_time_start = datetime.fromisoformat(record['crm_time_start'])
        students_time_zone = record['students_time_zone']
        seance_length = int(record['seance_length'])
        is_balance = record['is_balance']
        subject = record['subject']
        balance = record['balance']
        try: students_name = record['students_name']
        except: students_name = None
        users_number = record['number']
        if balance != None:             
            balance = int(balance)
        
        # print(is_balance,balance)
        
        meeting_link=record['meeting_link']
        # crm_time_zone = -2 # НЕ ЗАБЫТЬ УБРАТЬ
        location = record['location']

        # user_ids = record['user_id']

        try:
            user_ids = is_in_file[users_number]
        except:
            print('not in file '+str(users_number))
            user_ids = ['676352317']
        
        ids_numbers = {}
        for user_id in user_ids:
            ids_numbers.update({user_id:[]})
            for number in is_in_file:
                for user_id_file in is_in_file[number]:
                    if user_id == user_id_file and number != users_number: ids_numbers[user_id].append(number)
        
        now = now_for_server + timedelta(hours=int(students_time_zone))
        
        students_time_start = crm_time_start + timedelta(hours=int(students_time_zone))
        time_first_notice = students_time_start - timedelta(hours=6)
        time_second_notice = students_time_start + timedelta(seconds = seance_length)

        if seance_length / 3600 == 1.0: amount = 1
        elif seance_length / 3600 == 2.0: amount = 2

        #FIRST
        if time_first_notice > now:
            delta = time_first_notice - now
            seconds =  delta.seconds
            microseconds = delta.microseconds
        else: 
            delta = now - time_first_notice 
            seconds =  -(delta.seconds)
            microseconds = -(delta.microseconds)
        
        days = delta.days

        for i in range(len(str(microseconds))): microseconds *= 0.1
        seconds += microseconds
        
        if len(str(students_time_start.minute)) == 1:
            minute = '0'+str(students_time_start.minute)
        else: minute = str(students_time_start.minute)

        beautiful_time = str(students_time_start.hour)+':'+minute
        
        if days == 0 and 30 >= seconds > -30:
        # if record_id == '525154181':
            for user_id in user_ids:
                if len(ids_numbers[user_id]) == 0:
                    try:
                        print("FIRST ",seconds, record_id, is_balance, balance, beautiful_time)
                        if location == 'Онлайн':
                            if amount == 1 and balance == 1:
                                send_first_notice(user_id,blanks['notice_1_with_ending_balance'].format(beautiful_time,subject,meeting_link, balance))
                            elif amount == 2 and balance == 2:                        
                                send_first_notice(user_id,blanks['notice_1_with_ending_balance'].format(beautiful_time,subject,meeting_link, balance))
                            elif balance == None and subject.find('тестовый урок')==-1:
                                pay_link = do_linkpay(record_id)
                                send_first_notice(user_id,blanks['notice_1_not_balance'].format(beautiful_time,subject,meeting_link, pay_link))
                            else:                    
                                send_first_notice(user_id,blanks['notice_1'].format(beautiful_time,subject,meeting_link))
                        elif location == 'Очное':
                            if amount == 1 and balance == 1:                        
                                send_first_notice(user_id,blanks['notice_1_with_ending_balance_internally'].format(beautiful_time,subject, balance))
                            elif amount == 2 and balance == 2:                        
                                send_first_notice(user_id,blanks['notice_1_with_ending_balance_internally'].format(beautiful_time,subject, balance))
                            elif balance == None and subject.find('тестовый урок')==-1:
                                pay_link = do_linkpay(record_id)
                                send_first_notice(user_id,blanks['notice_1_internally_not_balance'].format(beautiful_time,subject, pay_link))
                            else:                    
                                send_first_notice(user_id,blanks['notice_1_internally'].format(beautiful_time,subject))
                    except Exception as e:
                         do_log('ERRORE: '+traceback.format_exc())
                else:
                    try:
                        print("FIRST ",seconds, record_id, is_balance, balance, beautiful_time)
                        if location == 'Онлайн':
                            if amount == 1 and balance == 1:
                                send_first_notice(user_id,blanks['notice_1_with_ending_balance_parents'].format(students_name,beautiful_time,subject,meeting_link, balance))
                            elif amount == 2 and balance == 2:                        
                                send_first_notice(user_id,blanks['notice_1_with_ending_balance_parents'].format(students_name,beautiful_time,subject,meeting_link, balance))
                            elif balance == None and subject.find('тестовый урок')==-1:
                                pay_link = do_linkpay(record_id)
                                send_first_notice(user_id,blanks['notice_1_not_balance_parents'].format(students_name,beautiful_time,subject,meeting_link, pay_link))
                            else:                       
                                send_first_notice(user_id,blanks['notice_1_parents'].format(students_name,beautiful_time,subject,meeting_link))
                        elif location == 'Очное':
                            if amount == 1 and balance == 1:                        
                                send_first_notice(user_id,blanks['notice_1_with_ending_balance_internally_parents'].format(students_name,beautiful_time,subject, balance))
                            elif amount == 2 and balance == 2:                        
                                send_first_notice(user_id,blanks['notice_1_with_ending_balance_internally_parents'].format(students_name,beautiful_time,subject, balance))
                            elif balance == None and subject.find('тестовый урок')==-1:
                                pay_link = do_linkpay(record_id)
                                send_first_notice(user_id,blanks['notice_1_internally_not_balance_parents'].format(students_name,beautiful_time,subject, pay_link))
                            else:                        
                                send_first_notice(user_id,blanks['notice_1_internally_parents'].format(students_name,beautiful_time,subject))
                    except Exception as e:
                         do_log('ERRORE NOTICE: '+traceback.format_exc())

        #SECOND
        if balance != None:
            if time_second_notice > now:
                delta = time_second_notice - now
                seconds =  delta.seconds
                microseconds = delta.microseconds
            else: 
                delta = now - time_second_notice 
                seconds =  -(delta.seconds)
                microseconds = -(delta.microseconds)
            
            days = delta.days

            for i in range(len(str(microseconds))): microseconds *= 0.1
            seconds += microseconds
            
            # if days == 0: print("SECOND ",seconds, record_id, is_balance, balance)

            if days == 0 and 30 >= seconds > -30:
            # if days == 0:
                for user_id in user_ids:
                    if len(ids_numbers[user_id]) == 0:
                        try:
                            print("SECOND ",seconds, record_id, is_balance, balance, beautiful_time)
                            send_second_notice(user_id,blanks['notice_2'].format(subject,balance))
                        except Exception as e:
                             do_log('ERRORE: '+traceback.format_exc())
                    else:
                        try:
                            print("SECOND ",seconds, record_id, is_balance, balance, beautiful_time)
                            send_second_notice(user_id,blanks['notice_2_parents'].format(students_name,subject,balance))
                        except Exception as e:
                             do_log('ERRORE: '+traceback.format_exc())   
                        
        # print("One time:",time.process_time()-time_start_2) 
    
    # print("All time:",time.process_time()-time_start) 
    time.sleep(60)

