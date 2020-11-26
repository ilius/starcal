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

import sys
import os
from math import floor, ceil

import typing
from typing import Union, Optional, Any, List, Tuple, Dict

Number = Union[int, float]


def ifloor(x: float) -> int:
	return int(floor(x))


def iceil(x: float) -> int:
	return int(ceil(x))


# replacement for numpy.core.multiarray.arange, in the lack of numpy
def arange(
	start: Number,
	stop: Number,
	step: Number,
) -> List[Number]:
	ls = []
	x = start
	stop -= 0.000001
	while x < stop:
		ls.append(x)
		x += step
	return ls


def toBytes(s: Union[bytes, str]) -> bytes:
	return s.encode("utf8") if isinstance(s, str) else bytes(s)


def toStr(s: Union[bytes, str]) -> str:
	return str(s, "utf8") if isinstance(s, bytes) else str(s)


def cmp(a: Any, b: Any) -> bool:
	return 0 if a == b else (1 if a > b else -1)


def versionLessThan(v0: str, v1: str) -> bool:
	from packaging import version
	return version.parse(v0) < version.parse(v1)


class FallbackLogger:
	def __init__(self):
		pass

	def error(self, text):
		sys.stderr.write("ERROR: " + text + "\n")

	def warning(self, text):
		log.info("WARNING: " + text)

	def debug(self, text):
		log.info(text)


def restartLow() -> typing.NoReturn:
	"""
	will not return from the function
	"""
	os.execl(
		sys.executable,
		sys.executable,
		*sys.argv
	)


class StrOrderedDict(dict):
	# A dict from strings to objects, with ordered keys
	# and some looks like a list
	def __init__(
		self,
		arg: Union[None, List, Tuple, Dict] = None,
		reorderOnModify: bool = True,
	) -> None:
		if arg is None:
			arg = []
		self.reorderOnModify = reorderOnModify
		if isinstance(arg, (list, tuple)):
			self.keyList = [item[0] for item in arg]
		elif isinstance(arg, dict):
			self.keyList = sorted(arg.keys())
		else:
			raise TypeError(
				f"StrOrderedDict: bad type for first argument: {type(arg)}"
			)
		dict.__init__(self, arg)

	def keys(self) -> List[str]:
		return self.keyList

	def values(self) -> List[Any]:
		return [
			dict.__getitem__(self, key)
			for key in self.keyList
		]

	def items(self) -> List[Tuple[str, Any]]:
		return [
			(key, dict.__getitem__(self, key))
			for key in self.keyList
		]

	def __getitem__(self, arg: Union[int, str, slice]) -> Any:
		if isinstance(arg, int):
			return dict.__getitem__(self, self.keyList[arg])
		elif isinstance(arg, str):
			return dict.__getitem__(self, arg)
		elif isinstance(arg, slice):  # not tested FIXME
			return StrOrderedDict([
				(key, dict.__getitem__(self, key))
				for key in self.keyList.__getitem__(arg)
			])
		else:
			raise ValueError(
				"Bad type argument given to StrOrderedDict.__getitem__" +
				f": {type(arg)}"
			)

	def __setitem__(self, arg: Union[int, str], value) -> None:
		if isinstance(arg, int):
			dict.__setitem__(self, self.keyList[arg], value)
		elif isinstance(arg, str):
			if arg in self.keyList:  # Modifying value for an existing key
				if reorderOnModify:
					self.keyList.remove(arg)
					self.keyList.append(arg)
			# elif isinstance(arg, slice):## ???????????? is not tested
			# 	#assert isinstance(value, StrOrderedDict)
			# 	if isinstance(value, StrOrderedDict):
			# 		for key in self.keyList.__getitem__(arg):
			else:
				self.keyList.append(arg)
			dict.__setitem__(self, arg, value)
		else:
			raise ValueError(
				"Bad type argument given to StrOrderedDict.__setitem__" +
				f": {type(item)}"
			)

	def __delitem__(self, arg: Union[int, str, slice]) -> None:
		if isinstance(arg, int):
			self.keyList.__delitem__(arg)
			dict.__delitem__(self, self.keyList[arg])
		elif isinstance(arg, str):
			self.keyList.remove(arg)
			dict.__delitem__(self, arg)
		elif isinstance(arg, slice):  # FIXME is not tested
			for key in self.keyList.__getitem__(arg):
				dict.__delitem__(self, key)
			self.keyList.__delitem__(arg)
		else:
			raise ValueError(
				"Bad type argument given to StrOrderedDict.__delitem__" +
				f": {type(arg)}"
			)

	# def pop(self, key: str) -> Any:  # FIXME
	# 	value = dict.pop(self, key)
	# 	del self.keyList[key]
	# 	return value

	def clear(self) -> None:
		self.keyList = []
		dict.clear(self)

	def append(self, key: str, value: Any):
		assert isinstance(key, str) and key not in self.keyList
		self.keyList.append(key)
		dict.__setitem__(self, key, value)

	def insert(self, index: int, key: str, value: Any):
		assert isinstance(key, str) and key not in self.keyList
		self.keyList.insert(index, key)
		dict.__setitem__(self, key, value)

	def sort(self, attr: Optional[str] = None) -> typing.Iterator:
		if attr is None:
			self.keyList.sort()
		else:
			self.keyList.sort(
				key=lambda k: getattr(dict.__getitem__(self, k), attr)
			)

	def __iter__(self):
		return self.keyList.__iter__()

	# lambda self: self.items().__iter__()
	def iteritems(self):
		for key in self.keyList:
			yield (key, dict.__getitem__(self, key))

	def __str__(self):
		return f"StrOrderedDict({self.items()!r})"
		# "StrOrderedDict{" + ", ".join([
		# 	repr(k) + ":" + repr(self[k])
		# 	for k in self.keyList
		# ]) + "}"

	def __repr__(self):
		return f"StrOrderedDict(({self.items()!r})"


