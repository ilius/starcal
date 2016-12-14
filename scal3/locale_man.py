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

import os, string
from os.path import join, isfile, isdir, isabs
from os.path import splitext
import locale, gettext

from natz.local import get_localzone

from .path import *
from scal3.utils import StrOrderedDict, myRaise
from scal3.utils import toBytes, toStr
from scal3.json_utils import *
from scal3.s_object import JsonSObj
from scal3.cal_types import calTypes

#import codecs
#open = lambda filename, mode='r': codecs.open(filename, mode=mode, encoding='utf-8')

##########################################################

localTz = get_localzone()
localTzStr = str(localTz)

##########################################################

confPath = join(confDir, 'locale.json')

confParams = (
	'lang',
	'enableNumLocale',
)

def loadConf():
	loadModuleJsonConf(__name__)

def saveConf():
	saveModuleJsonConf(__name__)


##########################################################

langDir = join(rootDir, 'conf', 'lang')
localeDir = '/usr/share/locale'

## point FIXME
digits = {
	'en':('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'),
	'ar':('٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'),
	'fa':('۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'),
	'ur':('۔', '١', '٢', '٣', '۴', '۵', '٦', '٧', '٨', '٩'),
	'hi':('०', '१', '२', '३', '४', '५', '६', '७', '८', '९'),
	'th':('๐', '๑', '๒', '๓', '๔', '๕', '๖', '๗', '๘', '๙'),
}

def getLangDigits(langSh0):
	try:
		return digits[langSh0]
	except KeyError:
		return digits['en']

## ar: Aarbic   ar_*    Arabic-indic                       Arabic Contries
## fa: Persian  fa_IR   Eastern (Extended) Arabic-indic    Iran & Afghanintan
## ur: Urdu     ur_PK   (Eastern) Arabic-indic             Pakistan (& Afghanintan??)
## hi: Hindi    hi_IN   Devenagari                         India
## th: Thai     th_TH   ----------                         Thailand

## Urdu digits is a combination of Arabic and Persian digits, except for Zero that is
## named ARABIC-INDIC DIGIT ZERO in unicode database

LRM = '\u200e' ## left to right mark
RLM = '\u200f' ## right to left mark
ZWNJ = '\u200c' ## zero width non-joiner
ZWJ = '\u200d' ## zero width joiner

sysLangDefault = os.environ.get('LANG', '')

langDefault = ''
lang = ''
langActive = ''
## langActive==lang except when lang=='' (in that case, langActive will be taken from system)
## langActive will not get changed while the program is running
## (because it needs to restart program to apply new language)
langSh = '' ## short language name, for example 'en', 'fa', 'fr', ...
rtl = False ## right to left

enableNumLocale = True

##########################################################

loadConf()

##########################################################

## translator
tr = lambda s, *a, **ka: numEncode(s, *a, **ka) if isinstance(s, int) else str(s)

class LangData(JsonSObj):
	params = (
		'code',
		'name',
		'nativeName',
		'fileName',## shortName, ... FIXME
		'flag',## flagFile
		'rtl',
		'timeZoneList',
	)
	def __init__(self, _file):
		self.file = _file ## json file path
		####
		self.code = ''
		self.name = ''
		self.nativeName = ''
		self.fileName = ''
		self.flag = ''
		self.rtl = False
		self.transPath = ''
		##
		self.timeZoneList = []
	def setData(self, data):
		JsonSObj.setData(self, data)
		#####
		for param in (
			'code',
			'name',
			'nativeName',
		):
			if not getattr(self, param):
				raise ValueError('missing or empty parameter "%s" in language file "%s"'%(param, self.file))
		#####
		if not isabs(self.flag):
			self.flag = join(pixDir, 'flags', self.flag)
		#####
		transPath = ''
		if self.fileName:
			path = join(rootDir, 'locale.d', self.fileName+'.mo')
			#print('path=%s'%path)
			if isfile(path):
				transPath = path
			else:
				#print('-------- File %r does not exists'%path)
				for prefix in ('/usr', '/usr/local'):
					path = join(prefix, 'share', 'locale', self.fileName, 'LC_MESSAGES', '%s.mo'%APP_NAME)
					if isfile(path):
						transPath = path
						break
		#print(code, transPath)
		self.transPath = transPath



