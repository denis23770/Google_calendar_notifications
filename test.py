from datetime import datetime, date


date_string = "11-07"
date_format = '%m-%d'
date_obj = datetime.strptime(date_string, date_format)

print(date_obj.day)

print(date_obj < datetime.now())
print(datetime.now().strftime('%A'))
