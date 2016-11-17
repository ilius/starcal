# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from time import time as now

import sys, os, os.path
from os import listdir
from os.path import dirname, join, isfile, splitext, isabs

from scal3.utils import NullObj, cleanCacheDict, myRaise, myRaiseTback
from scal3.utils import toBytes
from scal3.json_utils import *
from scal3.path import *

from scal3.cal_types import calTypes, jd_to

from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.locale_man import numDecode

from scal3 import core

from scal3 import event_lib
from scal3.event_diff import EventDiff

uiName = ''
null = NullObj()


#######################################################

sysConfPath = join(sysConfDir, 'ui.json') ## also includes LIVE config

confPath = join(confDir, 'ui.json')

confPathCustomize = join(confDir, 'ui-customize.json')

confPathLive = join(confDir, 'ui-live.json')

confParams = (
	'showMain',
	'winTaskbar',
	'useAppIndicator',
	'showDigClockTr',
	'fontCustomEnable',
	'fontCustom',
	'bgUseDesk',
	'bgColor',
	'borderColor',
	'cursorOutColor',
	'cursorBgColor',
	'todayCellColor',
	'textColor',
	'holidayColor',
	'inactiveColor',
	'borderTextColor',
	'cursorDiaFactor',
	'cursorRoundingFactor',
	'statusIconImage',
	'statusIconImageHoli',
	'statusIconFontFamilyEnable',
	'statusIconFontFamily',
	'statusIconFixedSizeEnable',
	'statusIconFixedSizeWH',
	'maxDayCacheSize',
	'pluginsTextStatusIcon',
	#'localTzHist',## FIXME
	'showYmArrows',
	'prefPagesOrder',
)

confParamsLive = (
	'winX',
	'winY',
	'winWidth',
	'winKeepAbove',
	'winSticky',
	'pluginsTextIsExpanded',
	'eventViewMaxHeight',
	'bgColor',
	'eventManPos',## FIXME
	'eventManShowDescription',## FIXME
	'localTzHist',
	'wcal_toolbar_weekNum_negative',
)

confParamsCustomize = (
	'mainWinItems',
	'winControllerButtons',
	'mcalHeight',
	'mcalLeftMargin',
	'mcalTopMargin',
	'mcalTypeParams',
	'mcalGrid',
	'mcalGridColor',
	'wcalHeight',
	'wcalTextSizeScale',
	'wcalItems',
	'wcalGrid',
	'wcalGridColor',
	'wcal_toolbar_mainMenu_icon',
	'wcal_weekDays_width',
	'wcalFont_weekDays',
	'wcalFont_pluginsText',
	'wcal_eventsIcon_width',
	'wcal_eventsText_showDesc',
	'wcal_eventsText_colorize',
	'wcalFont_eventsText',
	'wcal_daysOfMonth_dir',
	'wcalTypeParams',
	'wcal_daysOfMonth_width',
	'wcal_eventsCount_expand',
	'wcal_eventsCount_width',
	'wcalFont_eventsBox',
	'dcalHeight',
	'dcalTypeParams',
	'pluginsTextInsideExpander',
	'ud__wcalToolbarData',
	'ud__mainToolbarData',
)

def loadConf():
	loadModuleJsonConf(__name__)
	loadJsonConf(__name__, confPathCustomize)
	loadJsonConf(__name__, confPathLive)

def saveConf():
	saveModuleJsonConf(__name__)

def saveConfCustomize():
	saveJsonConf(__name__, confPathCustomize, confParamsCustomize)

def saveLiveConf():## rename to saveConfLive
	if core.debugMode:
		print('saveLiveConf', winX, winY, winWidth)
	saveJsonConf(__name__, confPathLive, confParamsLive)

def saveLiveConfLoop():## rename to saveConfLiveLoop
	tm = now()
	if tm-lastLiveConfChangeTime > saveLiveConfDelay:
		saveLiveConf()
		return False ## Finish loop
	return True ## Continue loop


#######################################################