langDict = StrOrderedDict()

try:
	langDefault = open(join(langDir, 'default')).read().strip()
except Exception as e:
	print('failed to read default lang file: %s'%e)


for fname in os.listdir(langDir):
	fname_nox, ext = splitext(fname)
	ext = ext.lower()
	if ext != '.json':
		continue
	fpath = join(langDir, fname)
	try:
		data = jsonToData(open(fpath, encoding='utf-8').read())
	except Exception as e:
		print('failed to load json file %s'%fpath)
		raise e
	langObj = LangData(fpath)
	langObj.setData(data)
	langDict[langObj.code] = langObj
	###
	if localTzStr in langObj.timeZoneList:
		langDefault = langObj.code


langDict.sort('name') ## OR 'code' or 'nativeName' ????????????


def prepareLanguage():
	global lang, langActive, langSh, rtl
	if lang=='':
		#langActive = locale.setlocale(locale.LC_ALL, '')
		langActive = sysLangDefault
		if not langActive in langDict.keyList:
			langActive = langDefault
		#os.environ['LANG'] = langActive
	elif lang in langDict.keyList:
		#try:
		#	lang = locale.setlocale(locale.LC_ALL, locale.normalize(lang))
		#except locale.Error:
		#lang = lang.lower()
		#lines = popen_output('locale -a').split('\n') ## FIXME
		#for line in lines:
		#	if line.lower().starts(lang)
		#locale.setlocale(locale.LC_ALL, lang) ## lang = locale.setlocale(...
		langActive = lang
		os.environ['LANG'] = lang
	else:## not lang in langDict.keyList
		#locale.setlocale(locale.LC_ALL, langDefault) ## lang = locale.setlocale(...
		lang               = langDefault
		langActive         = langDefault
		os.environ['LANG'] = langDefault
	langSh = langActive.split('_')[0]
	#sysRtl = (popen_output(['locale', 'cal_direction'])=='3\n')## FIXME
	rtl = langDict[langActive].rtl
	return langSh


def loadTranslator(ui_is_qt=False):
	global tr
	## FIXME: How to say to gettext that itself detects coding(charset) from locale name and return a unicode object instead of str?
	#if isdir(localeDir):
	#	transObj = gettext.translation(APP_NAME, localeDir, languages=[langActive, langDefault], fallback=True)
	#else:## for example on windows (what about mac?)
	try:
		fd = open(langDict[langActive].transPath, 'rb')
	except:
		transObj = None
	else:
		transObj = gettext.GNUTranslations(fd)
	if transObj:
		def tr(s, *a, **ka):
			if isinstance(s, (int, float)):
				s = numEncode(s, *a, **ka)
			else:
				s = toStr(transObj.gettext(s))
				if ui_is_qt:
					s = s.replace('_', '&')
				if a:
					s = s % a
				if ka:
					s = s % ka
			return s
		'''
		if ui_is_qt:## qt takes "&" instead of "_" as trigger
			tr = lambda s, *a, **ka: numEncode(s, *a, **ka) \
				if isinstance(s, int) \
				else transObj.gettext(toBytes(s)).replace('_', '&').decode('utf-8')
		else:
			tr = lambda s, *a, **ka: numEncode(s, *a, **ka) \
				if isinstance(s, int) \
				else transObj.gettext(toBytes(s)).decode('utf-8')
		'''
	else:
		def tr(s, *a, **ka):
			return str(s)
	return tr

rtlSgn = lambda: 1 if rtl else -1

getMonthName = lambda mode, month, year=None: tr(calTypes[mode].getMonthName(month, year))

getNumSep = lambda: tr('.') if enableNumLocale else '.'

def getDigits():
	if enableNumLocale:
		try:
			return digits[langSh]
		except KeyError:
			pass
	return digits['en']

