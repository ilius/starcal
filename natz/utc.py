import datetime

ZERO = datetime.timedelta(0)


class UTC(datetime.tzinfo):
	"""
	Optimized UTC implementation. It unpickles using the single module global
	instance defined beneath this class declaration.
	"""
	zone = "UTC"

	_utcoffset = ZERO
	_dst = ZERO
	_tzname = zone

	def fromutc(self, dt):
		if dt.tzinfo is None:
			return self.localize(dt)
		return super(utc.__class__, self).fromutc(dt)

	utcoffset = lambda self, dt: ZERO

	tzname = lambda self, dt: "UTC"

	dst = lambda self, dt: ZERO

	#def __reduce__(self):
	#	return _UTC, ()

	def localize(self, dt, is_dst=False):
		"""Convert naive time to local time"""
		if dt.tzinfo is not None:
			raise ValueError("Not naive datetime (tzinfo is already set)")
		return dt.replace(tzinfo=self)

	def normalize(self, dt, is_dst=False):
		"""Correct the timezone information on the given datetime"""
		if dt.tzinfo is self:
			return dt
		if dt.tzinfo is None:
			raise ValueError("Naive time - no tzinfo set")
		return dt.astimezone(self)

	__repr__ = lambda self: "natz.timezone(\'UTC\')"
	__str__ = lambda self: "UTC"
