import natz

from scal3.utils import myRaise
from scal3.locale_man import tr as _

from scal3.ui_gtk import *
from scal3.ui_gtk.utils import (
	window_set_size_aspect,
	dialog_add_button,
)
from scal3.ui_gtk.mywidgets import TextFrame
from scal3.ui_gtk.mywidgets.icon import IconSelectButton

class EventsBulkEditDialog(gtk.Dialog):
	def __init__(self, container, **kwargs):
		from scal3.ui_gtk.mywidgets.tz_combo import TimeZoneComboBoxEntry
		self._container = container
		gtk.Dialog.__init__(self, **kwargs)
		self.set_title(_('Bulk Edit Events'))
		####
		dialog_add_button(self, gtk.STOCK_CANCEL, _('_Cancel'), gtk.ResponseType.CANCEL)
		dialog_add_button(self, gtk.STOCK_OK, _('_OK'), gtk.ResponseType.OK)
		##
		self.connect('response', lambda w, e: self.hide())
		####
		try:
			title = container.title
		except AttributeError:
			event_count = len(container)
			msg = _('Here you are going to modify these %s events at once.') % event_count
		else:
			msg = _('Here you are going to modify all events inside group "%s" at once.') % title
		msg += ' '
		msg += _('You better make a backup from your events before doing this. Just right click on group and select "Export" (or a full backup: menu File -> Export)')
		msg += '\n\n'
		label = gtk.Label(msg)
		label.set_line_wrap(True)
		pack(self.vbox, label)
		####
		hbox = gtk.HBox()
		self.iconRadio = gtk.RadioButton(label=_('Icon'))
		pack(hbox, self.iconRadio, 1, 1)
		self.summaryRadio = gtk.RadioButton(label=_('Summary'), group=self.iconRadio)
		pack(hbox, self.summaryRadio, 1, 1)
		self.descriptionRadio = gtk.RadioButton(label=_('Description'), group=self.iconRadio)
		pack(hbox, self.descriptionRadio, 1, 1)
		self.timeZoneRadio = gtk.RadioButton(label=_('Time Zone'), group=self.iconRadio)
		pack(hbox, self.timeZoneRadio, 1, 1)
		pack(self.vbox, hbox)
		###
		self.iconRadio.connect('clicked', self.firstRadioChanged)
		self.summaryRadio.connect('clicked', self.firstRadioChanged)
		self.descriptionRadio.connect('clicked', self.firstRadioChanged)
		self.timeZoneRadio.connect('clicked', self.firstRadioChanged)
		####
		hbox = gtk.HBox()
		self.iconChangeCombo = gtk.ComboBoxText()
		self.iconChangeCombo.append_text('----')
		self.iconChangeCombo.append_text(_('Change'))
		self.iconChangeCombo.append_text(_('Change if empty'))
		pack(hbox, self.iconChangeCombo)
		pack(hbox, gtk.Label('  '))
		self.iconSelect = IconSelectButton()
		try:
			self.iconSelect.set_filename(container.icon)
		except AttributeError:
			pass
		pack(hbox, self.iconSelect)
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self.vbox, hbox)
		self.iconHbox = hbox
		####
		self.textVbox = gtk.VBox()
		###
		hbox = gtk.HBox()
		self.textChangeCombo = gtk.ComboBoxText()
		self.textChangeCombo.append_text('----')
		self.textChangeCombo.append_text(_('Add to beginning'))
		self.textChangeCombo.append_text(_('Add to end'))
		self.textChangeCombo.append_text(_('Replace text'))
		self.textChangeCombo.connect('changed', self.textChangeComboChanged)
		pack(hbox, self.textChangeCombo)
		pack(hbox, gtk.Label(''), 1, 1)
		## CheckButton(_('Regexp'))
		pack(self.textVbox, hbox)
		###
		self.textInput1 = TextFrame()
		pack(self.textVbox, self.textInput1, 1, 1)
		###
		hbox = gtk.HBox()
		pack(hbox, gtk.Label(_('with')))
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self.textVbox, hbox, 1, 1)
		self.withHbox = hbox
		###
		self.textInput2 = TextFrame()
		pack(self.textVbox, self.textInput2, 1, 1)
		####
		pack(self.vbox, self.textVbox, 1, 1)
		####
		hbox = gtk.HBox()
		self.timeZoneChangeCombo = gtk.ComboBoxText()
		self.timeZoneChangeCombo.append_text('----')
		self.timeZoneChangeCombo.append_text(_('Change'))
		self.timeZoneChangeCombo.append_text(_('Change if empty'))
		pack(hbox, self.timeZoneChangeCombo)
		pack(hbox, gtk.Label('  '))
		self.timeZoneInput = TimeZoneComboBoxEntry()
		pack(hbox, self.timeZoneInput)
		pack(hbox, gtk.Label(''), 1, 1)
		pack(self.vbox, hbox, 1, 1)
		self.timeZoneHbox = hbox
		####
		self.vbox.show_all()
		self.iconRadio.set_active(True)
		self.iconChangeCombo.set_active(0)
		self.textChangeCombo.set_active(0)
		self.firstRadioChanged()
		####
		window_set_size_aspect(self, 1.6)
	def firstRadioChanged(self, w=None):
		if self.iconRadio.get_active():
			self.iconHbox.show()
			self.textVbox.hide()
			self.timeZoneHbox.hide()
		elif self.timeZoneRadio.get_active():
			self.iconHbox.hide()
			self.textVbox.hide()
			self.timeZoneHbox.show()
		elif self.summaryRadio.get_active() or self.descriptionRadio.get_active():
			self.iconHbox.hide()
			self.textChangeComboChanged()
			self.timeZoneHbox.hide()
	def textChangeComboChanged(self, w=None):
		self.textVbox.show_all()
		chType = self.textChangeCombo.get_active()
		if chType==0:
			self.textInput1.hide()
			self.withHbox.hide()
			self.textInput2.hide()
		elif chType in (1, 2):
			self.withHbox.hide()
			self.textInput2.hide()
	def doAction(self):
		container = self._container
		if self.iconRadio.get_active():
			chType = self.iconChangeCombo.get_active()
			if chType!=0:
				icon = self.iconSelect.get_filename()
				for event in container:
					if not (chType==2 and event.icon):
						event.icon = icon
						event.afterModify()
						event.save()
		elif self.timeZoneRadio.get_active():
			chType = self.timeZoneChangeCombo.get_active()
			timeZone = self.timeZoneInput.get_text()
			if chType!=0:
				try:
					natz.timezone(timeZone)
				except:
					myRaise('Invalid Time Zone "%s"'%timeZone)
				else:
					for event in container:
						if not (chType==2 and event.timeZone):
							event.timeZone = timeZone
							event.afterModify()
							event.save()
		else:
			chType = self.textChangeCombo.get_active()
			if chType!=0:
				text1 = self.textInput1.get_text()
				text2 = self.textInput2.get_text()
				if self.summaryRadio.get_active():
					for event in container:
						if chType==1:
							event.summary = text1 + event.summary
						elif chType==2:
							event.summary = event.summary + text1
						elif chType==3:
							event.summary = event.summary.replace(text1, text2)
						event.afterModify()
						event.save()
				elif self.descriptionRadio.get_active():
					for event in container:
						if chType==1:
							event.description = text1 + event.description
						elif chType==2:
							event.description = event.description + text1
						elif chType==3:
							event.description = event.description.replace(text1, text2)
						event.afterModify()
						event.save()



