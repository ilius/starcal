__all__ = ["BadEventFile"]


class BadEventFile(Exception):  # FIXME
	"""Raised when an event file cannot be parsed or is invalid."""
