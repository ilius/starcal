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

import sys
from time import strftime
from time import localtime
from os.path import isfile, dirname, join, split, splitext, isabs


from scal3.path import *
from scal3.utils import myRaiseTback
from scal3.json_utils import *
from scal3.cal_types import calTypes, jd_to, to_jd, convert, DATE_GREG
from scal3.date_utils import ymdRange
from scal3.locale_man import tr as _
from scal3.locale_man import getMonthName
from scal3.ics import icsTmFormat, icsHeader
from scal3.s_object import *

try:
	import logging
	log = logging.getLogger(APP_NAME)
except:
	from scal3.utils import FallbackLogger
	log = FallbackLogger()

## FIXME
pluginsTitleByName = {
	'pray_times': _('Islamic Pray Times'),
}

pluginClassByName = {}


def registerPlugin(cls):
	assert cls.name
	pluginClassByName[cls.name] = cls
	return cls


def getPlugPath(_file):
	return _file if isabs(_file) else join(plugDir, _file)


def myRaise(File=__file__):
	i = sys.exc_info()
	log.error('File "%s", line %s: %s: %s\n' % (
		File,
		i[2].tb_lineno,
		i[0].__name__, i[1],
	))


class BasePlugin(SObj):
	name = None
	external = False
	loaded = True
	params = (
		#'mode',
		'title',  # previously 'desc'
		'enable',
		'show_date',
		'default_enable',
		'default_show_date',
		'about',
		'authors',
		'hasConfig',
		'hasImage',
		'lastDayMerge',
	)
	essentialParams = (  # FIXME
		'title',
	)

	def getArgs(self):
		return {
			'_file': self.file,
			'enable': self.enable,
			'show_date': self.show_date,
		}

	def __bool__(self):
		return self.enable  # FIXME

	def __init__(
		self,
		_file,
	):
		self.file = _file
		######
		self.mode = DATE_GREG
		self.title = ''
		###
		self.enable = False
		self.show_date = False
		##
		self.default_enable = False
		self.default_show_date = False
		###
		self.about = ''
		self.authors = []
		self.hasConfig = False
		self.hasImage = False
		self.lastDayMerge = True

	def getData(self):
		data = JsonSObj.getData(self)
		data['calType'] = calTypes.names[self.mode]
		return data

	def setData(self, data):
		if 'enable' not in data:
			data['enable'] = data.get('default_enable', self.default_enable)
		###
		if 'show_date' not in data:
			data['show_date'] = data.get('default_show_date', self.default_show_date)
		###
		try:
			data['title'] = _(data['title'])
		except KeyError:
			pass
		###
		try:
			data['about'] = _(data['about'])
		except KeyError:
			pass
		###
		try:
			authors = data['authors']
		except KeyError:
			pass
		else:
			data['authors'] = [_(author) for author in authors]
		#####
		if 'calType' in data:
			calType = data['calType']
			try:
				self.mode = calTypes.names.index(calType)
			except ValueError:
				#raise ValueError('Invalid calType: %r'%calType)
				log.error(
					'Plugin "%s" needs calendar module ' % _file +
					'"%s"' + ' that is not loaded!\n' % mode
				)
				self.mode = None
			del data['calType']
		#####
		JsonSObj.setData(self, data)

	def clear(self):
		pass

	def load(self):
		pass

	def getText(self, year, month, day):
		return ''

	def updateCell(self, c):
		y, m, d = c.dates[self.mode]
		text = ''
		t = self.getText(y, m, d)
		if t:
			text += t
		if self.lastDayMerge and d >= calTypes[self.mode].minMonthLen:
			# and d<=calTypes[self.mode].maxMonthLen:
			ny, nm, nd = jd_to(c.jd + 1, self.mode)
			if nm > m or ny > y:
				nt = self.getText(y, m, d + 1)
				if nt:
					text += nt
		if text:
			if c.pluginsText:
				c.pluginsText += '\n'
			c.pluginsText += text

	def onCurrentDateChange(self, gdate):
		pass

	def exportToIcs(self, fileName, startJd, endJd):
		currentTimeStamp = strftime(icsTmFormat)
		self.load()  # FIXME
		mode = self.mode
		icsText = icsHeader
		for jd in range(startJd, endJd):
			myear, mmonth, mday = jd_to(jd, mode)
			dayText = self.getText(myear, mmonth, mday)
			if dayText:
				gyear, gmonth, gday = jd_to(jd, DATE_GREG)
				gyear_next, gmonth_next, gday_next = jd_to(jd + 1, DATE_GREG)
				#######
				icsText += '\n'.join([
					'BEGIN:VEVENT',
					'CREATED:%s' % currentTimeStamp,
					'LAST-MODIFIED:%s' % currentTimeStamp,
					'DTSTART;VALUE=DATE:%.4d%.2d%.2d' % (
						gyear,
						gmonth,
						gday,
					),
					'DTEND;VALUE=DATE:%.4d%.2d%.2d' % (
						gyear_next,
						gmonth_next,
						gday_next,
					),
					'SUMMARY:%s' % dayText,
					'END:VEVENT',
				]) + '\n'
		icsText += 'END:VCALENDAR\n'
		open(fileName, 'w').write(icsText)


