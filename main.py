import pprint
import time
from datetime import datetime, date
import pickle
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
import telebot
from multiprocessing import Process, Value, Queue

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

token = os.getenv('token')
myid = os.getenv('myid')


class GoogleCalendar:
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    FILE_PATH = 'pythonnot-c71dbb5a4c15.json'

    def __init__(self, calendar_id):
        self.calendar_id = calendar_id
        credentials = service_account.Credentials.from_service_account_file(
            filename=self.FILE_PATH, scopes=self.SCOPES
        )
        self.service = build('calendar', 'v3', credentials=credentials)

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


class SenderBot:
    """
    Получает словарь с событиями, ищет в них события дата которых наступила, отправляет название, описание события в ТГ
    """

    def __init__(self, myid):
        self.myid = myid
        self.out_bot = telebot.TeleBot(token)
        self.past_birthdays = []  # список с исключениями событьи др, должен обновляться каждый год первого января.
        self.past_weekly = []  # список с исключениями событьи недели, должен обновляться каждый понедельник.

    def send_event_info(self, events_d):
        events = events_d['items']
        for event in events:
            if event['etag'][1:-1] not in self.past_birthdays and event['etag'][1:-1] not in self.past_weekly:
                self.comparison(event)

    def comparison(self, event):
        date2 = (
            datetime.now().year, datetime.now().month, datetime.now().day, datetime.now().hour, datetime.now().minute,
            datetime.now().second)
        text = f"{event['summary']} / date: {event['start']}"
        print(self.out_bot)
        meessage = self.out_bot.send_message(self.myid, text)
        if 'recurrence' in event:  # Дни рождения
            if event['recurrence'] == ['RRULE:FREQ=YEARLY']:
                if 'dateTime' in event['start']:
                    date1 = self.changing_datetime_format(event['start']['dateTime'])
                    if (date1.month, date1.day, date1.hour, date1.minute, date1.second) < date2[1:] and event[
                        'etag'] not in self.past_birthdays:
                        self.past_birthdays.append(event['etag'].replace('"', ''))
                        meessage
                else:
                    date1 = self.changing_datetime_format(event['start']['date'])
                    if (date1.month, date1.day, date1.hour, date1.minute, date1.second) < date2[1:] and event[
                        'etag'] not in self.past_birthdays:
                        self.past_birthdays.append(event['etag'].replace('"', ''))
                        meessage

            if 'RRULE:FREQ=MONTHLY' in event['recurrence'][0]:
                if 'dateTime' in event['start']:
                    date1 = self.changing_datetime_format(event['start']['dateTime'])
                    if (date1.day, date1.hour, date1.minute, date1.second) < date2[2:] and event[
                        'etag'] not in self.past_birthdays:
                        self.past_birthdays.append(event['etag'].replace('"', ''))
                        meessage
                else:
                    date1 = self.changing_datetime_format(event['start']['date'])
                    if (date1.day, date1.hour, date1.minute, date1.second) < date2[2:] and event[
                        'etag'] not in self.past_birthdays:
                        self.past_birthdays.append(event['etag'].replace('"', ''))
                        meessage
            if 'RRULE:FREQ=WEEKLY' in event['recurrence'][0]:
                # BYDAY = MO, WE, FR, TU, TH, SA, SU   Monday Tuesday Wednesday Thursday Friday Saturday Sunday
                days_event = event['recurrence'][0].split('BYDAY=')[-1]
                if datetime.now().strftime('%A')[:2].upper() in days_event:
                    if 'dateTime' in event['start']:
                        date1 = self.changing_datetime_format(event['start']['dateTime'])
                        if (date1.hour, date1.minute, date1.second) < date2[3:] and event[
                            'etag'] not in self.past_birthdays:
                            self.past_weekly.append(event['etag'].replace('"', ''))
                            meessage
                    else:
                        date1 = self.changing_datetime_format(event['start']['date'])
                        if (date1.hour, date1.minute, date1.second) < date2[3:] and event[
                            'etag'] not in self.past_birthdays:
                            self.past_weekly.append(event['etag'].replace('"', ''))
                            meessage
        else:
            if 'dateTime' in event['start']:
                date1 = self.changing_datetime_format(event['start']['dateTime'])
                if (date1.year, date1.month, date1.day, date1.hour, date1.minute, date1.second) < date2 and event[
                    'etag'] not in self.past_birthdays:
                    self.past_birthdays.append(event['etag'].replace('"', ''))
                    meessage

            else:
                date1 = self.changing_datetime_format(event['start']['date'])
                if (date1.year, date1.month, date1.day, date1.hour, date1.minute, date1.second) < date2 and event[
                    'etag'] not in self.past_birthdays:
                    self.past_birthdays.append(event['etag'].replace('"', ''))
                    meessage

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

    def start_bot(self, n, loaded_dict, n_message):
        i = 0
        while True:
            if n.value == 1.1:
                i += 1
                time.sleep(2)  # 240 секунд в релизной версии
                print(i)
                self.send_event_info(loaded_dict)
                self.zeroing_past_birthdays()
                self.zeroing_past_weekly()

                print(n.value)


class TelegramBot:
    def __init__(self):
        self.stop = 0.0

    def start(self, n):
        bot = telebot.TeleBot(token)

        @bot.message_handler(commands=['stop'])
        def stop_bot(message):
            n.value = 0.0
            bot.send_message(message.chat.id, 'Bot stopped')

        @bot.message_handler(commands=['start'])
        def start_bot(message):
            n.value = 1.1
            bot.send_message(message.chat.id, 'Bot started')

        bot.polling(none_stop=True)


if __name__ == '__main__':
    # loaded_dict = calendar.get_events()
    # with open('dict.txt', 'wb') as f:
    #     pickle.dump(loaded_dict, f)
    with open('dict.txt', 'rb') as f:
        loaded_dict = pickle.load(f)
    num = Value('d', 0.0)
    notification_message = Queue()
    calendar = GoogleCalendar('denis.elers23@gmail.com')
    stgbot = TelegramBot()
    p1 = Process(target=stgbot.start, args=(num,))
    sbot = SenderBot(myid=myid)

    p2 = Process(target=sbot.start_bot, args=(num, loaded_dict, notification_message))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