def parseDroppedDate(text):
	part = text.split('/')
	if len(part)==3:
		try:
			part[0] = numDecode(part[0])
			part[1] = numDecode(part[1])
			part[2] = numDecode(part[2])
		except:
			myRaise(__file__)
			return None
		maxPart = max(part)
		if maxPart > 999:
			minMax = (
				(1000, 2100),
				(1, 12),
				(1, 31),
			)
			formats = (
				[0, 1, 2],
				[1, 2, 0],
				[2, 1, 0],
			)
			for format in formats:
				for i in range(3):
					valid = True
					f = format[i]
					if not (minMax[f][0] <= part[i] <= minMax[f][1]):
						valid = False
						#print('format %s was not valid, part[%s]=%s'%(format, i, part[i]))
						break
				if valid:
					year = part[format.index(0)] ## "format" must be list because of method "index"
					month = part[format.index(1)]
					day = part[format.index(2)]
					break
		else:
			valid = 0 <= part[0] <= 99 and 1 <= part[1] <= 12 and 1 <= part[2] <= 31
			###
			year = 2000 + part[0] ## FIXME
			month = part[1]
			day = part[2]
		if not valid:
			return None
	else:
		return None
	##??????????? when drag from a persian GtkCalendar with format %y/%m/%d
	#if year < 100:
	#	year += 2000
	return (year, month, day)

def dictsTupleConfStr(data):
	n = len(data)
	st = '('
	for i in range(n):
		d = data[i].copy()
		st += '\n{'
		for k in d.keys():
			v = d[k]
			if isinstance(k, str):
				ks = '\'%s\''%k
			else:
				ks = str(k)
			if isinstance(v, str):
				vs = '\'%s\''%v
			else:
				vs = str(v)
			st += '%s:%s, '%(ks,vs)
		if i==n-1:
			st = st[:-2] + '})'
		else:
			st = st[:-2] + '},'
	return st


def checkNeedRestart():
	for key in needRestartPref.keys():
		if needRestartPref[key] != eval(key):
			print('"%s", "%s", "%s"'%(key, needRestartPref[key], eval(key)))
			return True
	return False

getPywPath = lambda: join(rootDir, core.APP_NAME + ('-qt' if uiName=='qt' else '') + '.pyw')


def dayOpenEvolution(arg=None):
	from subprocess import Popen
	##y, m, d = jd_to(cell.jd-1, core.DATE_GREG) ## in gnome-cal opens prev day! why??
	y, m, d = cell.dates[core.DATE_GREG]
	Popen('LANG=en_US.UTF-8 evolution calendar:///?startdate=%.4d%.2d%.2d'%(y, m, d), shell=True)## FIXME
	## 'calendar:///?startdate=%.4d%.2d%.2dT120000Z'%(y, m, d)
	## What "Time" pass to evolution? like gnome-clock: T193000Z (19:30:00) / Or ignore "Time"
	## evolution calendar:///?startdate=$(date +"%Y%m%dT%H%M%SZ")

def dayOpenSunbird(arg=None):
	from subprocess import Popen
	## does not work on latest version of Sunbird ## FIXME
	## and Sunbird seems to be a dead project
	## Opens previous day in older version
	y, m, d = cell.dates[core.DATE_GREG]
	Popen('LANG=en_US.UTF-8 sunbird -showdate %.4d/%.2d/%.2d'%(y, m, d), shell=True)

## How do this with KOrginizer? FIXME

#######################################################################


class Cell:## status and information of a cell
	#ocTimeMax = 0
	#ocTimeCount = 0
	#ocTimeSum = 0
	def __init__(self, jd):
		self.eventsData = []
		#self.eventsDataIsSet = False ## not used
		self.pluginsText = ''
		###
		self.jd = jd
		date = core.jd_to_primary(jd)
		self.year, self.month, self.day = date
		self.weekDay = core.jwday(jd)
		self.weekNum = core.getWeekNumber(self.year, self.month, self.day)
		#self.weekNumNeg = self.weekNum + 1 - core.getYearWeeksCount(self.year)
		self.weekNumNeg = self.weekNum - int(calTypes.primaryModule().avgYearLen / 7)
		self.holiday = (self.weekDay in core.holidayWeekDays)
		###################
		self.dates = [
			date if mode==calTypes.primary else jd_to(jd, mode)
			for mode in range(len(calTypes))
		]
		'''
		self.dates = dict([
			(
				mode, date if mode==calTypes.primary else jd_to(jd, mode)
			)
			for mode in calTypes.active
		])
		'''
		###################
		for k in core.plugIndex:
			plug = core.allPlugList[k]
			if plug:
				try:
					plug.update_cell(self)
				except:
					myRaiseTback()
		###################
		#t0 = now()
		self.eventsData = event_lib.getDayOccurrenceData(jd, eventGroups)## here? FIXME
		#dt = now() - t0
		#Cell.ocTimeSum += dt
		#Cell.ocTimeCount += 1
		#Cell.ocTimeMax = max(Cell.ocTimeMax, dt)
	def format(self, binFmt, mode=None, tm=null):## FIXME
		if mode is None:
			mode = calTypes.primary
		pyFmt, funcs = binFmt
		return pyFmt%tuple(f(self, mode, tm) for f in funcs)
	inSameMonth = lambda self, other:\
		self.dates[calTypes.primary][:2] == other.dates[calTypes.primary][:2]
	def getEventIcons(self, showIndex):
		iconList = []
		for item in self.eventsData:
			if not item['show'][showIndex]:
				continue
			icon = item['icon']
			if icon and not icon in iconList:
				iconList.append(icon)
		return iconList
	getDayEventIcons = lambda self: self.getEventIcons(0)
	getWeekEventIcons = lambda self: self.getEventIcons(1)
	getMonthEventIcons = lambda self: self.getEventIcons(2)



