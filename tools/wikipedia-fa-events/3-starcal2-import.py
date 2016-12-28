# -*- coding: utf-8 -*-

import os
import sys

sys.path.append('/starcal2')

from scal3.date_utils import dateDecode
from scal3.core import to_jd, jd_to, convert, moduleNames
from scal3 import event_lib
from scal3 import ui

dataToPrettyJson = lambda data: json.dumps(data, sort_keys=True, indent=2)

DATE_GREG = moduleNames.index('gregorian')
DATE_JALALI = moduleNames.index('jalali')

ui.eventGroups.load()

groupTitlePrefix = 'ویکی‌پدیا - '
newGroupsDict = {}


def getGroupByTitle(title):
	global newGroupsDict
	try:
		return newGroupsDict[title]
	except KeyError:
		group = event_lib.NoteBook()
		group.setData({
			'calType': 'jalali',
			'color': [255, 255, 0],
			'title': title,

		})
		newGroupsDict[title] = group
		ui.eventGroups.append(group)
		return group


for line in open('wikipedia-fa.tab'):
	line = line.strip()
	if not line:
		continue
	parts = line.split('\t')
	if len(parts) == 4:
		date_str, category, summary, description = parts
	elif len(parts) == 3:
		date_str, category, summary = parts
		description = ''
	else:
		print('BAD LINE', line)
		continue
	year, month, day = dateDecode(date_str)
	group = getGroupByTitle(groupTitlePrefix + category)
	event = group.createEvent('dailyNote')
	event.setDate(year, month, day)
	event.summary = summary
	event.description = description
	group.append(event)
	event.save()


for group in newGroupsDict.values():
	group.save()
ui.eventGroups.save()
