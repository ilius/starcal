#!/usr/bin/env python3

from scal3 import logger
log = logger.get()


def processDroppedDate(text, dtype):
	# data_type: "UTF8_STRING", "application/x-color", "text/uri-list",
	if dtype == "UTF8_STRING":
		if text.startswith("file://"):
			path = core.urlToPath(text)
			try:
				t = os.stat(path).st_mtime ## modification time
			except OSError:
				log.error(f"Dropped invalid file {path!r}")
			else:
				y, m, d = localtime(t)[:3]
				# log.debug(f"Dropped file {path!r}, modification date: {y}/{m}/{d}")
				return (y, m, d, core.GREGORIAN)
		else:
			date = ui.parseDroppedDate(text)
			if date:
				return date + (ui.dragRecMode,)
			else:
				# How to deny dragged object (to return to it's first location)
				# FIXME
				log.info(f"Dropped unknown text {text!r}")
				# log.debug(etime)
				#context.drag_status(gdk.DragAction.DEFAULT, etime)
				#context.drop_reply(False, etime)
				#context.drag_abort(etime)##Segmentation fault
				#context.drop_finish(False, etime)
				#context.finish(False, True, etime)
				#return True
	elif dtype == "text/uri-list":
		path = core.urlToPath(selection.data)
		try:
			t = os.stat(path).st_mtime ## modification time
		except OSError:
			log.error(f"Dropped invalid uri {path!r}")
			return True
		else:
			return localtime(t)[:3] + (core.GREGORIAN,)
