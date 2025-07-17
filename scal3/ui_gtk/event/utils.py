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
	from scal3.ui_gtk.menuitems import ItemCallback

__all__ = [
	"checkEventsReadOnly",
	"confirmEventTrash",
	"confirmEventsTrash",
	"eventTreeIconPixbuf",
	"eventWriteImageMenuItem",
	"eventWriteMenuItem",
	"menuItemFromEventGroup",
]


def confirmEventTrash(
	event: EventType,
	transient_for: gtk.Window | None = None,
) -> bool:
	return confirm(
		_(
			'Press Confirm if you want to move event "{eventSummary}" to {trashTitle}',
		).format(
			eventSummary=event.summary,
			trashTitle=ev.trash.title,
		),
		transient_for=transient_for,
	)


def confirmEventsTrash(toTrashCount: int, deleteCount: int) -> bool:
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


def eventWriteMenuItem(
	label: str = "",
	imageName: str | None = None,
	func: ItemCallback | None = None,
	sensitive: bool = True,
) -> gtk.MenuItem:
	item = ImageMenuItem(
		label=label,
		imageName=imageName,
		func=func,
	)
	item.set_sensitive(sensitive and not ev.allReadOnly)
	return item


def eventWriteImageMenuItem(
	label: str = "",
	imageName: str | None = None,
	func: ItemCallback | None = None,
) -> gtk.MenuItem:
	item = ImageMenuItem(
		label=label,
		imageName=imageName,
		func=func,
	)
	item.set_sensitive(not ev.allReadOnly)
	return item


def menuItemFromEventGroup(
	group: EventGroupType,
	func: ItemCallback | None = None,
) -> gtk.MenuItem:
	return ImageMenuItem(
		label=group.title,
		func=func,
		pixbuf=newColorCheckPixbuf(
			group.color.rgb(),
			conf.menuEventCheckIconSize.v,
			group.enable,
		),
	)


def eventTreeIconPixbuf(icon: str | None) -> GdkPixbuf.Pixbuf | None:
	return pixbufFromFile(
		icon,
		conf.eventTreeIconSize.v,
	)
