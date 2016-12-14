from scal3 import core
from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.customize import CustomizableCalObj

@registerSignals
class CalObj(gtk.VBox, CustomizableCalObj):
	_name = 'pluginsText'
	desc = _('Plugins Text')
	def __init__(self):
		from scal3.ui_gtk.mywidgets.text_widgets import ReadOnlyTextView
		gtk.VBox.__init__(self)
		self.initVars()
		####
		self.textview = ReadOnlyTextView()
		self.textview.set_wrap_mode(gtk.WrapMode.WORD)
		self.textview.set_justification(gtk.Justification.CENTER)
		self.textbuff = self.textview.get_buffer()
		##
		self.expander = gtk.Expander()
		self.expander.connect('activate', self.expanderExpanded)
		if ui.pluginsTextInsideExpander:
			self.expander.add(self.textview)
			pack(self, self.expander)
			self.expander.set_expanded(ui.pluginsTextIsExpanded)
			self.textview.show()
		else:
			pack(self, self.textview)
	def optionsWidgetCreate(self):
		if self.optionsWidget:
			return
		self.optionsWidget = gtk.HBox()
		self.enableExpanderCheckb = gtk.CheckButton(_('Inside Expander'))
		self.enableExpanderCheckb.set_active(ui.pluginsTextInsideExpander)
		self.enableExpanderCheckb.connect('clicked', lambda check: self.setEnableExpander(check.get_active()))
		self.setEnableExpander(ui.pluginsTextInsideExpander)
		pack(self.optionsWidget, self.enableExpanderCheckb)
		####
		self.optionsWidget.show_all()
	def expanderExpanded(self, exp):
		ui.pluginsTextIsExpanded = not exp.get_expanded()
		ui.saveLiveConf()
	getWidget = lambda self: self.expander if ui.pluginsTextInsideExpander else self.textview
	def setText(self, text):
		if text:
			self.textbuff.set_text(text)
			self.getWidget().show()
		else:## elif self.get_property('visible')
			self.textbuff.set_text('')## forethought
			self.getWidget().hide()
	def setEnableExpander(self, enable):
		#print('setEnableExpander', enable)
		if enable:
			if not ui.pluginsTextInsideExpander:
				self.remove(self.textview)
				self.expander.add(self.textview)
				pack(self, self.expander)
				self.expander.show_all()
		else:
			if ui.pluginsTextInsideExpander:
				self.expander.remove(self.textview)
				self.remove(self.expander)
				pack(self, self.textview)
				self.textview.show()
		ui.pluginsTextInsideExpander = enable
		self.onDateChange()
	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)
		self.setText(ui.cell.pluginsText)

