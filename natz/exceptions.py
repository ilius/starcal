__all__ = [
	'UnknownTimeZoneError',
	'InvalidTimeError',
	'AmbiguousTimeError',
	'NonExistentTimeError',
]

class UnknownTimeZoneError(KeyError):
	pass


class InvalidTimeError(Exception):
	pass

class AmbiguousTimeError(InvalidTimeError):
	'''Exception raised when attempting to create an ambiguous wallclock time.

	At the end of a DST transition period, a particular wallclock time will
	occur twice (once before the clocks are set back, once after). Both
	possibilities may be correct, unless further information is supplied.

	See DstTzInfo.normalize() for more info
	'''
	pass


class NonExistentTimeError(InvalidTimeError):
	'''Exception raised when attempting to create a wallclock time that
	cannot exist.

	At the start of a DST transition period, the wallclock time jumps forward.
	The instants jumped over never occur.
	'''

