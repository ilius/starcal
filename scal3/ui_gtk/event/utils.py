from scal3 import ui
from scal3.event_lib import state as event_state
from scal3.event_lib.event_base import Event
from scal3.event_lib.groups import EventGroup
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import GdkPixbuf, gtk
from scal3.ui_gtk.drawing import newColorCheckPixbuf
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.utils import (
	confirm,
	pixbufFromFile,
	showError,
)

__all__ = [
	"checkEventsReadOnly",
	"confirmEventTrash",
	"confirmEventsTrash",
	"eventTreeIconPixbuf",
	"eventWriteImageMenuItem",
	"eventWriteMenuItem",
	"menuItemFromEventGroup",
]


def confirmEventTrash(event: Event, **kwargs) -> bool:
	return confirm(
		_(
			'Press Confirm if you want to move event "{eventSummary}" to {trashTitle}',
		).format(
			eventSummary=event.summary,
			trashTitle=ui.eventTrash.title,
		),
		**kwargs,
	)


def confirmEventsTrash(toTrashCount: int, deleteCount: int, **kwargs) -> bool:
	return confirm(
		_(
			"Press Confirm if you want to move {toTrashCount} events to {trashTitle}"
			", and delete {deleteCount} events from {trashTitle}",
		).format(
			toTrashCount=_(toTrashCount),
			deleteCount=_(deleteCount),
			trashTitle=ui.eventTrash.title,
		),
		use_markup=True,
		**kwargs,
	)


def checkEventsReadOnly(doException: bool = True) -> bool:
	if event_state.allReadOnly:
		error = (
			"Events are Read-Only because they are locked by "
			"another StarCalendar 3.x process"
		)
		showError(_(error))
		if doException:
			raise RuntimeError(error)
		return False
	return True


def eventWriteMenuItem(*args, sensitive: bool = True, **kwargs) -> gtk.MenuItem:
	item = ImageMenuItem(*args, **kwargs)
	item.set_sensitive(sensitive and not event_state.allReadOnly)
	return item


def eventWriteImageMenuItem(*args, **kwargs) -> gtk.MenuItem:
	item = ImageMenuItem(*args, **kwargs)
	item.set_sensitive(not event_state.allReadOnly)
	return item


def menuItemFromEventGroup(group: EventGroup, **kwargs) -> gtk.MenuItem:
	return ImageMenuItem(
		group.title,
		pixbuf=newColorCheckPixbuf(
			group.color,
			conf.menuEventCheckIconSize.v,
			group.enable,
		),
		**kwargs,
	)


def eventTreeIconPixbuf(icon: str) -> GdkPixbuf.Pixbuf:
	return pixbufFromFile(
		icon,
		conf.eventTreeIconSize.v,
	)
