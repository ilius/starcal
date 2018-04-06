import os
import datetime
import dateutil.tz

class tzfile(datetime.tzinfo):
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


def gettz(*args, **kwargs):
	tz = dateutil.tz.gettz(*args, **kwargs)
	if tz is None:
		return None
	return tzfile(tz)