def getAvailableDigitKeys():
	keys = set(digits['en'])
	if langSh != 'en':
		try:
			locDigits = digits[langSh]
		except KeyError:
			pass
		else:
			keys.update(locDigits)
	return keys

def numEncode(num, mode=None, fillZero=0, negEnd=False):
	if not enableNumLocale:
		mode = 'en'
	if mode==None:
		mode = langSh
	elif isinstance(mode, int):
		if langSh != 'en':
			try:
				mode = calTypes[mode].origLang
			except AttributeError:
				mode = langSh
	if mode=='en' or not mode in digits:
		if fillZero:
			return '%.*d'%(fillZero, num)
		else:
			return '%d'%num
	neg = (num<0)
	dig = getLangDigits(mode)
	res = ''
	for c in str(abs(num)):
		if c=='.':
			if enableNumLocale:
				c = tr('.')
			res += c
		else:
			res += dig[int(c)]
	if fillZero>0:
		res = res.rjust(fillZero, dig[0])
	if neg:
		if negEnd:
			res = res + '-'
		else:
			res = '-' + res
	return res

def textNumEncode(st, mode=None, changeSpecialChars=True, changeDot=False):
	if not enableNumLocale:
		mode = 'en'
	if mode==None:
		mode = langSh
	elif isinstance(mode, int):
		if langSh != 'en':
			try:
				mode = calTypes[mode].origLang
			except AttributeError:
				mode = langSh
	dig = getLangDigits(mode)
	res = ''
	for c in toStr(st):
		try:
			i = int(c)
		except:
			if enableNumLocale:
				if c in (',', '_', '%'):## FIXME
					if changeSpecialChars:
						c = tr(c)
				elif c=='.':## FIXME
					if changeDot:
						c = tr(c)
			res += c
		else:
			res += dig[i]
	return res ## .encode('utf8')

floatEncode = lambda st, mode=None:\
	textNumEncode(st, mode, changeSpecialChars=False, changeDot=True)

def numDecode(numSt):
	numSt = numSt.strip()
	try:
		return int(numSt)
	except ValueError:
		pass
	numSt = toStr(numSt)
	tryLangs = list(digits.keys())
	if langSh in digits:
		tryLangs.remove(langSh)
		tryLangs.insert(0, langSh)
	for tryLang in tryLangs:
		tryLangDigits = digits[tryLang]
		numEn = ''
		for dig in numSt:
			if dig=='-':
				numEn += dig
			else:
				try:
					numEn += str(tryLangDigits.index(dig))
				except ValueError as e:
					print('error in decoding num char %s'%dig)
					#raise e
					break
		else:
			return int(numEn)
	raise ValueError('invalid locale number %s'%numSt)

def textNumDecode(text):## converts '۱۲:۰۰, ۱۳' to '12:00, 13'
	text = toStr(text)
	textEn = ''
	langDigits = getLangDigits(langSh)
	for ch in text:
		try:
			textEn += str(langDigits.index(ch))
		except ValueError:
			for sch in (',', '_', '.'):
				if ch == tr(sch):
					ch = sch
					break
			textEn += ch
	return textEn

dateLocale = lambda year, month, day:\
	numEncode(year, fillZero=4) + '/' + \
	numEncode(month, fillZero=2) + '/' + \
	numEncode(day, fillZero=2)

def cutText(text, n):
	text = toStr(text)
	newText = text[:n]
	if len(text) > n:
		if text[n] not in list(string.printable)+[ZWNJ]:
			try:
				newText += ZWJ
			except UnicodeDecodeError:
				pass
	return newText

addLRM = lambda text: LRM + toStr(text)

def popenDefaultLang(*args, **kwargs):
	global sysLangDefault, lang
	from subprocess import Popen
	os.environ['LANG'] = sysLangDefault
	p = Popen(*args, **kwargs)
	os.environ['LANG'] = lang
	return p

##############################################

prepareLanguage()
loadTranslator()


