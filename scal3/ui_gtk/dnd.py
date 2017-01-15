def processDroppedDate(text, dtype):
	## data_type: "UTF8_STRING", "application/x-color", "text/uri-list",
	if dtype == "UTF8_STRING":
		if text.startswith("file://"):
			path = core.urlToPath(text)
			try:
				t = os.stat(path).st_mtime ## modification time
			except OSError:
				print("Dropped invalid file \"%s\"" % path)
			else:
				y, m, d = localtime(t)[:3]
				#print("Dropped file "%s", modification time: %s/%s/%s"%(path, y, m, d))
				return (y, m, d, core.DATE_GREG)
		else:
			date = ui.parseDroppedDate(text)
			if date:
				return date + (ui.dragRecMode,)
			else:
				## Hot to deny dragged object (to return to it's first location)
				## FIXME
				print("Dropped unknown text \"%s\"" % text)
				#print(etime)
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
			print("Dropped invalid uri \"%s\"" % path)
			return True
		else:
			return localtime(t)[:3] + (core.DATE_GREG,)
