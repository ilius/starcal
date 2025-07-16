from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scal3 import logger
from scal3.s_object import copyParams
from scal3.ui_gtk.event.group.base import makeGroupWidget

log = logger.get()
from scal3 import event_lib
from scal3.event_lib import ev
from scal3.locale_man import tr as _
from scal3.ui_gtk import Dialog, gtk, pack
from scal3.ui_gtk.event.utils import checkEventsReadOnly
from scal3.ui_gtk.utils import dialog_add_button

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventGroupType
	from scal3.ui_gtk.event.group.base import BaseWidgetClass

__all__ = ["GroupEditorDialog"]


class GroupEditorDialog(Dialog):
	def __init__(
		self,
		group: EventGroupType | None = None,
		transient_for: gtk.Window | None = None,
	) -> None:
		checkEventsReadOnly()
		Dialog.__init__(self, transient_for=transient_for)
		self.isNew = group is None
		self.set_title(_("Add New Group") if self.isNew else _("Edit Group"))
		# self.connect("delete-event", lambda obj, e: self.destroy())
		# self.resize(800, 600)
		# ---
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
			label=_("_Save"),
		)
		self.connect("response", lambda _w, _e: self.hide())
		# -------
		self.activeWidget: BaseWidgetClass | None = None
		# -------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		combo = gtk.ComboBoxText()
		for cls in event_lib.classes.group:
			combo.append_text(cls.desc)
		pack(hbox, gtk.Label(label=_("Group Type")))
		pack(hbox, combo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.vbox, hbox)
		# ----
		if group is None:
			name = event_lib.classes.group[event_lib.defaultGroupTypeIndex].name
			self._group = ev.groups.create(name)
			combo.set_active(event_lib.defaultGroupTypeIndex)
		else:
			self._group = group
			combo.set_active(event_lib.classes.group.names.index(group.name))
		combo.connect("changed", self.typeChanged)
		self.comboType = combo
		self.vbox.show_all()
		self.typeChanged()

	@staticmethod
	def getNewGroupTitle(baseTitle: str) -> str:
		usedTitles = {group.title for group in ev.groups}
		if baseTitle not in usedTitles:
			return baseTitle

		def makeTitle(n: int) -> str:
			return baseTitle + " " + _(n)

		num = 1
		while makeTitle(num) in usedTitles:
			num += 1
		return makeTitle(num)

	def typeChanged(self, _combo: Any = None) -> None:
		if self.activeWidget:
			self.activeWidget.updateVars()
			self.activeWidget.destroy()
		groupType: str = event_lib.classes.group.names[self.comboType.get_active()]
		group = ev.groups.create(groupType)
		log.info(
			f"GroupEditorDialog: typeChanged: {self.activeWidget=}"
			f", new class: {group.name}",
		)
		if self.isNew:
			group.setRandomColor()
			if group.icon:
				self._group.icon = group.icon
		if not self.isNew:
			copyParams(group, self._group)
		group.setId(self._group.id)
		if self.isNew:
			group.title = self.getNewGroupTitle(group.desc)
		self._group = group
		self.activeWidget = makeGroupWidget(group)
		assert self.activeWidget is not None
		pack(self.vbox, self.activeWidget)
		self.activeWidget.show()

	def run2(self) -> EventGroupType | None:
		if self.activeWidget is None:
			return None
		if Dialog.run(self) != gtk.ResponseType.OK:
			return None
		self.activeWidget.updateVars()
		group = self._group
		group.save()  # FIXME
		assert group.id is not None
		if self.isNew:
			ev.lastIds.save()
		else:
			ev.groups[group.id] = group  # FIXME
		ev.notif.checkGroup(group)
		self.destroy()
		return group
