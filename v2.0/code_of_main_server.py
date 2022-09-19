from pymongo import MongoClient
import urllib.parse
import requests
import json
import numpy as np
from google.oauth2.credentials import Credentials
from gcsa.google_calendar import GoogleCalendar
from gcsa.recurrence import Recurrence, DAILY, SU, SA
from datetime import datetime, timedelta, timezone
from gcsa.conference import ConferenceSolutionCreateRequest, SolutionType
from gcsa.reminders import EmailReminder, PopupReminder
import random
import sys
import time
from google.auth.transport.requests import Request
import pytz
import traceback



from gcsa.event import Event
from beautiful_date import *

def do_log(text):
    with open('log.txt','r') as file: 
        log = file.read()
    with open('log.txt','w') as file: 
        file.write(log+'\n'+str(datetime.now())+' '+str(text)) 


password = urllib.parse.quote_plus('7ZfrNV3ifnWf2oor')
client = MongoClient('mongodb+srv://coolpoint:%s@coolpoint-cluster.5g2rs.mongodb.net/?retryWrites=true&w=majority' % (password))
base = client['base_of_peoples']
base_teachers = base['teachers']
base_students = base['students']


while True:
    try:
        uri = "https://api.yclients.com/api/v1/records/651183"
        headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
        params = {'start_date' :  str(datetime.today().day)+'.'+str(datetime.today().month)+'.'+str(datetime.today().year)}


        records_crm = json.loads(requests.get(uri, params=params, headers=headers).text)['data']
        with open('records_file.txt','r') as text: 
            data = text.read()
            if data == '': records_file = {}
            else: records_file = json.loads(data)

        for record in records_crm:
            record_id = str(record['id'])
            if records_file.get(record_id) == None:
                if record['client'] == None: continue
                number = '+'+str(record['client']['phone'])
                crm_time_start = datetime.fromisoformat(record['date'])
                print(record_id,crm_time_start,record['date'])
                do_log(str(record_id)+' '+str(crm_time_start)+' '+number)
                seance_length = record['seance_length']
                full_teachers_name = record['staff']['name']
                notification_name = record['client']['name']
                student_id = str(record['client']['id'])
                if record['services']==None: continue
                subject = record['services'][0]['title']
                is_deleted = record['deleted']
                
                crm_timezone = 0 # НЕ ЗАБЫТЬ УБРАТЬ
                
                if record['record_labels'] == []:
                    location = 'Онлайн'
                else:
                    location = record['record_labels'][0]['title']
                    ### ВРЕМЕННО
                # try: 
                #     full_teachers_name = record['record_labels'][1]['title']
                # except: None

                uri = "https://api.yclients.com/api/v1/client/651183/"+student_id
                headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
                response = json.loads(requests.get(uri, headers=headers).text)

                grade = response['data']['categories'][0]['title']

                uri = 'https://api.yclients.com/api/v1/loyalty/abonements/'
                headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
                params = {'company_id' : '651183','phone' : number}
                response = json.loads(requests.get(uri, params=params,headers=headers).text)['data']

                if response == []:
                    is_balance = False
                    balance = None
                else:
                    is_balance = True 
                    for one_balance in response:
                        if one_balance['balance_string'].split(',')[0] == subject:
                            balance = one_balance['united_balance_services_count']   

                item_student = base_students.find({'_id':number})
                
                item_teacher = base_teachers.find({'_id':full_teachers_name})
                is_student = False
                for item in item_student:
                    is_student = True
                    students_name = item['full_name'].split(' ')[1]
                    students_time_zone = item['time_zone']
                
                is_teacher = False
                for item in item_teacher:
                    is_teacher = True
                    token = json.loads(item['token'])
                    teachers_time_zone = int(item['time_zone'])

                if is_student == False: 
                    do_log(str(record_id)+' '+'not_such_student_in_db')
                    print('not_such_student_in_db')
                    students_name = "ERRORE not_such_student_in_db".split(' ')[1]
                    students_time_zone = +2
                
                if is_teacher == False: 
                    do_log(str(record_id)+' '+'not_such_teacher_in_db')
                    print('not_such_teacher_in_db')
                    continue
                
                teachers_time_start = crm_time_start + timedelta(hours=int(teachers_time_zone))
                teachers_time_end = teachers_time_start + timedelta(seconds = seance_length)

                students_time_start = crm_time_start + timedelta(hours=int(students_time_zone))
                students_time_end = students_time_start + timedelta(seconds = seance_length)

                students_time_first_notice = students_time_start - timedelta(hours=6)
                students_time_second_notice = students_time_start + timedelta(seconds = seance_length)

                credentials = Credentials(
                    token=token['token'],
                    refresh_token=token['refresh_token'],
                    client_id=token['client_id'],
                    client_secret=token['client_secret'],
                    scopes=token['scopes'],
                    token_uri=token['token_uri'],
                    expiry=token['expiry']
                )
                # print((datetime.now().date() - datetime.strptime(credentials.expiry, '%Y-%m-%dT%H:%M:%S.%fZ').date()).days)
                
                credentials.refresh(Request())
                base_teachers.update_one({"_id": full_teachers_name}, 
                                                 {"$set": {'token': credentials.to_json()}})

                gc = GoogleCalendar(credentials=credentials)
                
                if location == 'Онлайн':
                    conference_solution=ConferenceSolutionCreateRequest(solution_type=SolutionType.HANGOUTS_MEET)
                elif location == 'Очное':
                    conference_solution=None

                event = Event(summary=students_name+' || '+grade+' || '+subject,
                            start=teachers_time_start,
                            end=teachers_time_end,
                            timezone = 'Etc/GMT{}'.format(-3-teachers_time_zone),
                            reminders=PopupReminder(minutes_before_start=25),
                            conference_solution=conference_solution,
                            color_id=7,
                            event_id = random.randint(10000000,19999999),
                            description = location)

                gc.add_event(event)
                event_id = event.event_id

                event = gc.get_event(event_id)
                if location == 'Онлайн':
                    conference_id = event.conference_solution.conference_id
                elif location == 'Очное': conference_id = None

                with open('is_in_file.txt','r') as data: 
                    is_in_file = json.loads(data.read())

                try:
                    user_id = is_in_file[number]
                    print('is_real_user')
                except:
                    user_id = ['676352317']

                data = {
                    'crm_time_start' : crm_time_start.isoformat(),
                    'creation_date' : datetime.now().date().isoformat(),
                    'teachers_time_zone': teachers_time_zone,
                    'students_time_zone': students_time_zone,
                    'full_teachers_name': full_teachers_name,
                    'students_name' : students_name,
                    'seance_length' : seance_length,
                    'is_deleted' : is_deleted,
                    'is_balance' : is_balance,
                    'balance' : balance,
                    'number' : number,
                    'subject' : subject,
                    'notification_name' : notification_name,
                    'event_id' : event_id,
                    'token':token,
                    'meeting_link' : 'https://meet.google.com/'+str(conference_id),
                    'location':location,
                    'user_id':user_id
                }

                records_file.update({record_id:data}) 

                with open('records_file.txt','w') as file: 
                    file.write(json.dumps(records_file))
            else:
                record_file = records_file[record_id]
                if record_file['is_deleted']: continue
                file_time_start = datetime.fromisoformat(record_file['crm_time_start'])
                file_seance_length = record_file['seance_length']
                file_is_deleted = record_file['is_deleted']
                event_id = record_file['event_id']
                # token = record_file['token']
                file_is_balance = record_file['is_balance']
                file_balance = record_file['balance']
                number = record_file['number']
                notification_name = record_file['notification_name']
                full_teachers_name = record_file['full_teachers_name']
                user_ids = record_file['user_id']
                subject = record_file['subject']
                
                #BALANCE
                uri = 'https://api.yclients.com/api/v1/loyalty/abonements/'
                headers = {"Accept" : "application/vnd.yclients.v2+json","Content-Type" : "application/json","Authorization" : "Bearer uw2xhhghwja3kbkmadh4, User f774e3eb777a5244ccbe927cf8c6047f"}
                params = {'company_id' : '651183','phone' : number}
                response = json.loads(requests.get(uri, params=params,headers=headers).text)['data']

                if response == []:
                    crm_is_balance = False
                    crm_balance = None
                else:
                    crm_is_balance = True 
                    for one_balance in response:
                        if one_balance['balance_string'].split(',')[0] == subject:
                            crm_balance = one_balance['united_balance_services_count']
                #USER_ID
                with open('is_in_file.txt','r') as data: 
                    is_in_file = json.loads(data.read())
                try:
                    new_user_id = is_in_file[number]
                except:
                    new_user_id = ['676352317']
                changed_user_id = set(new_user_id) != set(user_ids)
                
                if changed_user_id:
                    print('CHENGED USER_ID: ', record_id)
                    do_log('CHENGED USER_ID: '+str(record_id)+' '+number+' '+str(user_ids)+' '+str(new_user_id))
                    record_file['user_id'] = new_user_id
                    records_file.update({record_id:record_file}) 

                    with open('records_file.txt','w') as file: 
                        file.write(json.dumps(records_file))



                crm_time_start = datetime.fromisoformat(record['date'])
                crm_seance_length = record['seance_length']
                crm_is_deleted = record['deleted']

                teachers_time_zone = record_file['teachers_time_zone']
                students_time_zone = record_file['students_time_zone']
                # crm_timezone = record_file['crm_timezone']

                changed_start_time = crm_time_start != file_time_start
                changed_seance_length = crm_seance_length != file_seance_length
                changed_is_balance = file_is_balance != crm_is_balance
                changed_balance = file_balance != crm_balance
                


                if changed_start_time or changed_seance_length:
                    print('CHENGED TIME: ', record_id)
                    do_log('CHENGED TIME: '+str(record_id)+' '+str(file_time_start)+' '+str(crm_time_start))
                    teachers_time_start = crm_time_start + timedelta(hours=int(teachers_time_zone))
                    teachers_time_end = teachers_time_start + timedelta(seconds = crm_seance_length)

                    students_time_start = crm_time_start + timedelta(hours=int(students_time_zone))
                    students_time_end = students_time_start + timedelta(seconds = crm_seance_length)

                    # print(record_id,' ', crm_time_start, ' ', file_time_start)
                    item_teacher = base_teachers.find({'_id':full_teachers_name})
                    
                    for item in item_teacher:
                        token = json.loads(item['token'])
                        teachers_time_zone = int(item['time_zone'])
                    
                    credentials = Credentials(
                        token=token['token'],
                        refresh_token=token['refresh_token'],
                        client_id=token['client_id'],
                        client_secret=token['client_secret'],
                        scopes=token['scopes'],
                        token_uri=token['token_uri'],
                        expiry=token['expiry']
                        
                    )
                    credentials.refresh(Request())
