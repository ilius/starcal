from __future__ import annotations

from scal3 import logger

log = logger.get()


from typing import TYPE_CHECKING

from scal3.locale_man import tr as _
from scal3.ui_gtk import Dialog, gtk, pack
from scal3.ui_gtk.utils import dialog_add_button, window_set_size_aspect

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventGroupType

__all__ = ["GroupConvertCalTypeDialog", "GroupSortDialog"]


class GroupSortDialog(Dialog):
	def __init__(
		self,
		group: EventGroupType,
		transient_for: gtk.Window | None = None,
	) -> None:
		self._group = group
		Dialog.__init__(self, transient_for=transient_for)
		self.set_title(_("Sort Events"))
		# ----
		dialog_add_button(
			self,
			res=gtk.ResponseType.CANCEL,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
		)
		dialog_add_button(
			self,
			res=gtk.ResponseType.OK,
			imageName="dialog-ok.svg",
			label=_("_Perform"),
		)
		# --
		self.connect("response", lambda _w, _e: self.hide())
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(
			hbox,
			gtk.Label(
				label=_('Sort events of group "{groupTitle}"').format(
					groupTitle=group.title,
				),
			),
		)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.vbox, hbox)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Based on") + " "))
		self.sortByNames = []
		self.sortByCombo = gtk.ComboBoxText()
		sortByDefault, sortBys = group.getSortBys()
		for item in sortBys:
			self.sortByNames.append(item[0])
			self.sortByCombo.append_text(item[1])
		self.sortByCombo.set_active(
			self.sortByNames.index(sortByDefault),
		)  # FIXME
		pack(hbox, self.sortByCombo)
		self.reverseCheck = gtk.CheckButton(label=_("Descending"))
		pack(hbox, self.reverseCheck)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.vbox, hbox)
		# ----
		self.vbox.show_all()

	def run2(self) -> bool:
		if Dialog.run(self) == gtk.ResponseType.OK:
			self._group.sort(
				self.sortByNames[self.sortByCombo.get_active()],
				self.reverseCheck.get_active(),
			)
			self._group.save()
			return True
		self.destroy()
		return False


class GroupConvertCalTypeDialog(Dialog):
	def __init__(
		self,
		group: EventGroupType,
		transient_for: gtk.Window | None = None,
	) -> None:
		from scal3.ui_gtk.mywidgets.cal_type_combo import CalTypeCombo

		self._group = group
		Dialog.__init__(self, transient_for=transient_for)
		self.set_title(_("Convert Calendar Type"))
		# ----
		dialog_add_button(
			self,
			res=gtk.ResponseType.CANCEL,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
		)
		dialog_add_button(
			self,
			res=gtk.ResponseType.OK,
			imageName="dialog-ok.svg",
			label=_("_Perform"),
		)
		# --
		self.connect("response", lambda _w, _e: self.hide())
		# ----
		label = gtk.Label(
			label=_(
				"This is going to convert calendar types of all events inside "
				'group "{groupTitle}" to a specific type. This operation does not work '
				"for Yearly events and also some of Custom events. You have to "
				"edit those events manually to change calendar type.",
			).format(groupTitle=group.title),
		)
		label.set_line_wrap(True)
		label.set_yalign(0.5)
		pack(self.vbox, label, 1, 1)
		# ---
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(hbox, gtk.Label(label=_("Calendar Type") + ":"))
		combo = CalTypeCombo()
		combo.set_active(group.calType)
		pack(hbox, combo)
		pack(hbox, gtk.Label(), 1, 1)
		self.calTypeCombo = combo
		pack(self.vbox, hbox)
		# ---
		pack(self.vbox, gtk.Label())
		# ----
		self.vbox.set_border_width(10)
		self.vbox.show_all()
		window_set_size_aspect(self, min_aspect=1.5, max_aspect=2.0)
		self.resize(100, 50)

	def perform(self) -> bool:
		if Dialog.run(self) != gtk.ResponseType.OK:
			self.destroy()
			return False
		calType = self.calTypeCombo.getActive()
		if calType is None:
			log.error("GroupConvertCalTypeDialog: calType is None")
			return False
		failedSummaryList = []
		for event in self._group:
			if event.changeCalType(calType):
				event.save()
			else:
				failedSummaryList.append(event.summary)
		if failedSummaryList:  # FIXME
			log.error(f"{failedSummaryList=}")
		return True