class CellCache:
	def __init__(self):
		self.jdCells = {} ## a mapping from julan_day to Cell instance
		self.plugins = {}
		self.weekEvents = {}
	def clear(self):
		global cell, todayCell
		self.jdCells = {}
		self.weekEvents = {}
		cell = self.getCell(cell.jd)
		todayCell = self.getCell(todayCell.jd)
	def registerPlugin(self, name, setParamsCallable, getCellGroupCallable):
		"""
			setParamsCallable(cell): cell.attr1 = value1 ....
			getCellGroupCallable(cellCache, *args): return cell_group
				call cellCache.getCell(jd) inside getCellGroupFunc
		"""
		self.plugins[name] = (
			setParamsCallable,
			getCellGroupCallable,
		)
		for localCell in self.jdCells.values():
			setParamsCallable(localCell)
	def getCell(self, jd):
		try:
			return self.jdCells[jd]
		except KeyError:
			return self.buildCell(jd)
	def getTmpCell(self, jd):## don't keep, no eventsData, no plugin params
		try:
			return self.jdCells[jd]
		except KeyError:
			return Cell(jd)
	getCellByDate = lambda self, y, m, d: self.getCell(core.primary_to_jd(y, m, d))
	getTodayCell = lambda self: self.getCell(core.getCurrentJd())
	def buildCell(self, jd):
		localCell = Cell(jd)
		for pluginData in self.plugins.values():
			pluginData[0](localCell)
		self.jdCells[jd] = localCell
		cleanCacheDict(self.jdCells, maxDayCacheSize, jd)
		return localCell
	getCellGroup = lambda self, pluginName, *args:\
		self.plugins[pluginName][1](self, *args)
	def getWeekData(self, absWeekNumber):
		cells = self.getCellGroup('WeekCal', absWeekNumber)
		try:
			wEventData = self.weekEvents[absWeekNumber]
		except KeyError:
			wEventData = event_lib.getWeekOccurrenceData(absWeekNumber, eventGroups)
			cleanCacheDict(self.weekEvents, maxWeekCacheSize, absWeekNumber)
			self.weekEvents[absWeekNumber] = wEventData
		return cells, wEventData
	#def getMonthData(self, year, month):## needed? FIXME


def changeDate(year, month, day, mode=None):
	global cell
	if mode is None:
		mode = calTypes.primary
	cell = cellCache.getCell(core.to_jd(year, month, day, mode))

def gotoJd(jd):
	global cell
	cell = cellCache.getCell(jd)

def jdPlus(plus=1):
	global cell
	cell = cellCache.getCell(cell.jd + plus)

def getMonthPlus(tmpCell, plus):
	year, month = core.monthPlus(tmpCell.year, tmpCell.month, plus)
	day = min(tmpCell.day, core.getMonthLen(year, month, calTypes.primary))
	return cellCache.getCellByDate(year, month, day)

def monthPlus(plus=1):
	global cell
	cell = getMonthPlus(cell, plus)

def yearPlus(plus=1):
	global cell
	year = cell.year + plus
	month = cell.month
	day = min(cell.day, core.getMonthLen(year, month, calTypes.primary))
	cell = cellCache.getCellByDate(year, month, day)

def getFont(scale=1.0):
	(name, bold, underline, size) = fontCustom if fontCustomEnable else fontDefaultInit
	return [name, bold, underline, size*scale]