#                     
                    base_teachers.update_one({"_id": full_teachers_name}, 
                                                     {"$set": {'token': credentials.to_json()}})
                    
                    
                    gc = GoogleCalendar(credentials=credentials)

                    event = gc.get_event(event_id)
                    event.start = teachers_time_start
                    event.end = teachers_time_end
                    try:
                        gc.update_event(event)
                    except: None
                        

                    record_file['crm_time_start'] = crm_time_start.isoformat()
                    record_file['seance_length'] = crm_seance_length

                    records_file.update({record_id:record_file}) 

                    with open('records_file.txt','w') as file: 
                        file.write(json.dumps(records_file))

                if changed_is_balance or changed_balance:
                    record_file['is_balance'] = crm_is_balance
                    record_file['balance'] = crm_balance
                    
                    print('CHENGED BALANCE: ', record_id)
                    do_log('CHENGED BALANCE: '+str(record_id))
                    
                    records_file.update({record_id:record_file}) 

                    with open('records_file.txt','w') as file: 
                        file.write(json.dumps(records_file))


        record_ids = []
        for record in records_crm:
            record_ids.append(str(record['id']))

        ids_missing_records = []
        for file_record_id in records_file:
            if file_record_id not in record_ids:
                ids_missing_records.append(file_record_id)
                
        for id_missing_record in ids_missing_records:
            file_record = records_file[id_missing_record]
            if file_record['is_deleted']: continue

            crm_time_start = datetime.fromisoformat(file_record['crm_time_start'])
            if crm_time_start.date() < datetime.now().date():
                print('YESTERDAY: ',id_missing_record)
                do_log('YESTERDAY: '+str(id_missing_record))
                
                records_file.pop(id_missing_record) 
                with open('records_file.txt','w') as file: 
                    file.write(json.dumps(records_file))
                    continue
            else:
                token = file_record['token']
                event_id =file_record['event_id']
                print('DELETED: ',id_missing_record)
                full_teachers_name = file_record['full_teachers_name']
                
                do_log('DELETED: '+str(id_missing_record))
                
                item_teacher = base_teachers.find({'_id':file_record['full_teachers_name']})

                for item in item_teacher:
                    token = json.loads(item['token'])
                    teachers_time_zone = int(item['time_zone'])
                
                credentials = Credentials(
                    token=token['token'],
                    refresh_token=token['refresh_token'],
                    client_id=token['client_id'],
                    client_secret=token['client_secret'],
                    scopes=token['scopes'],
                    token_uri=token['token_uri'],
                    expiry=token['expiry']
                )
                credentials.refresh(Request())
                base_teachers.update_one({"_id": file_record['full_teachers_name']}, 
                                                 {"$set": {'token': credentials.to_json()}})
        
                gc = GoogleCalendar(credentials=credentials)

                event = gc.get_event(event_id)
                event.summary = '(ОТМЕНЕН) '+event.summary
                event.color_id = 8
                try:
                    gc.update_event(event)
                except: None

                file_record['is_deleted'] = True

                records_file.update({id_missing_record:file_record}) 
                with open('records_file.txt','w') as file: 
                    file.write(json.dumps(records_file))    


        # print('cycle_end')
        time.sleep(60)
    except Exception as e:
         do_log('ERRORE: '+traceback.format_exc())