class BaseJsonPlugin(BasePlugin, JsonSObj):
	def save(self):  # json file self.file is read-only
		pass


class DummyExternalPlugin(BasePlugin):
	name = 'external' ## FIXME
	external = True
	loaded = False
	enable = False
	show_date = False
	about = ''
	authors = []
	hasConfig = False
	hasImage = False

	def __repr__(self):
		return 'loadPlugin(%r, enable=False, show_date=False)' % self.file

	def __init__(self, _file, title):
		self.file = _file
		self.title = title


def loadExternalPlugin(_file, **data):
	_file = getPlugPath(_file)
	fname = split(_file)[-1]
	if not isfile(_file):
		log.error('plugin file "%s" not found! maybe removed?' % _file)
		#try:
		#	plugIndex.remove(
		return None  # FIXME
		#plug = BaseJsonPlugin(
		#	_file,
		#	mode=0,
		#	title='Failed to load plugin',
		#	enable=enable,
		#	show_date=show_date,
		#)
		#plug.external = True
		#return plug
	###
	direc = dirname(_file)
	name = splitext(fname)[0]
	###
	if not data.get('enable'):
		return DummyExternalPlugin(
			_file,
			pluginsTitleByName.get(name, name),
		)
	###
	try:
		mainFile = data['mainFile']
	except KeyError:
		log.error('invalid external plugin "%s"' % _file)
		return
	###
	mainFile = getPlugPath(mainFile)
	###
	pyEnv = {
		'__file__': mainFile,
		'BasePlugin': BasePlugin,
		'BaseJsonPlugin': BaseJsonPlugin,
	}
	try:
		exec(open(mainFile).read(), pyEnv)
	except:
		log.error('error while loading external plugin "%s"' % _file)
		myRaiseTback()
		return
	###
	try:
		cls = pyEnv['TextPlugin']
	except KeyError:
		log.error('invalid external plugin "%s", no TextPlugin class' % _file)
		return
	###
	try:
		plugin = cls(_file)
	except:
		log.error('error while loading external plugin "%s"' % _file)
		myRaiseTback()
		return

	#sys.path.insert(0, direc)
	#try:
	#	mod = __import__(name)
	#except:
	#	myRaiseTback()
	#	return None
	#finally:
	#	sys.path.pop(0)
	## mod.module_init(rootDir, ) ## FIXME
	#try:
	#	plugin = mod.TextPlugin(_file)
	#except:
	#	myRaiseTback()
	#	#print(dir(mod))
	#	return
	plugin.external = True
	plugin.setData(data)
	plugin.onCurrentDateChange(localtime()[:3])
	return plugin


