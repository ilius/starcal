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

log = logger.get()

import os
import sys
import typing
from math import ceil, floor
from typing import Any

if typing.TYPE_CHECKING:
	type Number = int | float

__all__ = [
	"FallbackLogger",
	"arange",
	"cmp",
	"findNearestIndex",
	"findNearestNum",
	"findWordByPos",
	"iceil",
	"ifloor",
	"numRangesDecode",
	"numRangesEncode",
	"restartLow",
	"s_join",
	"toBytes",
	"toStr",
	"urlToPath",
	"versionLessThan",
]


def ifloor(x: float) -> int:
	return floor(x)


def iceil(x: float) -> int:
	return ceil(x)


# replacement for numpy.core.multiarray.arange, in the lack of numpy
def arange(
	start: Number,
	stop: Number,
	step: Number,
) -> list[Number]:
	ls = []
	x = start
	stop -= 0.000001
	while x < stop:
		ls.append(x)
		x += step
	return ls


def toBytes(s: bytes | str) -> bytes:
	return s.encode("utf8") if isinstance(s, str) else bytes(s)


def toStr(s: bytes | str) -> str:
	return str(s, "utf8") if isinstance(s, bytes) else str(s)


def cmp(a: Any, b: Any) -> bool:
	return 0 if a == b else (1 if a > b else -1)


def versionLessThan(v0: str, v1: str) -> bool:
	from packaging import version

	return version.parse(v0) < version.parse(v1)


# Note: to check if saved preferences are older than a version:
# versionLessThan(core.prefVersion, v)


class FallbackLogger:
	def __init__(self) -> None:
		pass

	def error(self, text) -> None:  # noqa: PLR6301
		sys.stderr.write("ERROR: " + text + "\n")

	def warning(self, text) -> None:  # noqa: PLR6301
		log.info("WARNING: " + text)

	def debug(self, text) -> None:  # noqa: PLR6301
		log.info(text)

	def exception(self, prefix) -> None:  # noqa: PLR6301
		typ, value, tback = sys.exc_info()
		text = f"line {tback.tb_lineno}: {typ.__name__}: {value}\n"
		log.error(prefix + "\n" + text)


def restartLow() -> typing.NoReturn:
	"""Will not return from the function."""
	os.execl(
		sys.executable,
		sys.executable,
		*sys.argv,
	)


# a fully transparent object
class NullObj:
	def __setattr__(self, attr: str, value: Any) -> None:
		pass

	def __getattr__(self, attr: str) -> NullObj:
		return self

	def __call__(self, *_a, **_kw) -> NullObj:
		return self

	def __str__(self) -> str:
		return ""

	def __repr__(self) -> str:
		return ""

	def __int__(self) -> int:
		return 0


def s_join(ls: list[Any]) -> str:
	return " ".join([str(x) for x in ls])


def urlToPath(url: str) -> str:
	if not url.startswith("file://"):
		return url
	path = url[7:]
	if path.startswith("\r\n"):
		path = path[:-2]
	elif path.startswith("\r"):
		path = path[:-1]
	# here convert html unicode symbols to utf8 string:
	if "%" not in path:
		return path
	path2 = ""
	n = len(path)
	i = 0
	while i < n:
		if path[i] == "%" and i < n - 2:
			path2 += chr(int(path[i + 1 : i + 3], 16))
			i += 3
		else:
			path2 += path[i]
			i += 1
	return path2


def findNearestNum(lst: list[int], num: int) -> int:
	if not lst:
		return
	best = lst[0]
	for x in lst[1:]:
		if abs(x - num) < abs(best - num):
			best = x
	return best


def findNearestIndex(lst: list[int], num: int) -> int:
	if not lst:
		return
	index = 0
	count = len(lst)
	for i in range(1, count):
		if abs(lst[i] - num) < abs(lst[index] - num):
			index = i
	return index


def findWordByPos(text: str, pos: int) -> tuple[str, int]:
	"""Returns (word, startPos)."""
	if pos < 0:
		return "", -1
	if pos > len(text):
		return "", -1
	prevI = text.rfind(" ", 0, pos) + 1
	nextI = text.find(" ", pos)
	if nextI == -1:
		nextI = len(text)
	return text[prevI:nextI], prevI


def numRangesEncode(
	values: list[int | tuple[int, int] | list[int]],
	sep: str,
):
	parts = []
	for value in values:
		if isinstance(value, int):
			parts.append(str(value))
		elif isinstance(value, tuple | list):
			parts.append(f"{value[0]:d}-{value[1]:d}")
	return sep.join(parts)


def numRangesDecode(text: str) -> list[int | tuple[int, int]]:
	values = []
	for part in text.split(","):
		pparts = part.strip().split("-")
		try:
			if len(pparts) == 1:
				values.append(int(pparts[0]))
			elif len(pparts) > 1:
				values.append(
					(
						int(pparts[0]),
						int(pparts[1]),
					),
				)
			else:
				log.error(f"numRangesDecode: invalid range string '{part}'")
		except ValueError:
			log.exception("")
	return values
