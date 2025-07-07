from scal3.event_lib import ev
from scal3.locale_man import tr as _
from scal3.ui_gtk import Dialog, gtk, pack
from scal3.ui_gtk.event.utils import checkEventsReadOnly
from scal3.ui_gtk.mywidgets.icon import IconSelectButton
from scal3.ui_gtk.utils import (
	dialog_add_button,
	set_tooltip,
)

__all__ = ["TrashEditorDialog"]


class TrashEditorDialog(Dialog):
	def __init__(self, transient_for: gtk.Window | None = None) -> None:
		checkEventsReadOnly()
		Dialog.__init__(self, transient_for=transient_for)
		self.set_title(_("Edit Trash"))
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
		# --
		self.connect("response", lambda _w, _e: self.hide())
		# -------
		self.trash = ev.trash
		# --
		sizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# -------
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Title"))
		label.set_xalign(0)
		pack(hbox, label)
		sizeGroup.add_widget(label)
		self.titleEntry = gtk.Entry()
		pack(hbox, self.titleEntry, 1, 1)
		pack(self.vbox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		label = gtk.Label(label=_("Icon"))
		label.set_xalign(0)
		pack(hbox, label)
		sizeGroup.add_widget(label)
		self.iconSelect = IconSelectButton()
		pack(hbox, self.iconSelect)
		pack(hbox, gtk.Label(), 1, 1)
		pack(self.vbox, hbox)
		# ----
		hbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		self.addEventsToBeginningCheck = gtk.CheckButton(
			label=_("Add New Events to Beginning"),
		)
		set_tooltip(
			hbox,  # label or hbox?
			_("Add new events to beginning of event list, not to the end"),
		)
		pack(hbox, self.addEventsToBeginningCheck)
		pack(self.vbox, hbox)
		# ----
		self.vbox.show_all()
		self.updateWidget()

	def run(self) -> gtk.ResponseType:
		res = super().run()
		if res == gtk.ResponseType.OK:
			self.updateVars()
		self.destroy()
		return res

	def updateWidget(self) -> None:
		self.titleEntry.set_text(self.trash.title)
		if self.trash.icon:
			self.iconSelect.set_filename(self.trash.icon)
		self.addEventsToBeginningCheck.set_active(self.trash.addEventsToBeginning)

	def updateVars(self) -> None:
		self.trash.title = self.titleEntry.get_text()
		self.trash.icon = self.iconSelect.filename
		self.trash.addEventsToBeginning = self.addEventsToBeginningCheck.get_active()
		self.trash.save()
