from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scal3 import logger

log = logger.get()

from scal3 import event_lib, ui
from scal3.event_lib import state as event_state
from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.event import makeWidget
from scal3.ui_gtk.event.utils import checkEventsReadOnly
from scal3.ui_gtk.utils import dialog_add_button

if TYPE_CHECKING:
	from scal3.event_lib.groups import EventGroup

__all__ = ["GroupEditorDialog"]


class GroupEditorDialog(gtk.Dialog):
	def __init__(self, group: EventGroup | None = None, **kwargs) -> None:
		checkEventsReadOnly()
		gtk.Dialog.__init__(self, **kwargs)
		self.isNew = group is None
		self.set_title(_("Add New Group") if self.isNew else _("Edit Group"))
		# self.connect("delete-event", lambda obj, e: self.destroy())
		# self.resize(800, 600)
		# ---
		dialog_add_button(
			self,
			imageName="dialog-cancel.svg",
			label=_("Cancel"),
			res=gtk.ResponseType.CANCEL,
		)
		dialog_add_button(
			self,
			imageName="dialog-ok.svg",
			label=_("_Save"),
			res=gtk.ResponseType.OK,
		)
		self.connect("response", lambda _w, _e: self.hide())
		# -------
		self.activeWidget = None
		# -------
		hbox = HBox()
		combo = gtk.ComboBoxText()
		for cls in event_lib.classes.group:
			combo.append_text(cls.desc)
		pack(hbox, gtk.Label(label=_("Group Type")))
		pack(hbox, combo)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.vbox, hbox)
		# ----
		if self.isNew:
			name = event_lib.classes.group[event_lib.defaultGroupTypeIndex].name
			self._group = ui.eventGroups.create(name)
			combo.set_active(event_lib.defaultGroupTypeIndex)
		else:
			self._group = group
			combo.set_active(event_lib.classes.group.names.index(group.name))
		self.activeWidget = None
		combo.connect("changed", self.typeChanged)
		self.comboType = combo
		self.vbox.show_all()
		self.typeChanged()

	def dateModeChanged(self, combo: gtk.ComboBox) -> None:
		pass

	@staticmethod
	def getNewGroupTitle(baseTitle: str) -> str:
		usedTitles = {group.title for group in ui.eventGroups}
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
		group = ui.withFS(event_lib.classes.group[self.comboType.get_active()]())
		log.info(
			f"GroupEditorDialog: typeChanged: {self.activeWidget=}"
			f", new class: {group.name}",
		)
		if self.isNew:
			group.setRandomColor()
			if group.icon:
				self._group.icon = group.icon
		if not self.isNew:
			group.copyFrom(self._group)
		group.setId(self._group.id)
		if self.isNew:
			group.title = self.getNewGroupTitle(group.desc)
		self._group = group
		self.activeWidget = makeWidget(group)
		pack(self.vbox, self.activeWidget)
		self.activeWidget.show()

	def run(self) -> EventGroup | None:
		if self.activeWidget is None:
			return None
		if gtk.Dialog.run(self) != gtk.ResponseType.OK:
			return None
		self.activeWidget.updateVars()
		self._group.save()  # FIXME
		if self.isNew:
			event_state.lastIds.save()
		else:
			ui.eventGroups[self._group.id] = self._group  # FIXME
		ui.eventNotif.checkGroup(self._group)
		self.destroy()
		return self._group
