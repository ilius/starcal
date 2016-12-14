from os.path import join, split, splitext

from scal3.path import deskDir
from scal3.json_utils import *
from scal3 import core
from scal3.core import DATE_GREG
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import dialog_add_button
from scal3.ui_gtk.mywidgets.dialog import MyDialog
from scal3.ui_gtk.event.common import GroupsTreeCheckList


class SingleGroupExportDialog(gtk.Dialog, MyDialog):
	def __init__(self, group, **kwargs):
		self._group = group
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_('Export Group'))
		####
		dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), gtk.ResponseType.CANCEL)
		dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.ResponseType.OK)
		self.connect('response', lambda w, e: self.hide())
		####
		hbox = gtk.HBox()
		frame = gtk.Frame()
		frame.set_label(_('Format'))
		radioBox = gtk.VBox()
		##
		self.radioIcs = gtk.RadioButton(label='iCalendar')
		self.radioJsonCompact = gtk.RadioButton(label=_('Compact JSON (StarCalendar)'), group=self.radioIcs)
		self.radioJsonPretty = gtk.RadioButton(label=_('Pretty JSON (StarCalendar)'), group=self.radioIcs)
		##
		pack(radioBox, self.radioJsonCompact)
		pack(radioBox, self.radioJsonPretty)
		pack(radioBox, self.radioIcs)
		##
		self.radioJsonCompact.set_active(True)
		self.radioIcs.connect('clicked', self.formatRadioChanged)
		self.radioJsonCompact.connect('clicked', self.formatRadioChanged)
		self.radioJsonPretty.connect('clicked', self.formatRadioChanged)
		##
		frame.add(radioBox)
		pack(hbox, frame)
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self.vbox, hbox)
		########
		self.fcw = gtk.FileChooserWidget(action=gtk.FileChooserAction.SAVE)
		try:
			self.fcw.set_current_folder(deskDir)
		except AttributeError:## PyGTK < 2.4
			pass
		pack(self.vbox, self.fcw, 1, 1)
		####
		self.vbox.show_all()
		self.formatRadioChanged()
	def formatRadioChanged(self, widget=None):
		fpath = self.fcw.get_filename()
		if fpath:
			fname_nox, ext = splitext(split(fpath)[1])
		else:
			fname_nox, ext = '', ''
		if not fname_nox:
			fname_nox = core.fixStrForFileName(self._group.title)
		if self.radioIcs.get_active():
			if ext != '.ics':
				ext = '.ics'
		else:
			if ext != '.json':
				ext = '.json'
		self.fcw.set_current_name(fname_nox + ext)
	def save(self):
		fpath = self.fcw.get_filename()
		if self.radioJsonCompact.get_active():
			text = dataToCompactJson(ui.eventGroups.exportData([self._group.id]))
			open(fpath, 'w', encoding='utf-8').write(text)
		elif self.radioJsonPretty.get_active():
			text =  dataToPrettyJson(ui.eventGroups.exportData([self._group.id]))
			open(fpath, 'w', encoding='utf-8').write(text)
		elif self.radioIcs.get_active():
			ui.eventGroups.exportToIcs(fpath, [self._group.id])
	def run(self):
		if gtk.Dialog.run(self)==gtk.ResponseType.OK:
			self.waitingDo(self.save)
		self.destroy()


class MultiGroupExportDialog(gtk.Dialog, MyDialog):
	def __init__(self, **kwargs):
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_('Export'))
		self.vbox.set_spacing(10)
		####
		dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), gtk.ResponseType.CANCEL)
		dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.ResponseType.OK)
		####
		hbox = gtk.HBox()
		frame = gtk.Frame()
		frame.set_label(_('Format'))
		radioBox = gtk.VBox()
		##
		self.radioIcs = gtk.RadioButton(label='iCalendar')
		self.radioJsonCompact = gtk.RadioButton(label=_('Compact JSON (StarCalendar)'), group=self.radioIcs)
		self.radioJsonPretty = gtk.RadioButton(label=_('Pretty JSON (StarCalendar)'), group=self.radioIcs)
		##
		pack(radioBox, self.radioJsonCompact)
		pack(radioBox, self.radioJsonPretty)
		pack(radioBox, self.radioIcs)
		##
		self.radioJsonCompact.set_active(True)
		self.radioIcs.connect('clicked', self.formatRadioChanged)
		self.radioJsonCompact.connect('clicked', self.formatRadioChanged)
		self.radioJsonPretty.connect('clicked', self.formatRadioChanged)
		##
		frame.add(radioBox)
		pack(hbox, frame)
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self.vbox, hbox)
		########
		hbox = gtk.HBox(spacing=2)
		pack(hbox, gtk.Label(_('File')+':'))
		self.fpathEntry = gtk.Entry()
		self.fpathEntry.set_text(join(deskDir, 'events-%.4d-%.2d-%.2d'%core.getSysDate(DATE_GREG)))
		pack(hbox, self.fpathEntry, 1, 1)
		pack(self.vbox, hbox)
		####
		self.groupSelect = GroupsTreeCheckList()
		swin = gtk.ScrolledWindow()
		swin.add(self.groupSelect)
		swin.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
		pack(self.vbox, swin, 1, 1)
		####
		self.vbox.show_all()
		self.formatRadioChanged()
		self.resize(600, 600)
	def formatRadioChanged(self, widget=None):
		#self.dateRangeBox.set_visible(self.radioIcs.get_active())
		###
		fpath = self.fpathEntry.get_text()
		if fpath:
			fpath_nox, ext = splitext(fpath)
			if fpath_nox:
				if self.radioIcs.get_active():
					if ext != '.ics':
						ext = '.ics'
				else:
					if ext != '.json':
						ext = '.json'
				self.fpathEntry.set_text(fpath_nox + ext)
	def save(self):
		fpath = self.fpathEntry.get_text()
		activeGroupIds = self.groupSelect.getValue()
		if self.radioIcs.get_active():
			ui.eventGroups.exportToIcs(fpath, activeGroupIds)
		else:
			data = ui.eventGroups.exportData(activeGroupIds)
			## what to do with all groupData['info'] s? FIXME
			if self.radioJsonCompact.get_active():
				text = dataToCompactJson(data)
			elif self.radioJsonPretty.get_active():
				text = dataToPrettyJson(data)
			else:
				raise RuntimeError
			open(fpath, 'w', encoding='utf-8').write(text)
	def run(self):
		if gtk.Dialog.run(self)==gtk.ResponseType.OK:
			self.waitingDo(self.save)
		self.destroy()