@registerPlugin
class HolidayPlugin(BaseJsonPlugin):
	name = 'holiday'

	def __init__(self, _file):
		BaseJsonPlugin.__init__(
			self,
			_file,
		)
		self.lastDayMerge = True ## FIXME
		self.holidays = {}

	def setData(self, data):
		if 'holidays' in data:
			for modeName in data['holidays']:
				try:
					mode = calTypes.names.index(modeName)
				except ValueError:
					continue
				self.holidays[mode] = [
					(x[0], x[1])
					for x in data['holidays'][modeName]
					if len(x) == 2
				]
			del data['holidays']
		else:
			log.error('no "holidays" key in holiday plugin "%s"' % self.file)
		###
		BaseJsonPlugin.setData(self, data)

	def updateCell(self, c):
		if not c.holiday:
			for mode in self.holidays:
				y, m, d = c.dates[mode]
				for hm, hd in self.holidays[mode]:
					if m == hm:
						if d == hd:
							c.holiday = True
							break
						elif (
							self.lastDayMerge and
							d == hd - 1 and
							hd >= calTypes[mode].minMonthLen
						):
							ny, nm, nd = jd_to(c.jd + 1, mode)
							if (ny, nm) > (y, m):
								c.holiday = True
								break

	def exportToIcs(self, fileName, startJd, endJd):
		currentTimeStamp = strftime(icsTmFormat)
		icsText = icsHeader
		for jd in range(startJd, endJd):
			isHoliday = False
			for mode in self.holidays.keys():
				myear, mmonth, mday = jd_to(jd, mode)
				if (mmonth, mday) in self.holidays[mode]:
					isHoliday = True
					break
			if isHoliday:
				gyear, gmonth, gday = jd_to(jd, DATE_GREG)
				gyear_next, gmonth_next, gday_next = jd_to(jd + 1, DATE_GREG)
				#######
				icsText += '\n'.join([
					'BEGIN:VEVENT'
					'CREATED:%s' % currentTimeStamp,
					'LAST-MODIFIED:%s' % currentTimeStamp,
					'DTSTART;VALUE=DATE:%.4d%.2d%.2d' % (
						gyear,
						gmonth,
						gday,
					),
					'DTEND;VA0LUE=DATE:%.4d%.2d%.2d' % (
						gyear_next,
						gmonth_next,
						gday_next,
					),
					'CATEGORIES:Holidays',
					'TRANSP:TRANSPARENT',
					# TRANSPARENT because being in holiday time,
					# does not make you busy!
					# see http://www.kanzaki.com/docs/ical/transp.html
					'SUMMARY:%s' % _('Holiday'),
					'END:VEVENT',
				])
		icsText += 'END:VCALENDAR\n'
		open(fileName, 'w').write(icsText)

	#def getJdList(self, startJd, endJd):


@registerPlugin
class YearlyTextPlugin(BaseJsonPlugin):
	name = 'yearlyText'
	params = BaseJsonPlugin.params + (
		'dataFile',
	)

	def __init__(self, _file):
		BaseJsonPlugin.__init__(
			self,
			_file,
		)
		self.dataFile = ''

	def setData(self, data):
		if 'dataFile' in data:
			self.dataFile = getPlugPath(data['dataFile'])
			del data['dataFile']
		else:
			log.error(
				'no "dataFile" key in yearly text plugin "%s"' % self.file
			)
		####
		BaseJsonPlugin.setData(self, data)

	def clear(self):
		self.yearlyData = []

	def load(self):
		#print('YearlyTextPlugin(%s).load()'%self._file)
		yearlyData = []
		for j in range(12):
			monthDb = []
			for k in range(calTypes[self.mode].maxMonthLen):
				monthDb.append('')
			yearlyData.append(monthDb)
		# last item is a dict of dates (y, m, d) and the description of day:
		yearlyData.append({})
		ext = splitext(self.dataFile)[1].lower()
		if ext == '.txt':
			sep = '\t'
			lines = open(self.dataFile).read().split('\n')
			for line in lines[1:]:
				line = line.strip()
				if not line:
					continue
				if line[0] == '#':
					continue
				parts = line.split('\t')
				if len(parts) < 2:
					log.error('bad plugin data line: %s' % line)
					continue
				date = parts[0].split('/')
				text = '\t'.join(parts[1:])
				if len(date) == 3:
					y = int(date[0])
					m = int(date[1])
					d = int(date[2])
					yearlyData[12][(y, m, d)] = text
				elif len(date) == 2:
					m = int(date[0])
					d = int(date[1])
					yearlyData[m - 1][d - 1] = text
				else:
					raise IOError('Bad line in database %s:\n%s' % (
						self.dataFile,
						line,
					))
		else:
			raise ValueError('invalid plugin dataFile extention "%s"' % ext)
		self.yearlyData = yearlyData

	def getText(self, year, month, day):
		yearlyData = self.yearlyData
		if not yearlyData:
			return ''
		mode = self.mode
		text = ''
		#if mode!=calTypes.primary:
		#	year, month, day = convert(year, month, day, calTypes.primary, mode)
		try:
			text = yearlyData[month - 1][day - 1]
		except:## KeyError or IndexError
			pass
		else:
			if self.show_date and text:
				text = '%s %s: %s' % (
					_(day),
					getMonthName(mode, month),
					text,
				)
		try:
			text2 = yearlyData[12][(year, month, day)]
		except:## KeyError or IndexError
			pass
		else:
			if text:
				text += '\n'
			if self.show_date:
				text2 = '%s %s %s: %s' % (
					_(day),
					getMonthName(mode, month, year),
					_(year),
					text2,
				)

			text += text2
		return text


