from scal3 import core
from scal3.locale_man import tr as _
from scal3 import event_lib
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import dialog_add_button
from scal3.ui_gtk.event import makeWidget
from scal3.ui_gtk.event.utils import checkEventsReadOnly

class GroupEditorDialog(gtk.Dialog):
	def __init__(self, group=None, **kwargs):
		checkEventsReadOnly()
		gtk.Dialog.__init__(self, **kwargs)
		self.isNew = (group is None)
		self.set_title(_('Add New Group') if self.isNew else _('Edit Group'))
		#self.connect('delete-event', lambda obj, e: self.destroy())
		#self.resize(800, 600)
		###
		dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), gtk.ResponseType.CANCEL)
		dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.ResponseType.OK)
		self.connect('response', lambda w, e: self.hide())
		#######
		self.activeWidget = None
		#######
		hbox = gtk.HBox()
		combo = gtk.ComboBoxText()
		for cls in event_lib.classes.group:
			combo.append_text(cls.desc)
		pack(hbox, gtk.Label(_('Group Type')))
		pack(hbox, combo)
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self.vbox, hbox)
		####
		if self.isNew:
			self._group = event_lib.classes.group[event_lib.defaultGroupTypeIndex]()
			combo.set_active(event_lib.defaultGroupTypeIndex)
		else:
			self._group = group
			combo.set_active(event_lib.classes.group.names.index(group.name))
		self.activeWidget = None
		combo.connect('changed', self.typeChanged)
		self.comboType = combo
		self.vbox.show_all()
		self.typeChanged()
	def dateModeChanged(self, combo):
		pass
	def getNewGroupTitle(self, baseTitle):
		usedTitles = [group.title for group in ui.eventGroups]
		if not baseTitle in usedTitles:
			return baseTitle
		i = 1
		while True:
			newTitle = baseTitle + ' ' + _(i)
			if newTitle in usedTitles:
				i += 1
			else:
				return newTitle
	def typeChanged(self, combo=None):
		if self.activeWidget:
			self.activeWidget.updateVars()
			self.activeWidget.destroy()
		cls = event_lib.classes.group[self.comboType.get_active()]
		group = cls()
		if self.isNew:
			group.setRandomColor()
			if group.icon:
				self._group.icon = group.icon
		if not self.isNew:
			group.copyFrom(self._group)
		group.setId(self._group.id)
		if self.isNew:
			group.title = self.getNewGroupTitle(cls.desc)
		self._group = group
		self.activeWidget = makeWidget(group)
		pack(self.vbox, self.activeWidget)
	def run(self):
		if self.activeWidget is None:
			return None
		if gtk.Dialog.run(self) != gtk.ResponseType.OK:
			return None
		self.activeWidget.updateVars()
		self._group.save()## FIXME
		if self.isNew:
			event_lib.lastIds.save()
		else:
			ui.eventGroups[self._group.id] = self._group ## FIXME
		self.destroy()
		return self._group

