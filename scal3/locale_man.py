#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.

from __future__ import annotations

from scal3 import logger
from scal3.property import Property

log = logger.get()

import typing

if typing.TYPE_CHECKING:
	import subprocess
	from collections.abc import Callable

import gettext
import json
import os
import string
from contextlib import suppress
from operator import attrgetter
from os.path import (
	isabs,
	isfile,
	join,
	splitext,
)

import mytz
from scal3.cal_types import calTypes
from scal3.config_utils import (
	loadModuleConfig,
	saveModuleConfig,
)
from scal3.dict_utils import sortDict
from scal3.path import (
	APP_NAME,
	confDir,
	pixDir,
	sourceDir,
)
from scal3.s_object import SObjTextModel
from scal3.utils import toStr

__all__ = [
	"addLRM",
	"cutText",
	"dateLocale",
	"digits",
	"floatEncode",
	"getAlphabet",
	"getAvailableDigitKeys",
	"getDigits",
	"getLocaleFirstWeekDay",
	"getMonthName",
	"getNeedRestartParams",
	"lang",
	"langDict",
	"langHasUppercase",
	"langSh",
	"loadTranslator",
	"localTz",
	"numDecode",
	"numEncode",
	"popenDefaultLang",
	"prepareLanguage",
	"rtl",
	"rtlSgn",
	"saveConf",
	"sysLangDefault",
	"textNumDecode",
	"textNumEncode",
	"tr",
]


# ----------------------------------------------------------

mytz.defaultTZ = mytz.UTC

localTz = mytz.gettz()
localTzStr = str(localTz)

# ----------------------------------------------------------

confPath = join(confDir, "locale.json")

lang = Property("")
enableNumLocale = Property(True)

confParams = {
	"lang": lang,
	"enableNumLocale": enableNumLocale,
}


def loadConf() -> None:
	loadModuleConfig(__name__)


def saveConf() -> None:
	saveModuleConfig(__name__)


# ----------------------------------------------------------

langDir = join(sourceDir, "conf", "lang")
# localeDir = "/usr/share/locale"

# point FIXME
digits = {
	"en": ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"),
	"ar": ("٠", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩"),
	"fa": ("۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"),
	"ur": ("۔", "١", "٢", "٣", "۴", "۵", "٦", "٧", "٨", "٩"),
	"hi": ("०", "१", "२", "३", "४", "५", "६", "७", "८", "९"),
	"th": ("๐", "๑", "๒", "๓", "๔", "๕", "๖", "๗", "๘", "๙"),
}

ascii_alphabet = string.ascii_letters
alphabet = ""


def getLangDigits(
	langShortArg: str,
) -> tuple[str, str, str, str, str, str, str, str, str, str]:
	d = digits.get(langShortArg)
	if d is not None:
		return d
	return digits["en"]


# ar: Aarbic   ar_* 	Arabic-indic				Arabic Contries
# fa: Persian  fa_IR	Eastern (Extended) Arabic-indic    Iran & Afghanintan
# ur: Urdu     ur_PK	(Eastern) Arabic-indic		Pakistan (& Afghanintan??)
# hi: Hindi    hi_IN	Devenagari					India
# th: Thai     th_TH	# ----------					Thailand

# Urdu digits is a combination of Arabic and Persian digits,
# except for Zero that is named ARABIC-INDIC DIGIT ZERO in unicode database

LRM = "\u200e"  # left to right mark
# RLM = "\u200f"  # right to left mark
ZWNJ = "\u200c"  # zero width non-joiner
ZWJ = "\u200d"  # zero width joiner

sysLangDefault = os.environ.get("LANG", "")

langDefault = ""
langActive = ""
# langActive==lang except when lang==""
# (in that case, langActive will be taken from system)
# langActive will not get changed while the program is running
# (because it needs to restart program to apply new language)
langSh = ""  # short language name, for example "en", "fa", "fr", ...
rtl = False  # right to left
langHasUppercase = True


# ----------------------------------------------------------

loadConf()

# ----------------------------------------------------------


def tr(s: str | int, *a, **ka) -> str:
	"""String translator function."""
	return numEncode(s, *a, **ka) if isinstance(s, int) else str(s)


class LangData(SObjTextModel):
	params = (
		"code",
		"name",
		"nativeName",
		"fileName",  # shortName
		"flag",  # flagFile
		"rtl",
		"hasUppercase",
		"timeZoneList",
	)

	def __init__(self, _file: str) -> None:
		self.file = _file  # json file path
		# ----
		self.code = ""
		self.name = ""
		self.nativeName = ""
		self.fileName = ""
		self.flag = ""
		self.rtl = False
		self.hasUppercase = True
		self.transPath = ""
		# --
		self.timeZoneList: list[str] = []

	def setData(self, data: dict) -> None:
		SObjTextModel.setData(self, data)
		# -----
		for param in (
			"code",
			"name",
			"nativeName",
		):
			if not getattr(self, param):
				raise ValueError(
					f'missing or empty parameter "{param}"'
					f' in language file "{self.file}"',
				)
		# -----
		if not isabs(self.flag):
			self.flag = join(pixDir, "flags", self.flag)
		# -----
		transPath = ""
		if self.fileName:
			path = join(sourceDir, "locale.d", self.fileName + ".mo")
			# log.debug(f"{path=}")
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


# ----------------------------------------------------------


langDict = {}
try:
	with open(join(langDir, "default"), encoding="utf-8") as fp:
		langDefault = fp.read().strip()
except Exception as e:
	log.error(f"failed to read default lang file: {e}")


langFileList = []
with open(join(langDir, "list"), encoding="utf-8") as fp:
	for line in fp:
		line = line.strip()  # noqa: PLW2901
		if line.startswith("#"):
			continue
		langFileList.append(line)


for fname in langFileList:
	_fname_nox, ext = splitext(fname)
	ext = ext.lower()
	if ext != ".json":
		continue
	fpath = join(langDir, fname)
	try:
		with open(fpath, encoding="utf-8") as fp:
			data = json.loads(fp.read())
	except Exception:
		log.error(f"failed to load json file {fpath}")
		raise
	langObj = LangData(fpath)
	langObj.setData(data)
	langDict[langObj.code] = langObj
	# ---
	if localTzStr in langObj.timeZoneList:
		langDefault = langObj.code


# maybe sort by "code" or "nativeName"
langDict = sortDict(langDict, attrgetter("name"))


def popen_output(cmd: list[str] | str) -> str:
	import subprocess

	return subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]  # noqa: S603