@registerPlugin
class IcsTextPlugin(BasePlugin):
	name = 'ics'

	def __init__(self, _file, enable=True, show_date=False, all_years=False):
		title = splitext(_file)[0]
		self.ymd = None
		self.md = None
		self.all_years = all_years
		BasePlugin.__init__(
			self,
			_file,
		)
		self.mode = DATE_GREG
		self.title = title
		self.enable = enable
		self.show_date = show_date

	def clear(self):
		self.ymd = None
		self.md = None

	def load(self):
		lines = open(self.file).read().replace('\r', '').split('\n')
		n = len(lines)
		i = 0
		while True:
			try:
				if lines[i] == 'BEGIN:VEVENT':
					break
			except IndexError:
				log.error('bad ics file "%s"' % self.fpath)
				return
			i += 1
		SUMMARY = ''
		DESCRIPTION = ''
		DTSTART = None
		DTEND = None
		if self.all_years:
			md = {}
			while True:
				i += 1
				try:
					line = lines[i]
				except IndexError:
					break
				if line == 'END:VEVENT':
					if SUMMARY and DTSTART and DTEND:
						text = SUMMARY
						if DESCRIPTION:
							text += '\n%s' % DESCRIPTION
						for (y, m, d) in ymdRange(DTSTART, DTEND):
							md[(m, d)] = text
					else:
						log.error(
							'unsupported ics event' +
							', SUMMARY=%s' % SUMMARY +
							', DTSTART=%s' % DTSTART +
							', DTEND=%s' % DTEND								,
						)
					SUMMARY = ''
					DESCRIPTION = ''
					DTSTART = None
					DTEND = None
				elif line.startswith('SUMMARY:'):
					SUMMARY = line[8:].replace('\\,', ',').replace('\\n', '\n')
				elif line.startswith('DESCRIPTION:'):
					DESCRIPTION = line[12:].replace('\\,', ',').replace('\\n', '\n')
				elif line.startswith('DTSTART;'):
					#if not line.startswith('DTSTART;VALUE=DATE;'):
					#	log.error('unsupported ics line: %s'%line)
					#	continue
					date = line.split(':')[-1]
					#if len(date)!=8:
					#	log.error('unsupported ics line: %s'%line)
					#	continue
					try:
						DTSTART = (
							int(date[:4]),
							int(date[4:6]),
							int(date[6:8]),
						)
					except:
						log.error('unsupported ics line: %s' % line)
						myRaise()
						continue
				elif line.startswith('DTEND;'):
					#if not line.startswith('DTEND;VALUE=DATE;'):
					#	log.error('unsupported ics line: %s'%line)
					#	continue
					date = line.split(':')[-1]
					#if len(date)!=8:
					#	log.error('unsupported ics line: %s'%line)
					#	continue
					try:
						DTEND = (
							int(date[:4]),
							int(date[4:6]),
							int(date[6:8]),
						)
					except:
						log.error('unsupported ics line: %s' % line)
						myRaise()
						continue
			self.ymd = None
			self.md = md
		else:## not self.all_years
			ymd = {}
			while True:
				i += 1
				try:
					line = lines[i]
				except IndexError:
					break
				if line == 'END:VEVENT':
					if SUMMARY and DTSTART and DTEND:
						text = SUMMARY
						if DESCRIPTION:
							text += '\n%s' % DESCRIPTION
						for (y, m, d) in ymdRange(DTSTART, DTEND):
							ymd[(y, m, d)] = text
					SUMMARY = ''
					DESCRIPTION = ''
					DTSTART = None
					DTEND = None
				elif line.startswith('SUMMARY:'):
					SUMMARY = line[8:].replace('\\,', ',').replace('\\n', '\n')
				elif line.startswith('DESCRIPTION:'):
					DESCRIPTION = line[12:].replace('\\,', ',').replace('\\n', '\n')
				elif line.startswith('DTSTART;'):
					#if not line.startswith('DTSTART;VALUE=DATE;'):
					#	log.error('unsupported ics line: %s'%line)
					#	continue
					date = line.split(':')[-1]
					#if len(date)!=8:
					#	log.error('unsupported ics line: %s'%line)
					#	continue
					try:
						DTSTART = (int(date[:4]), int(date[4:6]), int(date[6:8]))
					except:
						log.error('unsupported ics line: %s' % line)
						myRaise()
						continue
				elif line.startswith('DTEND;'):
					#if not line.startswith('DTEND;VALUE=DATE;'):
					#	log.error('unsupported ics line: %s'%line)
					#	continue
					date = line.split(':')[-1]
					#if len(date)!=8:
					#	log.error('unsupported ics line: %s'%line)
					#	continue
					try:
						DTEND = (int(date[:4]), int(date[4:6]), int(date[6:8]))
					except:
						log.error('unsupported ics line: %s' % line)
						myRaise()
						continue
			self.ymd = ymd
			self.md = None

	def getText(self, y, m, d):
		if self.ymd:
			if (y, m, d) in self.ymd:
				if self.show_date:
					return '%s %s %s: %s' % (
						_(d),
						getMonthName(self.mode, m),
						_(y),
						self.ymd[(y, m, d)],
					)
				else:
					return self.ymd[(y, m, d)]
		if self.md:
			if (m, d) in self.md:
				if self.show_date:
					return '%s %s %s: %s' % (
						_(d),
						getMonthName(self.mode, m),
						_(y),
						self.ymd[(y, m, d)],
					)
				else:
					return self.md[(m, d)]
		return ''

	def open_configure(self):
		pass

	def open_about(self):
		pass

