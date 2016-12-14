from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import dialog_add_button
from scal3.ui_gtk.mywidgets.icon import IconSelectButton
from scal3.ui_gtk.event.utils import checkEventsReadOnly


class TrashEditorDialog(gtk.Dialog):
	def __init__(self, **kwargs):
		checkEventsReadOnly()
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_('Edit Trash'))
		#self.connect('delete-event', lambda obj, e: self.destroy())
		#self.resize(800, 600)
		###
		dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), gtk.ResponseType.CANCEL)
		dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.ResponseType.OK)
		##
		self.connect('response', lambda w, e: self.hide())
		#######
		self.trash = ui.eventTrash
		##
		sizeGroup = gtk.SizeGroup(gtk.SizeGroupMode.HORIZONTAL)
		#######
		hbox = gtk.HBox()
		label = gtk.Label(_('Title'))
		label.set_alignment(0, 0.5)
		pack(hbox, label)
		sizeGroup.add_widget(label)
		self.titleEntry = gtk.Entry()
		pack(hbox, self.titleEntry, 1, 1)
		pack(self.vbox, hbox)
		####
		hbox = gtk.HBox()
		label = gtk.Label(_('Icon'))
		label.set_alignment(0, 0.5)
		pack(hbox, label)
		sizeGroup.add_widget(label)
		self.iconSelect = IconSelectButton()
		pack(hbox, self.iconSelect)
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self.vbox, hbox)
		####
		self.vbox.show_all()
		self.updateWidget()
	def run(self):
		if gtk.Dialog.run(self)==gtk.ResponseType.OK:
			self.updateVars()
		self.destroy()
	def updateWidget(self):
		self.titleEntry.set_text(self.trash.title)
		self.iconSelect.set_filename(self.trash.icon)
	def updateVars(self):
		self.trash.title = self.titleEntry.get_text()
		self.trash.icon = self.iconSelect.filename
		self.trash.save()

