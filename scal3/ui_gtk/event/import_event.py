import sys

from scal3.path import deskDir
from scal3.json_utils import *
from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.wizard import WizardWindow


class EventsImportWindow(WizardWindow):
	def __init__(self, manager):
		self.manager = manager
		WizardWindow.__init__(self, _('Import Events'))
		self.set_type_hint(gdk.WindowTypeHint.DIALOG)
		#self.set_property('skip-taskbar-hint', True)
		#self.set_modal(True)
		#self.set_transient_for(manager)
		#self.set_destroy_with_parent(True)
		self.resize(400, 200)

	class FirstStep(gtk.VBox):
		def __init__(self, win):
			gtk.VBox.__init__(self)
			self.set_spacing(20)
			self.win = win
			self.buttons = (
				(_('Cancel'), self.cancelClicked),
				(_('Next'), self.nextClicked),
			)
			####
			hbox = gtk.HBox(spacing=10)
			frame = gtk.Frame()
			frame.set_label(_('Format'))
			#frame.set_border_width(10)
			radioBox = gtk.VBox(spacing=10)
			radioBox.set_border_width(10)
			##
			self.radioJson = gtk.RadioButton(label=_('JSON (StarCalendar)'))
			#self.radioIcs = gtk.RadioButton(label='iCalendar', group=self.radioJson)
			##
			pack(radioBox, self.radioJson)
			#pack(radioBox, self.radioIcs)
			##
			self.radioJson.set_active(True)
			#self.radioJson.connect('clicked', self.formatRadioChanged)
			##self.radioIcs.connect('clicked', self.formatRadioChanged)
			##
			frame.add(radioBox)
			pack(hbox, frame, 0, 0, 10)
			pack(hbox, gtk.Label(''), 1, 1)
			pack(self, hbox)
			####
			hbox = gtk.HBox()
			pack(hbox, gtk.Label(_('File') + ':'))
			self.fcb = gtk.FileChooserButton(_('Import: Select File'))
			self.fcb.set_local_only(True)
			self.fcb.set_current_folder(deskDir)
			pack(hbox, self.fcb, 1, 1)
			pack(self, hbox)
			####
			self.show_all()

		def run(self):
			pass

		def cancelClicked(self, obj):
			self.win.destroy()

		def nextClicked(self, obj):
			fpath = self.fcb.get_filename()
			if not fpath:
				return
			if self.radioJson.get_active():
				format = 'json'
			#elif self.radioIcs.get_active():
			#	format = 'ics'
			else:
				return
			self.win.showStep(1, format, fpath)

	class SecondStep(gtk.VBox):
		def __init__(self, win):
			gtk.VBox.__init__(self)
			self.set_spacing(20)
			self.win = win
			self.buttons = (
				(_('Back'), self.backClicked),
				(_('Close'), self.closeClicked),
			)
			####
			self.textview = gtk.TextView()
			pack(self, self.textview, 1, 1)
			####
			self.show_all()

		def redirectStdOutErr(self):
			from scal3.ui_gtk.buffer import GtkBufferFile
			t_table = gtk.TextTagTable()
			tag_out = gtk.TextTag(name='output')
			t_table.add(tag_out)
			tag_err = gtk.TextTag(name='error')
			t_table.add(tag_err)
			self.buffer = self.textview.get_buffer()
			self.out_fp = GtkBufferFile(self.buffer, tag_out)
			sys.stdout = self.out_fp
			self.err_fp = GtkBufferFile(self.buffer, tag_err)
			sys.stderr = self.err_fp

		def restoreStdOutErr(self):
			sys.stdout = sys.__stdout__
			sys.stderr = sys.__stderr__

		def run(self, format, fpath):
			self.redirectStdOutErr()
			try:
				if format == 'json':
					try:
						text = open(fpath, 'r', encoding='utf-8').read()
					except Exception as e:
						sys.stderr.write(
							_(
								'Error in reading file'
							) + '\n%s\n' % e
						)
					else:
						try:
							data = jsonToData(text)
						except Exception as e:
							sys.stderr.write(
								_(
									'Error in loading JSON data'
								) + '\n%s\n' % e
							)
						else:
							try:
								newGroups = ui.eventGroups.importData(data)
							except Exception as e:
								sys.stderr.write(
									_(
										'Error in importing events'
									) + '\n%s\n' % e
								)
							else:
								for group in newGroups:
									self.win.manager.appendGroupTree(group)
								print(
									_(
										'%s groups imported successfully'
									) % _(len(newGroups))
								)
				else:
					raise ValueError('invalid format %r' % format)
			finally:
				self.restoreStdOutErr()

		def backClicked(self, obj):
			self.win.showStep(0)

		def closeClicked(self, obj):
			self.win.destroy()

	stepClasses = [
		FirstStep,
		SecondStep,
	]