def getLocaleFirstWeekDay() -> int:
	return int(popen_output(["locale", "first_weekday"])) - 1


def prepareLanguage() -> str:
	global langActive, langSh, rtl, langHasUppercase
	if lang.v == "":  # noqa: PLC1901
		# langActive = locale.setlocale(locale.LC_ALL, "")
		langActive = sysLangDefault
		if langActive not in langDict:
			langActive = langDefault
		# os.environ["LANG"] = langActive
	elif lang.v in langDict:
		# try:
		# 	lang.v = locale.setlocale(locale.LC_ALL, locale.normalize(lang))
		# except locale.Error:
		# lang.v = lang.lower()
		# lines = popen_output("locale -a").split("\n")  # FIXME
		# for line in lines:
		# 	if line.lower().starts(lang.v)
		# locale.setlocale(locale.LC_ALL, lang) # lang.v = locale.setlocale(...
		langActive = lang.v
		os.environ["LANG"] = lang.v
	else:  # not lang in langDict
		# locale.setlocale(locale.LC_ALL, langDefault) # lang.v = locale.setlocale(...
		lang.v = langDefault
		langActive = langDefault
		os.environ["LANG"] = langDefault
	langSh = langActive.split("_")[0]
	# sysRtl = (popen_output(["locale", "cal_direction"])=="3\n")  # FIXME
	rtl = langDict[langActive].rtl
	langHasUppercase = langDict[langActive].hasUppercase
	return langSh


def loadTranslator() -> Callable:
	global tr
	transObj = None
	langObj = langDict[langActive]
	if langObj.transPath:
		try:
			with open(langObj.transPath, "rb") as fp:
				transObj = gettext.GNUTranslations(fp)
		except Exception:
			log.exception("")
	if transObj:

		def tr(s, *a, nums=False, ctx=None, default=None, **ka):
			orig = s
			if isinstance(s, int | float):
				s = numEncode(s, *a, **ka)
			else:
				# pgettext is added in Python 3.8
				# even the word "context" does not exist in docs of 3.7
				# https://docs.python.org/3.7/library/gettext.html
				if ctx and hasattr(transObj, "pgettext"):
					s = toStr(transObj.pgettext(ctx, s))
				else:
					s = toStr(transObj.gettext(s))
				if default is not None and s == orig:
					s = default
				if a:
					s %= a
				if ka:
					s %= ka
				if nums:
					s = textNumEncode(s)
			return s

	else:

		def tr(s, *_a, **_ka):
			return str(s)

	return tr


