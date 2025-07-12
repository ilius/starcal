from __future__ import annotations

from datetime import datetime
from time import time as now
from typing import TYPE_CHECKING, Final

from scal3.option import Option

if TYPE_CHECKING:
	from collections.abc import Callable

__all__ = [
	"compressLongInt",
	"eventTextSep",
	"firstWeekDay",
	"getAbsWeekNumberFromJd",
	"getCompactTime",
	"getCurrentJd",
	"setTranslator",
	"weekDayName",
	"weekDayNameEnglish",
]

tr: Callable[[str], str] = str


def setTranslator(translator: Callable[[str], str]) -> None:
	global tr, weekDayName
	tr = translator
	weekDayName = (
		tr("Sunday"),
		tr("Monday"),
		tr("Tuesday"),
		tr("Wednesday"),
		tr("Thursday"),
		tr("Friday"),
		tr("Saturday"),
	)


# to separate summary from description for display
eventTextSep = ": "

type StrTuple7 = tuple[str, str, str, str, str, str, str]

weekDayNameEnglish: Final[StrTuple7] = (
	"Sunday",
	"Monday",
	"Tuesday",
	"Wednesday",
	"Thursday",
	"Friday",
	"Saturday",
)
weekDayName: StrTuple7 = weekDayNameEnglish

firstWeekDay: Final[Option[int]] = Option(0)


def getCurrentJd() -> int:
	return datetime.now().toordinal() + 1721425


def compressLongInt(num: int) -> str:
	"""Num must be less than 2**64."""
	from base64 import b64encode
	from struct import pack

	return (
		b64encode(
			pack("L", num % 2**64).rstrip(b"\x00"),
		)[:-3]
		.decode("ascii")
		.replace("/", "_")
	)


def getCompactTime(maxDays: int = 1000, minSec: float = 0.1) -> str:
	return compressLongInt(
		int(
			now() % (maxDays * 86400) / minSec,
		),
	)


def getWeekDateFromJd(jd: int) -> tuple[int, int]:
	"""Return (absWeekNumber, weekDay)."""
	return divmod(jd - firstWeekDay.v + 1, 7)


def getAbsWeekNumberFromJd(jd: int) -> int:
	return getWeekDateFromJd(jd)[0]