def initFonts(fontDefaultNew):
	global fontDefault, fontCustom, mcalTypeParams
	fontDefault = fontDefaultNew
	if not fontCustom:
		fontCustom = fontDefault
	########
	###
	if mcalTypeParams[0]['font']==None:
		mcalTypeParams[0]['font'] = getFont(1.0)
	###
	for item in mcalTypeParams[1:]:
		if item['font']==None:
			item['font'] = getFont(0.6)
	######
	if dcalTypeParams[0]['font']==None:
		dcalTypeParams[0]['font'] = getFont(10.0)
	###
	for item in dcalTypeParams[1:]:
		if item['font']==None:
			item['font'] = getFont(3.0)


def getHolidaysJdList(startJd, endJd):
	jdList = []
	for jd in range(startJd, endJd):
		tmpCell = cellCache.getTmpCell(jd)
		if tmpCell.holiday:
			jdList.append(jd)
	return jdList


######################################################################

def checkMainWinItems():
	global mainWinItems
	#print(mainWinItems)
	## cleaning and updating mainWinItems
	names = set([name for (name, i) in mainWinItems])
	defaultNames = set([name for (name, i) in mainWinItemsDefault])
	#print(mainWinItems)
	#print(sorted(list(names)))
	#print(sorted(list(defaultNames)))
	#####
	## removing items that are no longer supported
	mainWinItems, mainWinItemsTmp = [], mainWinItems
	for name, enable in mainWinItemsTmp:
		if name in defaultNames:
			mainWinItems.append((name, enable))
	#####
	## adding items newly added in this version, this is for user's convenience
	newNames = defaultNames.difference(names)
	#print('mainWinItems: newNames =', newNames)
	##
	name = 'winContronller'
	if name in newNames:
		mainWinItems.insert(0, (name, True))
		newNames.remove(name)
	##
	for name in newNames:
		mainWinItems.append((name, False))## FIXME


def deleteEventGroup(group):
	eventGroups.moveToTrash(group, eventTrash)

def moveEventToTrash(group, event):
	eventIndex = group.remove(event)
	group.save()
	eventTrash.insert(0, event)## or append? FIXME
	eventTrash.save()
	return eventIndex

def moveEventToTrashFromOutside(group, event):
	global reloadGroups, reloadTrash
	moveEventToTrash(group, event)
	reloadGroups.append(group.id)
	reloadTrash = True

getEvent = lambda groupId, eventId: eventGroups[groupId][eventId]

def duplicateGroupTitle(group):
	title = group.title
	titleList = [g.title for g in eventGroups]
	parts = title.split('#')
	try:
		index = int(parts[-1])
		title = '#'.join(parts[:-1])
	except:
		#myRaise()
		index = 1
	index += 1
	while True:
		newTitle = title + '#%d'%index
		if newTitle not in titleList:
			group.title = newTitle
			return
		index += 1


def init():
	global todayCell, cell, eventAccounts, eventGroups
	core.init()
	#### Load accounts, groups and trash? FIXME
	eventAccounts = event_lib.EventAccountsHolder.load()
	eventGroups = event_lib.EventGroupsHolder.load()
	####
	todayCell = cell = cellCache.getTodayCell() ## FIXME



######################################################################

localTzHist = [
	str(core.localTz),
]

shownCals = [] ## FIXME

mcalTypeParams = [
	{
		'pos': (0, -2),
		'font': None,
		'color': (220, 220, 220),
	},
	{
		'pos': (18, 5),
		'font': None,
		'color': (165, 255, 114),
	},
	{
		'pos': (-18, 4),
		'font': None,
		'color': (0, 200, 205),
	},
]

wcalTypeParams = [
	{'font': None},
	{'font': None},
	{'font': None},
]

dcalTypeParams = [## FIXME
	{
		'pos': (0, -12),
		'font': None,
		'color': (220, 220, 220),
	},
	{
		'pos': (125, 30),
		'font': None,
		'color': (165, 255, 114),
	},
	{
		'pos': (-125, 24),
		'font': None,
		'color': (0, 200, 205),
	},
]


getActiveMonthCalParams = lambda: list(zip(
	calTypes.active,
	mcalTypeParams,
))


getActiveDayCalParams = lambda: list(zip(
	calTypes.active,
	dcalTypeParams,
))


################################
tagsDir = join(pixDir, 'event')

