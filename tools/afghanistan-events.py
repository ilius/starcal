#!/usr/bin/python3

import json
import os
from collections import OrderedDict
from os.path import dirname, join, realpath

myPath = realpath(__file__)
sourceDir = dirname(dirname(myPath))
plugDir = join(sourceDir, "plugins")

holidaysAbout = "\n".join(
	[
		"Official Holidays of Afghanistan",
		(
			"تعطیلات رسمی افغانستان (آخرین تغییرات: ۱۳۹۶/۱۲/۲۴)\n"
			"برای روزهای تعطیل، رنگ شماره‌ ماه را تغییر می‌دهد"
		),
		"برای تنظیم این رنگ مراجعه کنید به:",
		"ترجیحات -> ظاهر -> رنگ نوشته‌ها -> روز تعطیل",
	],
)

holidaysAuthors = [
	"وزارت شهرسازی و اراضی افغانستان",
	"Ebrahim Byagowi <ebrahim@gnu.org>",
	"سعید رسولی <saeed.gnu@gmail.com>",
]

homeDir = os.getenv("HOME")
assert homeDir
jsonPath = join(
	homeDir,
	"DroidPersianCalendar",
	"PersianCalendar",
	"data",
	"events.json",
)

with open(jsonPath, encoding="utf-8") as jsonFile:
	data = json.load(jsonFile)

# print(list(data))
# print(data['Irregular Recurring'])

calTypes = {
	"jalali": "Persian Calendar",
	"hijri": "Hijri Calendar",
	"gregorian": "Gregorian Calendar",
}

holidays = {}

for calType, calTypeKey in calTypes.items():
	calTypeHolidays = []
	with open(
		join(plugDir, f"afghanistan-{calType}-data.txt"),
		mode="w",
		encoding="utf-8",
	) as outFile:
		for event in data[calTypeKey]:
			if event["type"] != "Afghanistan":
				continue
			outFile.write(f"{event['month']}/{event['day']}\t{event['title']}\n")
			if event["holiday"]:
				calTypeHolidays.append((event["month"], event["day"]))

	if calTypeHolidays:
		holidays[calType] = calTypeHolidays


with open(
	join(plugDir, "holidays-afghanistan.json"),
	mode="w",
	encoding="utf-8",
) as outFile:
	json.dump(
		OrderedDict(
			[
				("type", "holiday"),
				("title", "تعطیلات رسمی افغانستان"),
				("about", holidaysAbout),
				("authors", holidaysAuthors),
				("hasConfig", False),
				("holidays", holidays),
			],
		),
		outFile,
		ensure_ascii=False,
		indent="\t",
	)
