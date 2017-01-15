from scal3.locale_man import tr as _
from scal3 import core
from scal3 import event_lib
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import confirm, showError, labelStockMenuItem
from scal3.ui_gtk.drawing import newColorCheckPixbuf


def confirmEventTrash(event, parent=None):
	return confirm(
		_("Press OK if you want to move event \"%s\" to %s") % (
			event.summary,
			ui.eventTrash.title,
		),
		parent=parent,
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


def eventWriteMenuItem(*args, **kwargs):
	item = labelStockMenuItem(*args, **kwargs)
	item.set_sensitive(not event_lib.allReadOnly)
	return item


def menuItemFromEventGroup(group):
	item = ImageMenuItem()
	item.set_label(group.title)
	##
	image = gtk.Image()
	image.set_from_pixbuf(newColorCheckPixbuf(
		group.color,
		20,
		group.enable,
	))
	item.set_image(image)
	return item