class TagIconItem:
	def __init__(self, name, desc='', icon='', eventTypes=()):
		self.name = name
		if not desc:
			desc = name.capitalize()
		self.desc = _(desc)
		if icon:
			if not isabs(icon):
				icon = join(tagsDir, icon)
		else:
			iconTmp = join(tagsDir, name) + '.png'
			if isfile(iconTmp):
				icon = iconTmp
		self.icon = icon
		self.eventTypes = eventTypes
		self.usage = 0
	__repr__ = lambda self: 'TagIconItem(%r, desc=%r, icon=%r, eventTypes=%r)'%(
		self.name,
		self.desc,
		self.icon,
		self.eventTypes,
	)


eventTags = (
	TagIconItem('birthday', eventTypes=('yearly',)),
	TagIconItem('marriage', eventTypes=('yearly',)),
	TagIconItem('obituary', eventTypes=('yearly',)),
	TagIconItem('note', eventTypes=('dailyNote',)),
	TagIconItem('task', eventTypes=('task',)),
	TagIconItem('alarm'),
	TagIconItem('business'),
	TagIconItem('personal'),
	TagIconItem('favorite'),
	TagIconItem('important'),
	TagIconItem('appointment', eventTypes=('task',)),
	TagIconItem('meeting', eventTypes=('task',)),
	TagIconItem('phone_call', desc='Phone Call', eventTypes=('task',)),
	TagIconItem('university', eventTypes=('task',)),## FIXME
	TagIconItem('education'),
	TagIconItem('holiday'),
	TagIconItem('travel'),
)

getEventTagsDict = lambda: dict([(tagObj.name, tagObj) for tagObj in eventTags])
eventTagsDesc = dict([(t.name, t.desc) for t in eventTags])

###################
eventTrash = event_lib.EventTrash.load()
eventAccounts = []
eventGroups = []

def iterAllEvents():## dosen't include orphan events
	for group in eventGroups:
		for event in group:
			yield event
	for event in eventTrash:
		yield event



changedGroups = []## list of groupId's
reloadGroups = [] ## a list of groupId's that their contents are changed
reloadTrash = False

eventDiff = EventDiff()



#def updateEventTagsUsage():## FIXME where to use?
#	tagsDict = getEventTagsDict()
#	for tagObj in eventTags:
#		tagObj.usage = 0
#	for event in events:## FIXME
#		for tag in event.tags:
#			try:
#				tagsDict[tag].usage += 1
#			except KeyError:
#				pass


###################
## BUILD CACHE AFTER SETTING calTypes.primary
maxDayCacheSize = 100 ## maximum size of cellCache (days number)
maxWeekCacheSize = 12

cellCache = CellCache()
todayCell = cell = None
###########################
autoLocale = True
logo = join(pixDir, 'starcal.png')
###########################
#themeDir = join(rootDir, 'themes')
#theme = None
########################### Options ###########################
winWidth = 480
mcalHeight = 250
winTaskbar = False
useAppIndicator = True
showDigClockTb = True ## On Toolbar ## FIXME
showDigClockTr = True ## On Status Icon
####
toolbarIconSizePixel = 24 ## used in pyqt ui
####
bgColor = (26, 0, 1, 255)## or None
bgUseDesk = False
borderColor = (123, 40, 0, 255)
borderTextColor = (255, 255, 255, 255) ## text of weekDays and weekNumbers
#menuBgColor = borderColor ##???????????????
textColor = (255, 255, 255, 255)
menuTextColor = None##borderTextColor##???????????????
holidayColor = (255, 160, 0, 255)
inactiveColor = (255, 255, 255, 115)
todayCellColor  = (0, 255, 0, 50)
##########
cursorOutColor = (213, 207, 0, 255)
cursorBgColor = (41, 41, 41, 255)
cursorDiaFactor = 0.15
cursorRoundingFactor = 0.50
mcalGrid = False
mcalGridColor = (255, 252, 0, 82)
##########
mcalLeftMargin = 30
mcalTopMargin = 30
####################
wcalHeight = 200
wcalTextSizeScale = 0.6 ## between 0 and 1
#wcalTextColor = (255, 255, 255) ## FIXME
wcalPadding = 10
wcalGrid = False
wcalGridColor = (255, 252, 0, 82)

