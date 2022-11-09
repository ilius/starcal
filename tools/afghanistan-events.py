#!/usr/bin/python3

import os
from os.path import join, dirname, realpath
import json
from collections import OrderedDict

myPath = realpath(__file__)
sourceDir = dirname(dirname(myPath))
pluginsDir = join(sourceDir, "plugins")

holidaysAbout = "\n".join([
	"Official Holidays of Afghanistan",
	"تعطیلات رسمی افغانستان (آخرین تغییرات: ۱۳۹۶/۱۲/۲۴)\n"
	"برای روزهای تعطیل، رنگ شماره‌ ماه را تغییر می‌دهد",
	"برای تنظیم این رنگ مراجعه کنید به:",
	"ترجیحات -> ظاهر -> رنگ نوشته‌ها -> روز تعطیل",
])

holidaysAuthors = [
    "وزارت شهرسازی و اراضی افغانستان",
    "Ebrahim Byagowi <ebrahim@gnu.org>",
    "سعید رسولی <saeed.gnu@gmail.com>",
]


jsonPath = join(
	os.getenv("HOME"),
	"DroidPersianCalendar",
	"PersianCalendar",
	"data",
	"events.json",
)

with open(jsonPath) as jsonFile:
	data = json.load(jsonFile)

#print(list(data.keys()))
#print(data['Irregular Recurring'])

calTypes = {
	"jalali": "Persian Calendar",
	"hijri": "Hijri Calendar",
	"gregorian": "Gregorian Calendar",
}

holidays = {}

for calType, calTypeKey in calTypes.items():
	calTypeHolidays = []
	with open(join(pluginsDir, f"afghanistan-{calType}-data.txt"), mode="w") as outFile:
		for event in data[calTypeKey]:
			if event["type"] != "Afghanistan":
				continue
			outFile.write(
				f"{event['month']}/{event['day']}\t{event['title']}\n"
			)
			if event["holiday"]:
				calTypeHolidays.append((event['month'], event['day']))

	if calTypeHolidays:
		holidays[calType] = calTypeHolidays


with open(join(pluginsDir, "holidays-afghanistan.json"), mode="w") as outFile:
	json.dump(OrderedDict([
		("type", "holiday"),
		("title", "تعطیلات رسمی افغانستان"),
		("about", holidaysAbout),
		("authors", holidaysAuthors),
		("hasConfig", False),
		("holidays", holidays),
	]), outFile, ensure_ascii=False, indent="\t")




