import pprint
import time
from datetime import datetime, date
import pickle
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import telebot
# from multiprocessing import Process, Value, Queue
import threading
from queue import Queue

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

token = os.getenv('token')
myid = os.getenv('myid')


class SenderBot:
    """
    Получает словарь с событиями, ищет в них события дата которых наступила, отправляет название, описание события в ТГ
    """
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    FILE_PATH = 'pythonnot-c71dbb5a4c15.json'

    def __init__(self, calendar_id, myid):
        self.calendar_id = calendar_id
        credentials = service_account.Credentials.from_service_account_file(
            filename=self.FILE_PATH, scopes=self.SCOPES
        )
        self.service = build('calendar', 'v3', credentials=credentials)
        self.myid = myid
        self.bot = telebot.TeleBot(token)
        self.out_bot = telebot.TeleBot(token)
        self.message = ''
        self.past_birthdays = []  # список с исключениями событьи др, должен обновляться каждый год первого января.
        self.past_weekly = []  # список с исключениями событьи недели, должен обновляться каждый понедельник.

    def get_calendar_list(self):
        return self.service.calendarList().list().execute()

    def add_calendar(self):
        calendar_list_entry = {
            'id': self.calendar_id,
        }
        return self.service.calendarList().insert(
            body=calendar_list_entry).execute()

    def get_events(self):
        return self.service.events().list(calendarId=self.calendar_id).execute()

    def send_event_info(self, events_d):
        events = events_d['items']
        for event in events:
            if event['etag'][1:-1] not in self.past_birthdays and event['etag'][1:-1] not in self.past_weekly:
                self.comparison(event)

    def comparison(self, event):
        date2 = (
            datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute,
            datetime.now().second)
        text = f"{event['summary']} / date: {event['start']} / {event['etag']}"
        if 'recurrence' in event:  # Дни рождения
            if event['recurrence'] == ['RRULE:FREQ=YEARLY']:
                if 'dateTime' in event['start']:
                    date1 = self.changing_datetime_format(event['start']['dateTime'])
                    if (date1.month, date1.day, date1.hour, date1.minute, date1.second) < date2[1:] and event[
                        'etag'] not in self.past_birthdays:
                        self.past_birthdays.append(event['etag'].replace('"', ''))
                        # self.bot.send_message(myid, text)
                        print(text)
                else:
                    date1 = self.changing_datetime_format(event['start']['date'])
                    if (date1.month, date1.day, date1.hour, date1.minute, date1.second) < date2[1:] and event[
                        'etag'] not in self.past_birthdays:
                        self.past_birthdays.append(event['etag'].replace('"', ''))
                        # self.bot.send_message(myid, text)
                        print(text)
            if 'RRULE:FREQ=MONTHLY' in event['recurrence'][0]:
                if 'dateTime' in event['start']:
                    date1 = self.changing_datetime_format(event['start']['dateTime'])
                    if (date1.day, date1.hour, date1.minute, date1.second) < date2[2:] and event[
                        'etag'] not in self.past_birthdays:
                        self.past_birthdays.append(event['etag'].replace('"', ''))
                        # self.bot.send_message(myid, text)
                        print(text)
                else:
                    date1 = self.changing_datetime_format(event['start']['date'])
                    if (date1.day, date1.hour, date1.minute, date1.second) < date2[2:] and event[
                        'etag'] not in self.past_birthdays:
                        self.past_birthdays.append(event['etag'].replace('"', ''))
                        # self.bot.send_message(myid, text)
                        print(text)
            if 'RRULE:FREQ=WEEKLY' in event['recurrence'][0]:
                # BYDAY = MO, WE, FR, TU, TH, SA, SU   Monday Tuesday Wednesday Thursday Friday Saturday Sunday
                days_event = event['recurrence'][0].split('BYDAY=')[-1]
                if datetime.now().strftime('%A')[:2].upper() in days_event:
                    if 'dateTime' in event['start']:
                        date1 = self.changing_datetime_format(event['start']['dateTime'])
                        if (date1.hour, date1.minute, date1.second) < date2[3:] and event[
                            'etag'] not in self.past_birthdays:
                            self.past_weekly.append(event['etag'].replace('"', ''))
                            # self.bot.send_message(myid, text)
                            print(text)
                    else:
                        date1 = self.changing_datetime_format(event['start']['date'])
                        if (date1.hour, date1.minute, date1.second) < date2[3:] and event[
                            'etag'] not in self.past_birthdays:
                            self.past_weekly.append(event['etag'].replace('"', ''))
                            # self.bot.send_message(myid, text)
                            print(text)
        else:
            if 'dateTime' in event['start']:
                date1 = self.changing_datetime_format(event['start']['dateTime'])
                if (date1.year, date1.month, date1.day, date1.hour, date1.minute, date1.second) < date2 and event[
                    'etag'] not in self.past_birthdays:
                    self.past_birthdays.append(event['etag'].replace('"', ''))
                    # self.bot.send_message(myid, text)
                    print(text)


            else:
                date1 = self.changing_datetime_format(event['start']['date'])
                if (date1.year, date1.month, date1.day, date1.hour, date1.minute, date1.second) < date2 and event[
                    'etag'] not in self.past_birthdays:
                    self.past_birthdays.append(event['etag'].replace('"', ''))
                    # self.bot.send_message(myid, text)
                    print(text)

    def changing_datetime_format(self, event_datetime):
        if 'T' not in event_datetime:
            event_datetime += 'T00:00:00+00:00'
            new_event_datetime = str(event_datetime.split('T')[0].replace(':', '-')) + ' ' + str(
                event_datetime.split('T')[1].split('+')[0])
        else:
            new_event_datetime = str(event_datetime.split('T')[0].replace(':', '-')) + ' ' + str(
                event_datetime.split('T')[1].split('+')[0])
        result = datetime.strptime(new_event_datetime, "%Y-%m-%d %H:%M:%S")
        return result

    def zeroing_past_birthdays(self):
        if int(datetime.now().month) == 1 and int(datetime.now().day) == 1 and int(datetime.now().hour) == 1 and int(
                datetime.now().minute) <= 5:
            self.past_birthdays = []

    def zeroing_past_weekly(self):
        if datetime.now().strftime('%A') == 'Monday' and int(datetime.now().hour) == 1 and int(
                datetime.now().minute) <= 5:
            self.past_weekly = []

    def start_bot(self, flag):
        i = 0
        while not flag.is_set():
            i += 1
            time.sleep(240)  # 240 секунд в релизной версии
            print(i)
            self.send_event_info(self.get_events())
            self.zeroing_past_birthdays()
            self.zeroing_past_weekly()

    def telegram_start(self, flag):

        @self.bot.message_handler(commands=['stop'])
        def stop_bot(message):
            flag.set()
            self.bot.send_message(message.chat.id, 'Bot stopped')

        @self.bot.message_handler(commands=['start'])
        def start_bot(message):
            self.bot.send_message(message.chat.id, 'Bot started')

        self.bot.polling(none_stop=True)


if __name__ == '__main__':
    # with open('dict.txt', 'wb') as f:
    #     pickle.dump(loaded_dict, f)
    # with open('dict.txt', 'rb') as f:
    #     loaded_dict = pickle.load(f)
    notification_message = Queue()
    stop_flag = threading.Event()
    sbot = SenderBot(myid=myid, calendar_id='denis.elers23@gmail.com')
    p1 = threading.Thread(target=sbot.telegram_start, args=(stop_flag,))
    p2 = threading.Thread(target=sbot.start_bot, args=(stop_flag, ))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
