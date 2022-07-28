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

bot_token = '5473320366:AAEwnENs-cyjGA5pBJFA-qpeHiU-v4B2_5A'

def send_first_notice(user_id,bot_message):
    url = "https://api.telegram.org/bot"+bot_token+"/sendphoto"
    data = {
        "chat_id": user_id,
        'caption' : bot_message,
        'parse_mode':'Markdown'}
    with open('image.png', "rb") as image_file:
        requests.post(url,data=data,files={"photo": image_file})
        
    data = {
        "chat_id": str(676352317),
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
    
    data = {
        "chat_id": str(676352317),
        'text' : bot_message,
        'parse_mode':'Markdown'}
    requests.post(url,data=data)



blanks = {
    'notice_1' : '*Уведомление*\n{}, добрый день! 😊\nСегодня в {} запланировано занятие по предмету {}.\nСсылка для подключения:\n{}',
    'notice_1_with_ending_balance' : '*Уведомление*\n{}, добрый день! 😊\nСегодня в {} запланировано занятие по предмету {}.\nСсылка для подключения:\n{}\n-------------------------------------------------\nНа балансе абонемента осталось: {} занятие(-я). Продлить можно по ссылке (либо привычным для Вас образом): https://www.tinkoff.ru/rm/surovtsev.vladislav1/KQZTy69201/',
    'notice_2' : '*Урок окончен!*\nОстаток занятий по абонементу: {}'
    
}
    
API_TOKEN = '5504384147:AAFRfM4v1cxShj30PIdqFrgZM_0aAHhSY2c'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


while True:
    
    with open('records_file.txt','r') as data: 
        text = data.read()
        if text == '': records_file = {}
        else: records_file = json.loads(text)

    for record_id in records_file:
        record = records_file[record_id]

        if record['is_deleted']: continue

        crm_time_start = datetime.fromisoformat(record['crm_time_start'])
        students_time_zone = record['students_time_zone']
        seance_length = int(record['seance_length'])
        is_deleted = record['is_deleted']
        is_balance = record['is_balance']
        if record['balance'] != None: balance = int(record['balance'])
        subject = record['subject']
        notification_name = record['notification_name']
        meeting_link=record['meeting_link']
        crm_time_zone = -2 # НЕ ЗАБЫТЬ УБРАТЬ

        user_id = record['user_id']
        

        # now = datetime.now() + timedelta(hours=int(students_time_zone)+crm_time_zone)
        
        now = datetime.now() + timedelta(hours=int(students_time_zone))
        # now = datetime.now(pytz.timezone('Europe/Moscow')) + timedelta(hours=int(students_time_zone))

        students_time_start = crm_time_start + timedelta(hours=int(students_time_zone)+crm_time_zone)
        time_first_notice = students_time_start - timedelta(hours=6)
        # students_time_start = crm_time_start + timedelta(hours=int(students_time_zone))
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

        if days == 0: print("FIRST ",seconds, record_id, is_balance, balance)
        
        if len(str(students_time_start.minute)) == 1:
            minute = '0'+str(students_time_start.minute)
        else: minute = str(students_time_start.minute)

        beautiful_time = str(students_time_start.hour)+':'+minute
        
        if days == 0 and 30 >= seconds > -30:
        # if days == 0:

            if is_balance:
                if amount == 1 and balance == 1:
                    send_first_notice(user_id,blanks['notice_1_with_ending_balance'].format(notification_name,beautiful_time,subject,meeting_link, balance))
                elif amount == 2 and balance == 2:
                    send_first_notice(user_id,blanks['notice_1_with_ending_balance'].format(notification_name,beautiful_time,subject,meeting_link, balance))
                else:
                    send_first_notice(user_id,blanks['notice_1'].format(notification_name,beautiful_time,subject,meeting_link))
            else:
                send_first_notice(user_id,blanks['notice_1'].format(notification_name,beautiful_time,subject,meeting_link))
                


        #SECOND
        if is_balance:
            if time_second_notice > now:
                delta = time_second_notice - now
                seconds =  delta.seconds
                microseconds = delta.microseconds
            else: 
                delta = now - time_second_notice 
                seconds =  -(delta.seconds)
                microseconds = -(delta.microseconds)

            for i in range(len(str(microseconds))): microseconds *= 0.1
            seconds += microseconds
            
            if days == 0: print("SECOND ",seconds, record_id, is_balance, balance)

            if days == 0 and 30 >= seconds > -30:
            # if days == 0:

                send_second_notice(user_id,blanks['notice_2'].format(balance))
    
    
    time.sleep(60)

