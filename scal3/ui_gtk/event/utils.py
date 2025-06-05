from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.event_lib import ev
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk.drawing import newColorCheckPixbuf
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.utils import confirm, pixbufFromFile, showError

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventGroupType, EventType
	from scal3.ui_gtk import GdkPixbuf, gtk

__all__ = [
	"checkEventsReadOnly",
	"confirmEventTrash",
	"confirmEventsTrash",
	"eventTreeIconPixbuf",
	"eventWriteImageMenuItem",
	"eventWriteMenuItem",
	"menuItemFromEventGroup",
]


def confirmEventTrash(event: EventType, **kwargs) -> bool:
	return confirm(
		_(
			'Press Confirm if you want to move event "{eventSummary}" to {trashTitle}',
		).format(
			eventSummary=event.summary,
			trashTitle=ev.trash.title,
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
			trashTitle=ev.trash.title,
		),
		use_markup=True,
		**kwargs,
	)


def checkEventsReadOnly(doException: bool = True) -> bool:
	if ev.allReadOnly:
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
	item.set_sensitive(sensitive and not ev.allReadOnly)
	return item


def eventWriteImageMenuItem(*args, **kwargs) -> gtk.MenuItem:
	item = ImageMenuItem(*args, **kwargs)
	item.set_sensitive(not ev.allReadOnly)
	return item


def menuItemFromEventGroup(group: EventGroupType, **kwargs) -> gtk.MenuItem:
	return ImageMenuItem(
		group.title,
		pixbuf=newColorCheckPixbuf(
			group.color.rgb(),
			conf.menuEventCheckIconSize.v,
			group.enable,
		),
		**kwargs,
	)


def eventTreeIconPixbuf(icon: str | None) -> GdkPixbuf.Pixbuf | None:
	return pixbufFromFile(
		icon,
		conf.eventTreeIconSize.v,
	)
