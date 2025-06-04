import json
import sys

sys.path.append("/starcal2")

from scal3 import event_lib, logger
from scal3.date_utils import dateDecode
from scal3.event_lib import ev


def dataToPrettyJson(data):
	return json.dumps(data, sort_keys=True, indent=2)


log = logger.get()

ev.groups.load()

groupTitlePrefix = "ویکی‌پدیا - "
newGroupsDict = {}


def getGroupByTitle(title):
	try:
		return newGroupsDict[title]
	except KeyError:
		group = event_lib.NoteBook()
		group.setData(
			{
				"calType": "jalali",
				"color": [255, 255, 0],
				"title": title,
			},
		)
		newGroupsDict[title] = group
		ev.groups.append(group)
		return group


for line in open("wikipedia-fa.tab", encoding="utf-8"):  # noqa: SIM115
	line = line.strip()  # noqa: PLW2901
	if not line:
		continue
	parts = line.split("\t")
	if len(parts) == 4:
		date_str, category, summary, description = parts
	elif len(parts) == 3:
		date_str, category, summary = parts
		description = ""
	else:
		log.info(f"BAD LINE: {line}")
		continue
	year, month, day = dateDecode(date_str)
	group = getGroupByTitle(groupTitlePrefix + category)
	event = group.createEvent("dailyNote")
	event.setDate(year, month, day)
	event.summary = summary
	event.description = description
	group.append(event)
	event.save()


for group in newGroupsDict.values():
	group.save()
ev.groups.save()