def rtlSgn() -> int:
	return 1 if rtl else -1


def getMonthName(
	calType: int,
	month: int,
	year: int | None = None,
	abbreviate: bool = False,
) -> str:
	module, ok = calTypes[calType]
	if not ok:
		raise RuntimeError(f"cal type '{calType}' not found")
	if abbreviate:
		return module.getMonthNameAb(tr, month, year)
	return tr(module.getMonthName(month, year))


def getNumSep() -> str:
	return tr(".", ctx="number formatting") if enableNumLocale else "."


def getDigits() -> tuple[str, str, str, str, str, str, str, str, str, str]:
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


def getAvailableDigitKeys() -> set[str]:
	keys = set(digits["en"])
	if langSh != "en":
		locDigits = digits.get(langSh)
		if locDigits is not None:
			keys.update(locDigits)
	return keys


def numEncode(
	num: int,
	localeMode: str | int | None = None,
	fillZero: int = 0,
	negEnd: bool = False,
) -> str:
	if not enableNumLocale:
		localeMode = "en"
	if localeMode is None:
		localeMode = langSh
	elif isinstance(localeMode, int):  # noqa: SIM102
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
		return str(num)
	neg = num < 0
	dig = getLangDigits(localeMode)
	res = ""
	for c in str(abs(num)):
		if c == ".":
			res += getNumSep()
		else:
			res += dig[int(c)]
	if fillZero > 0:
		res = res.rjust(fillZero, dig[0])
	if neg:
		if negEnd:
			res += "-"
		else:
			res = "-" + res
	return res


def textNumEncode(
	st: str,
	localeMode: str | int | None = None,
	changeSpecialChars: bool = True,
	changeDot: bool = False,
) -> str:
	if not enableNumLocale:
		localeMode = "en"
	if localeMode is None:
		localeMode = langSh
	elif isinstance(localeMode, int):  # noqa: SIM102
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
		except ValueError:  # noqa: PERF203
			if enableNumLocale:
				if c == ".":
					if changeDot:
						c = tr(c, ctx="number formatting")  # noqa: PLW2901
				elif c in {",", "_"}:
					if changeSpecialChars:
						c = tr(c)  # noqa: PLW2901
				elif c == "%":  # noqa: SIM102
					if changeSpecialChars:
						c = tr(c, ctx="number formatting")  # noqa: PLW2901
			res += c
		else:
			res += dig[i]
	return res


def floatEncode(
	st: str,
	localeMode: str | int | None = None,
):
	return textNumEncode(
		st,
		localeMode,
		changeSpecialChars=False,
		changeDot=True,
	)


def numDecode(numSt: str) -> int:
	numSt = numSt.strip()
	with suppress(ValueError):
		return int(numSt)
	numSt = toStr(numSt)
	tryLangs = list(digits)
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
				except ValueError:
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
		except ValueError:  # noqa: PERF203
			if ch == tr(".", ctx="number formatting"):
				textEn += "."
			elif ch == tr(","):
				textEn += ","
			elif ch == tr("_"):
				textEn += "_"
			else:
				# "-" is specially important
				textEn += ch
	return textEn


def dateLocale(year: int, month: int, day: int) -> str:
	return (
		numEncode(year, fillZero=4)
		+ "/"
		+ numEncode(month, fillZero=2)
		+ "/"
		+ numEncode(day, fillZero=2)
	)


def cutText(text: str, n: int) -> str:
	text = toStr(text)
	newText = text[:n]
	if len(text) > n and text[n] not in list(string.printable) + [ZWNJ]:
		with suppress(UnicodeDecodeError):
			newText += ZWJ
	return newText


def addLRM(text: str) -> str:
	return LRM + toStr(text)


def popenDefaultLang(*args, **kwargs) -> subprocess.Popen:
	from subprocess import Popen

	os.environ["LANG"] = sysLangDefault
	p = Popen(*args, **kwargs)  # noqa: S603
	os.environ["LANG"] = lang
	return p


def getNeedRestartParams() -> list[Property]:
	return [
		lang,
		enableNumLocale,
	]


# ----------------------------------------------

prepareLanguage()
loadTranslator()