#class EveryDayTextPlugin(BaseJsonPlugin):
#class RandomTextPlugin(BaseJsonPlugin):


def loadPlugin(_file=None, **kwargs):
	if not _file:
		log.error('plugin file is empty!')
		return
	_file = getPlugPath(_file)
	if not isfile(_file):
		log.error('error while loading plugin "%s": no such file!\n' % _file)
		return
	ext = splitext(_file)[1].lower()
	####
	## should ics plugins require a json file too?
	## FIXME
	if ext == '.ics':
		return IcsTextPlugin(_file, **kwargs)
	####
	if ext != '.json':
		log.error(
			'unsupported plugin extention %s' % ext +
			', new style plugins have a json file'
		)
		return
	try:
		text = open(_file).read()
	except Exception as e:
		log.error(
			'error while reading plugin file "%s"' % _file +
			': %s' % e
		)
		return
	try:
		data = jsonToData(text)
	except Exception as e:
		log.error('invalid json file "%s"' % _file)
		return
	####
	data.update(kwargs)  # FIXME
	####
	try:
		name = data['type']
	except KeyError:
		log.error('invalid plugin "%s", no "type" key' % _file)
		return
	####
	if name == 'external':
		return loadExternalPlugin(_file, **data)
	####
	try:
		cls = pluginClassByName[name]
	except:
		log.error('invald plugin type "%s" in file "%s"' % (name, _file))
		return
	####
	for param in cls.essentialParams:
		if not data.get(param):
			log.error(
				'invalid plugin "%s"' % _file +
				': parameter "%s" is missing' % param
			)
			return
	####
	plug = cls(_file)
	plug.setData(data)
	####
	return plug