wcal_toolbar_mainMenu_icon = join(pixDir, 'starcal-24.png')
wcal_toolbar_mainMenu_icon_default = wcal_toolbar_mainMenu_icon
wcal_toolbar_weekNum_negative = False
wcal_weekDays_width = 80
wcal_eventsCount_width = 80
wcal_eventsCount_expand = False
wcal_eventsIcon_width = 50
wcal_eventsText_showDesc = False
wcal_eventsText_colorize = True
wcal_daysOfMonth_width = 30
wcal_daysOfMonth_dir = 'ltr' ## ltr/rtl/auto
wcalFont_eventsText = None
wcalFont_weekDays = None
wcalFont_pluginsText = None
wcalFont_eventsBox = None


####################
dcalHeight = 250


####################
boldYmLabel = True ## apply in Pref FIXME
showYmArrows = True ## apply in Pref FIXME
labelMenuDelay = 0.1 ## delay for shift up/down items of menu for right click on YearLabel
####################
statusIconImage = join(rootDir, 'status-icons', 'dark-green.svg')
statusIconImageHoli = join(rootDir, 'status-icons', 'dark-red.svg')
statusIconImageDefault, statusIconImageHoliDefault = statusIconImage, statusIconImageHoli
statusIconFontFamilyEnable = False
statusIconFontFamily = None
statusIconFixedSizeEnable = False
statusIconFixedSizeWH = (24, 24)
####################
menuActiveLabelColor = "#ff0000"
pluginsTextStatusIcon = False
pluginsTextInsideExpander = True
pluginsTextIsExpanded = True ## affect only if pluginsTextInsideExpander
eventViewMaxHeight = 200
####################
dragGetMode = core.DATE_GREG  ## apply in Pref FIXME
#dragGetDateFormat = '%Y/%m/%d'
dragRecMode = core.DATE_GREG  ## apply in Pref FIXME
####################
monthRMenuNum = True
#monthRMenu
prefPagesOrder = tuple(range(5))
winControllerButtons = (
	('sep', True),
	('min', True),
	('max', False),
	('close', True),
	('sep', False),
	('sep', False),
	('sep', False),
)
winControllerSpacing = 0
####################
winKeepAbove = True
winSticky = True
winX = 0
winY = 0
###
fontDefault = ['Sans', False, False, 12]
fontDefaultInit = fontDefault
fontCustom = None
fontCustomEnable = False
#####################
showMain = True ## Show main window on start (or only goto statusIcon)
#####################
mainWinItems = (
	('winContronller', True),
	('toolbar', True),
	('labelBox', True),
	('monthCal', False),
	('weekCal', True),
	('dayCal', False),
	('statusBar', True),
	('seasonPBar', True),
	('pluginsText', True),
	('eventDayView', True),
)

mainWinItemsDefault = mainWinItems[:]


wcalItems = (
	('toolbar', True),
	('weekDays', True),
	('pluginsText', True),
	('eventsIcon', True),
	('eventsText', True),
	('daysOfMonth', True),
)

wcalItemsDefault = wcalItems[:]

####################

ntpServers = (
	'pool.ntp.org',
	'ir.pool.ntp.org',
	'asia.pool.ntp.org',
	'europe.pool.ntp.org',
	'north-america.pool.ntp.org',
	'oceania.pool.ntp.org',
	'south-america.pool.ntp.org',
	'ntp.ubuntu.com',
)


#####################
#dailyNoteChDateOnEdit = True ## change date of a dailyNoteEvent when editing it
eventManPos = (0, 0)
eventManShowDescription = True
#####################
focusTime = 0
lastLiveConfChangeTime = 0


saveLiveConfDelay = 0.5 ## seconds
timeout_initial = 200
timeout_repeat = 50


def updateFocusTime(*args):
	global focusTime
	focusTime = now()



########################################################

loadConf()

########################################################

if not isfile(statusIconImage):
	statusIconImage = statusIconImageDefault
if not isfile(statusIconImageHoli):
	statusIconImageHoli = statusIconImageHoliDefault


try:
	localTzHist.remove(str(core.localTz))
except ValueError:
	pass
localTzHist.insert(0, str(core.localTz))
saveLiveConf()


needRestartPref = {} ### Right place ????????
for key in (
	'locale_man.lang',
	'locale_man.enableNumLocale',
	'winTaskbar',
	'showYmArrows',
	'useAppIndicator',
):
	needRestartPref[key] = eval(key)

if menuTextColor is None:
	menuTextColor = borderTextColor

##################################

## move to gtk_ud ? FIXME
mainWin = None
prefDialog = None
eventManDialog = None
timeLineWin = None
weekCalWin = None






