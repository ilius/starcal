import os
from time import localtime

from scal3 import core, logger, ui
from scal3.date_utils import parseDroppedDate
from scal3.utils import urlToPath

__all__ = ["processDroppedDate"]


log = logger.get()


def processDroppedDate(text: str, dtype: str) -> tuple[int, int, int, int] | None:
	"""Returns (year: int, month: int, day: int, calType: int) or None."""
	# data_type: "UTF8_STRING", "application/x-color", "text/uri-list",
	if dtype == "UTF8_STRING":
		if text.startswith("file://"):
			path = urlToPath(text)
			try:
				t = os.stat(path).st_mtime  # modification time
			except OSError:
				log.error(f"Dropped invalid file {path!r}")
			else:
				y, m, d = localtime(t)[:3]
				# log.debug(f"Dropped file {path!r}, modification date: {y}/{m}/{d}")
				return (y, m, d, core.GREGORIAN)
		else:
			date = parseDroppedDate(text)
			if date:
				return date + (ui.dragRecMode,)
			# How to deny dragged object (to return to it's first location)
			# FIXME
			log.info(f"Dropped unknown text {text!r}")
			return None
			# log.debug(etime)
			# context.drag_status(gdk.DragAction.DEFAULT, etime)
			# context.drop_reply(False, etime)
			# context.drag_abort(etime)--Segmentation fault
			# context.drop_finish(False, etime)
			# context.finish(False, True, etime)
			# return True
	elif dtype == "text/uri-list":
		path = urlToPath(text)
		# print(f"{text = }, {path = }")
		try:
			t = os.stat(path).st_mtime  # modification time
		except OSError:
			log.error(f"Dropped invalid uri {path!r}")
			return None
		else:
			return localtime(t)[:3] + (core.GREGORIAN,)
	return None