# a fully transparent object
class NullObj:
	def __setattr__(self, attr: str, value: Any) -> None:
		pass

	def __getattr__(self, attr: str) -> "NullObj":
		return self

	def __call__(self, *args, **kwargs) -> "NullObj":
		return self

	def __str__(self) -> str:
		return ""

	def __repr__(self) -> str:
		return ""

	def __int__(self) -> int:
		return 0


def int_split(s: str) -> List[int]:
	return [int(x) for x in s.split()]


def s_join(ls: List[Any]) -> str:
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
			path2 += chr(int(path[i + 1:i + 3], 16))
			# OR: chr(eval("0x" + path[i + 1:i + 3]))
			i += 3
		else:
			path2 += path[i]
			i += 1
	return path2


def findNearestNum(lst: List[int], num: int) -> int:
	if not lst:
		return
	best = lst[0]
	for x in lst[1:]:
		if abs(x - num) < abs(best - num):
			best = x
	return best


def findNearestIndex(lst: List[int], num: int) -> int:
	if not lst:
		return
	index = 0
	count = len(lst)
	for i in range(1, count):
		if abs(lst[i] - num) < abs(lst[index] - num):
			index = i
	return index


def strFindNth(st: str, sub: str, n: int) -> int:
	pos = 0
	for i in range(n):
		pos = st.find(sub, pos + 1)
		if pos == -1:
			break
	return pos


def findWordByPos(text: str, pos: int) -> Tuple[str, int]:
	"returns (word, startPos)"
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
	values: List[Union[int, Tuple[int, int], List[int]]],
	sep: str,
):
	parts = []
	for value in values:
		if isinstance(value, int):
			parts.append(str(value))
		elif isinstance(value, (tuple, list)):
			parts.append(f"{value[0]:d}-{value[1]:d}")
	return sep.join(parts)


def numRangesDecode(text: str) -> List[Union[int, Tuple[int, int]]]:
	values = []
	for part in text.split(","):
		pparts = part.strip().split("-")
		try:
			if len(pparts) == 1:
				values.append(int(pparts[0]))
			elif len(pparts) > 1:
				values.append((
					int(pparts[0]),
					int(pparts[1]),
				))
			else:
				log.error(f"numRangesDecode: invalid range string '{part}'")
		except ValueError:
			log.exception("")
	return values


def inputDate(msg: str) -> Optional[Tuple[int, int, int]]:
	while True:
		try:
			date = input(msg)
		except KeyboardInterrupt:
			return
		if date.lower() == "q":
			return
		try:
			return dateDecode(date)
		except Exception as e:
			log.info(str(e))


def inputDateJd(msg: str) -> Optional[int]:
	date = inputDate(msg)
	if date:
		y, m, d = date
		return to_jd(y, m, d, GREGORIAN)
