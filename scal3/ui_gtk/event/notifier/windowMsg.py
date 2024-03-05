from scal3.locale_man import tr as _
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.utils import (
	dialog_add_button,
	imageFromFile,
)


class WidgetClass(gtk.Entry):
	def __init__(self, notifier):
		self.notifier = notifier
		gtk.Entry.__init__(self)

	def updateWidget(self):
		self.set_text(self.notifier.extraMessage)

	def updateVars(self):
		self.notifier.extraMessage = self.get_text()


def hideWindow(_widget, dialog):
	dialog.hide()
	return True


def notify(notifier, finishFunc):  # FIXME
	event = notifier.event
	dialog = gtk.Dialog()
	####
	lines = []
	lines.append(event.getText())
	if notifier.extraMessage:
		lines.append(notifier.extraMessage)
	text = "\n".join(lines)
	####
	dialog.set_title(event.getText())
	####
	hbox = HBox(spacing=15)
	hbox.set_border_width(10)
	if event.icon:
		pack(hbox, imageFromFile(event.icon))
		dialog.set_icon_from_file(event.icon)
	label = gtk.Label(label=text)
	label.set_selectable(True)
	pack(hbox, label, 1, 1)
	pack(dialog.vbox, hbox)
	####
	okB = dialog_add_button(
		dialog,
		imageName="dialog-ok.svg",
		label=_("_Close"),
		res=gtk.ResponseType.OK,
	)
	okB.connect("clicked", hideWindow, dialog)
	####
	dialog.vbox.show_all()
	dialog.connect("response", lambda _w, _e: finishFunc())
	dialog.present()
