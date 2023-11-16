from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
calendar_id = os.getenv('calendar_id')  # айди календаря


class AddCalendar:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    FILE_PATH = 'pythonnot-691616cc1321.json'  # ключ сервисного аккаунта google

    def __init__(self, calendar_id):
        credentials = service_account.Credentials.from_service_account_file(
            filename=self.FILE_PATH, scopes=self.SCOPES
        )

        self.service = build('calendar', 'v3', credentials=credentials)
        self.calendar_id = calendar_id

    def get_calendar_list(self):
        return self.service.calendarList().list().execute()

    def add_calendar(self):
        calendar_list_entry = {
            'id': self.calendar_id
        }
        return self.service.calendarList().insert(
            body=calendar_list_entry).execute()


obj = AddCalendar(calendar_id=calendar_id)
obj.add_calendar()
