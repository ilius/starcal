from scal3.cal_types import calTypes
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.datelabel import DateLabel
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import CustomizableCalObj

@registerSignals
class CalObj(gtk.HBox, CustomizableCalObj):
	_name = 'statusBar'
	desc = _('Status Bar')
	def __init__(self):
		from scal3.ui_gtk.mywidgets.resize_button import ResizeButton
		gtk.HBox.__init__(self)
		self.initVars()
		self.labelBox = gtk.HBox()
		pack(self, self.labelBox, 1, 1)
		resizeB = ResizeButton(ui.mainWin)
		pack(self, resizeB, 0, 0)
		if rtl:
			self.set_direction(gtk.TextDirection.LTR)
			self.labelBox.set_direction(gtk.TextDirection.LTR)
	def onConfigChange(self, *a, **kw):
		CustomizableCalObj.onConfigChange(self, *a, **kw)
		###
		for label in self.labelBox.get_children():
			label.destroy()
		###
		for mode in calTypes.active:
			label = DateLabel(None)
			label.mode = mode
			pack(self.labelBox, label, 1)
		self.show_all()
		###
		self.onDateChange()
	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)
		for i, label in enumerate(self.labelBox.get_children()):
			text = ui.cell.format(ud.dateFormatBin, label.mode)
			if i==0:
				text = '<b>%s</b>'%text
			label.set_label(text)

