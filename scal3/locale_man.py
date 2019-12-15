#!/usr/bin/env python3
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

from scal3 import logger
log = logger.get()

import os
import string
from os.path import (
	join,
	isfile,
	isdir,
	isabs,
)
from os.path import splitext
import locale
import gettext

from typing import Optional, Union, Set, Tuple, List, Dict, Callable

import natz

from .path import *
from scal3.utils import StrOrderedDict
from scal3.utils import toBytes, toStr
from scal3.json_utils import *
from scal3.s_object import JsonSObj
from scal3.cal_types import calTypes

##########################################################

localTz = natz.gettz()
localTzStr = str(localTz)
# FIXME: looks like in some cases localTzStr == "etc/localtime"

##########################################################

confPath = join(confDir, "locale.json")

confParams = (
	"lang",
	"enableNumLocale",
)


def loadConf() -> None:
	loadModuleJsonConf(__name__)


def saveConf() -> None:
	saveModuleJsonConf(__name__)


##########################################################

langDir = join(sourceDir, "conf", "lang")
localeDir = "/usr/share/locale"

# point FIXME
digits = {
	"en": ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"),
	"ar": ("٠", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩"),
	"fa": ("۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"),
	"ur": ("۔", "١", "٢", "٣", "۴", "۵", "٦", "٧", "٨", "٩"),
	"hi": ("०", "१", "२", "३", "४", "५", "६", "७", "८", "९"),
	"th": ("๐", "๑", "๒", "๓", "๔", "๕", "๖", "๗", "๘", "๙"),
}

ascii_alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
alphabet = ""


def getLangDigits(langShortArg: str) -> Tuple[
	str, str, str, str, str,
	str, str, str, str, str,
]:
	d = digits.get(langShortArg)
	if d is not None:
		return d
	return digits["en"]


# ar: Aarbic   ar_* 	Arabic-indic				Arabic Contries
# fa: Persian  fa_IR	Eastern (Extended) Arabic-indic    Iran & Afghanintan
# ur: Urdu     ur_PK	(Eastern) Arabic-indic		Pakistan (& Afghanintan??)
# hi: Hindi    hi_IN	Devenagari					India
# th: Thai     th_TH	----------					Thailand

# Urdu digits is a combination of Arabic and Persian digits,
# except for Zero that is named ARABIC-INDIC DIGIT ZERO in unicode database

LRM = "\u200e"  # left to right mark
RLM = "\u200f"  # right to left mark
ZWNJ = "\u200c"  # zero width non-joiner
ZWJ = "\u200d"  # zero width joiner

sysLangDefault = os.environ.get("LANG", "")

langDefault = ""
lang = ""
langActive = ""
# langActive==lang except when lang==""
# (in that case, langActive will be taken from system)
# langActive will not get changed while the program is running
# (because it needs to restart program to apply new language)
langSh = ""  # short language name, for example "en", "fa", "fr", ...
rtl = False  # right to left

enableNumLocale = True

##########################################################

loadConf()

##########################################################


def tr(s: Union[str, int], *a, **ka) -> str:
	"""
	string translator function
	"""
	return numEncode(s, *a, **ka) if isinstance(s, int) else str(s)


class LangData(JsonSObj):
	params = (
		"code",
		"name",
		"nativeName",
		"fileName",  # shortName
		"flag",  # flagFile
		"rtl",
		"timeZoneList",
	)

	def __init__(self, _file: str) -> None:
		self.file = _file  # json file path
		####
		self.code = ""
		self.name = ""
		self.nativeName = ""
		self.fileName = ""
		self.flag = ""
		self.rtl = False
		self.transPath = ""
		##
		self.timeZoneList = []  # type: List[str]

	def setData(self, data: Dict):
		JsonSObj.setData(self, data)
		#####
		for param in (
			"code",
			"name",
			"nativeName",
		):
			if not getattr(self, param):
				raise ValueError(
					f"missing or empty parameter \"{param}\"" +
					f" in language file \"{self.file}\""
				)
		#####
		if not isabs(self.flag):
			self.flag = join(pixDir, "flags", self.flag)
		#####
		transPath = ""
		if self.fileName:
			path = join(sourceDir, "locale.d", self.fileName + ".mo")
			# log.debug(f"path={path}")
			if isfile(path):
				transPath = path
			else:
				# log.debug(f"-------- File {path!r} does not exists")
				for prefix in ("/usr", "/usr/local"):
					path = join(
						prefix,
						"share",
						"locale",
						self.fileName,
						"LC_MESSAGES",
						f"{APP_NAME}.mo",
					)
					if isfile(path):
						transPath = path
						break
		# log.debug(code, transPath)
		self.transPath = transPath

##########################################################


langDict = StrOrderedDict()
try:
	with open(join(langDir, "default")) as fp:
		langDefault = fp.read().strip()
except Exception as e:
	log.error(f"failed to read default lang file: {e}")


langFileList = []
with open(join(langDir, "list")) as fp:
	for line in fp:
		line = line.strip()
		if line.startswith("#"):
			continue
		langFileList.append(line)


for fname in langFileList:
	fname_nox, ext = splitext(fname)
	ext = ext.lower()
	if ext != ".json":
		continue
	fpath = join(langDir, fname)
	try:
		with open(fpath, encoding="utf-8") as fp:
			data = jsonToData(fp.read())
	except Exception as e:
		log.error(f"failed to load json file {fpath}")
		raise e
	langObj = LangData(fpath)
	langObj.setData(data)
	langDict[langObj.code] = langObj
	###
	if localTzStr in langObj.timeZoneList:
		langDefault = langObj.code


# maybe sort by "code" or "nativeName"
langDict.sort("name")


def popen_output(cmd: Union[List[str], str]) -> str:
	return Popen(cmd, stdout=subprocess.PIPE).communicate()[0]


def getLocaleFirstWeekDay() -> int:
	return int(popen_output(["locale", "first_weekday"])) - 1


def prepareLanguage() -> str:
	global lang, langActive, langSh, rtl
	if lang == "":
		# langActive = locale.setlocale(locale.LC_ALL, "")
		langActive = sysLangDefault
		if langActive not in langDict.keyList:
			langActive = langDefault
		# os.environ["LANG"] = langActive
	elif lang in langDict.keyList:
		# try:
		# 	lang = locale.setlocale(locale.LC_ALL, locale.normalize(lang))
		# except locale.Error:
		# lang = lang.lower()
		# lines = popen_output("locale -a").split("\n")  # FIXME
		# for line in lines:
		# 	if line.lower().starts(lang)
		# locale.setlocale(locale.LC_ALL, lang) ## lang = locale.setlocale(...
		langActive = lang
		os.environ["LANG"] = lang
	else:  # not lang in langDict.keyList
		# locale.setlocale(locale.LC_ALL, langDefault) ## lang = locale.setlocale(...
		lang = langDefault
		langActive = langDefault
		os.environ["LANG"] = langDefault
	langSh = langActive.split("_")[0]
	# sysRtl = (popen_output(["locale", "cal_direction"])=="3\n")  # FIXME
	rtl = langDict[langActive].rtl
	return langSh


def loadTranslator(ui_is_qt=False) -> Callable:
	global tr
	# FIXME: How to say to gettext that itself detects coding(charset)
	# from locale name and return a unicode object instead of str?
	# if isdir(localeDir):
	# 	transObj = gettext.translation(
	# 		APP_NAME,
	# 		localeDir,
	# 		languages=[langActive, langDefault],
	# 		fallback=True,
	# 	)
	# else:  # for example on windows (what about mac?)
	transObj = None
	langObj = langDict[langActive]
	if langObj.transPath:
		try:
			with open(langObj.transPath, "rb") as fp:
				transObj = gettext.GNUTranslations(fp)
		except Exception:
			log.exception("")
	if transObj:
		def tr(s, *a, nums=False, **ka):
			if isinstance(s, (int, float)):
				s = numEncode(s, *a, **ka)
			else:
				s = toStr(transObj.gettext(s))
				if ui_is_qt:
					s = s.replace("_", "&")
				if a:
					s = s % a
				if ka:
					s = s % ka
				if nums:
					s = textNumEncode(s)
			return s
		"""
		if ui_is_qt:## qt takes "&" instead of "_" as trigger
			tr = lambda s, *a, **ka: numEncode(s, *a, **ka) \
				if isinstance(s, int) \
				else transObj.gettext(toBytes(s)).replace("_", "&").decode("utf-8")
		else:
			tr = lambda s, *a, **ka: numEncode(s, *a, **ka) \
				if isinstance(s, int) \
				else transObj.gettext(toBytes(s)).decode("utf-8")
		"""
	else:
		def tr(s, *a, **ka):
			return str(s)
	return tr


def rtlSgn() -> int:
	return 1 if rtl else -1


def getMonthName(
	calType: int,
	month: int,
	year: Optional[int] = None,
	abbreviate: bool = False,
) -> str:
	module, ok = calTypes[calType]
	if not ok:
		raise RuntimeError(f"cal type '{calType}' not found")
	if abbreviate:
		return tr(module.getMonthNameAb(month, year))
	return tr(module.getMonthName(month, year))


def getNumSep() -> str:
	return tr(".") if enableNumLocale else "."


def getDigits() -> Tuple[str, str, str, str, str, str, str, str, str, str]:
	if enableNumLocale:
		d = digits.get(langSh)
		if d is not None:
			return d
	return digits["en"]


def getAlphabet() -> str:
	global alphabet
	if alphabet:
		return alphabet
	key = "__alphabet__"
	value = tr(key)
	if value == key:
		alphabet = ascii_alphabet
	else:
		alphabet = value.replace(" ", "")
	return alphabet


def getAvailableDigitKeys() -> Set[str]:
	keys = set(digits["en"])
	if langSh != "en":
		locDigits = digits.get(langSh)
		if locDigits is not None:
			keys.update(locDigits)
	return keys


def numEncode(
	num: int,
	localeMode: Union[None, str, int] = None,
	fillZero: int = 0,
	negEnd: bool = False,
) -> str:
	if not enableNumLocale:
		localeMode = "en"
	if localeMode is None:
		localeMode = langSh
	elif isinstance(localeMode, int):
		if langSh != "en":
			module, ok = calTypes[localeMode]
			if not ok:
				raise RuntimeError(f"cal type '{localeMode}' not found")
			try:
				localeMode = module.origLang
			except AttributeError:
				localeMode = langSh
	if localeMode == "en" or localeMode not in digits:
		if fillZero:
			return str(num).zfill(fillZero)
		else:
			return str(num)
	neg = (num < 0)
	dig = getLangDigits(localeMode)
	res = ""
	for c in str(abs(num)):
		if c == ".":
			if enableNumLocale:
				c = tr(".")
			res += c
		else:
			res += dig[int(c)]
	if fillZero > 0:
		res = res.rjust(fillZero, dig[0])
	if neg:
		if negEnd:
			res = res + "-"
		else:
			res = "-" + res
	return res


def textNumEncode(
	st: str,
	localeMode: Union[None, str, int] = None,
	changeSpecialChars: bool = True,
	changeDot: bool = False,
) -> str:
	if not enableNumLocale:
		localeMode = "en"
	if localeMode is None:
		localeMode = langSh
	elif isinstance(localeMode, int):
		if langSh != "en":
			module, ok = calTypes[localeMode]
			if not ok:
				raise RuntimeError(f"cal type '{localeMode}' not found")
			try:
				localeMode = module.origLang
			except AttributeError:
				localeMode = langSh
	dig = getLangDigits(localeMode)
	res = ""
	for c in toStr(st):
		try:
			i = int(c)
		except ValueError:
			if enableNumLocale:
				if c in (",", "_", "%"):
					if changeSpecialChars:
						c = tr(c)
				elif c == ".":
					if changeDot:
						c = tr(c)
			res += c
		else:
			res += dig[i]
	return res


def floatEncode(
	st: str,
	localeMode: Union[None, str, int] = None,
):
	return textNumEncode(
		st,
		localeMode,
		changeSpecialChars=False,
		changeDot=True,
	)


def numDecode(numSt: str) -> int:
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
		numEn = ""
		for dig in numSt:
			if dig == "-":
				numEn += dig
			else:
				try:
					numEn += str(tryLangDigits.index(dig))
				except ValueError as e:
					log.error(f"error in decoding num char {dig}")
					# raise e
					break
		else:
			return int(numEn)
	raise ValueError(f"invalid locale number {numSt}")


# converts "۱۲:۰۰, ۱۳" to "12:00, 13"
def textNumDecode(text: str) -> str:
	text = toStr(text)
	textEn = ""
	langDigits = getLangDigits(langSh)
	for ch in text:
		try:
			textEn += str(langDigits.index(ch))
		except ValueError:
			for sch in (",", "_", "."):
				if ch == tr(sch):
					ch = sch
					break
			textEn += ch
	return textEn


def dateLocale(year: int, month: int, day: int) -> str:
	return (
		numEncode(year, fillZero=4) +
		"/" +
		numEncode(month, fillZero=2) +
		"/" +
		numEncode(day, fillZero=2)
	)


def cutText(text: str, n: int) -> str:
	text = toStr(text)
	newText = text[:n]
	if len(text) > n:
		if text[n] not in list(string.printable) + [ZWNJ]:
			try:
				newText += ZWJ
			except UnicodeDecodeError:
				pass
	return newText


def addLRM(text: str) -> str:
	return LRM + toStr(text)


def popenDefaultLang(*args, **kwargs) -> "subprocess.Popen":
	global sysLangDefault, lang
	from subprocess import Popen
	os.environ["LANG"] = sysLangDefault
	p = Popen(*args, **kwargs)
	os.environ["LANG"] = lang
	return p


##############################################

prepareLanguage()
loadTranslator()
