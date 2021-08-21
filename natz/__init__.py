#!/usr/bin/env python3

import logging
log = logging.getLogger("root")

import os
from os.path import split, join, islink, isfile
import datetime
import dateutil.tz

from typing import Optional

defaultTZ = None


class TimeZone(datetime.tzinfo):
	def __init__(self, tz):
		self._tz = tz
		if os.sep == "\\":
			self._name = tz.tzname(datetime.datetime.now())
		else:
			parts = tz._filename.split("/")
			self._name = "/".join(parts[-2:])

	def __str__(self):
		# This is the only function that we needed to override on dateutil.tz.tzfile
		return self._name

	def utcoffset(self, dt):
		return self._tz.utcoffset(dt)

	def dst(self, dt):
		return self._tz.dst(dt)

	def tzname(self, dt):
		return self._tz.tzname(dt)


def readEtcLocaltime():
	if not islink("/etc/localtime"):
		if isfile("/var/db/zoneinfo"):
			with open("/var/db/zoneinfo") as _file:
				tzname = _file.read().strip()
				return dateutil.tz.gettz(tzname)
		# 'zdump /etc/localtime' does not show timezone's name
		return dateutil.tz.tzfile("/etc/localtime")
	fpath = os.readlink("/etc/localtime")
	parts = fpath.split("/")
	try:
		index = parts.index("zoneinfo")
	except ValueError:
		log.info(f"Unexpected timezone file: {fpath}")
		return
	tzname = "/".join(parts[index + 1:])
	return dateutil.tz.gettz(tzname)


def gettz(*args, **kwargs) -> Optional[TimeZone]:
	tz = dateutil.tz.gettz(*args, **kwargs)
	if tz is None:
		return defaultTZ
	if tz._filename == "/etc/localtime":
		tz = readEtcLocaltime()
		if tz is None:
			return defaultTZ
	return TimeZone(tz)


UTC = gettz("UTC")
