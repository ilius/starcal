#!/usr/bin/env python3
from scal3.locale_man import tr as _
from scal3 import core
from scal3 import event_lib
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	confirm,
	showError,
	pixbufFromFile,
)
from scal3.ui_gtk.menuitems import (
	ImageMenuItem,
)
from scal3.ui_gtk.drawing import newColorCheckPixbuf


def confirmEventTrash(event, **kwargs):
	return confirm(
		_(
			"Press OK if you want to move event \"{eventSummary}\""
			" to {trashTitle}"
		).format(
			eventSummary=event.summary,
			trashTitle=ui.eventTrash.title,
		),
		**kwargs
	)

def confirmEventsTrash(toTrashCount: int, deleteCount: int, **kwargs):
	return confirm(
		_(
			"Press OK if you want to move {toTrashCount} events to {trashTitle}"
			", and delete {deleteCount} events from {trashTitle}"
		).format(
			toTrashCount=_(toTrashCount),
			deleteCount=_(deleteCount),
			trashTitle=ui.eventTrash.title,
		),
		use_markup=True,
		**kwargs
	)

def checkEventsReadOnly(doException=True):
	if event_lib.allReadOnly:
		error = (
			"Events are Read-Only because they are locked by "
			"another StarCalendar 3.x process"
		)
		showError(_(error))
		if doException:
			raise RuntimeError(error)
		return False
	return True


def eventWriteMenuItem(*args, sensitive=True, **kwargs):
	item = ImageMenuItem(*args, **kwargs)
	item.set_sensitive(sensitive and not event_lib.allReadOnly)
	return item


def eventWriteImageMenuItem(*args, **kwargs):
	item = ImageMenuItem(*args, **kwargs)
	item.set_sensitive(not event_lib.allReadOnly)
	return item


def menuItemFromEventGroup(group, **kwargs):
	return ImageMenuItem(
		group.title,
		pixbuf=newColorCheckPixbuf(
			group.color,
			ui.menuEventCheckIconSize,
			group.enable,
		),
		**kwargs
	)


def eventTreeIconPixbuf(icon: str) -> GdkPixbuf.Pixbuf:
	return pixbufFromFile(
		icon,
		ui.eventTreeIconSize,
	)
