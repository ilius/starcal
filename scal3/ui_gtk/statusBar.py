from scal3 import ui
from scal3.cal_types import calTypes
from scal3.color_utils import colorizeSpan
from scal3.locale_man import rtl
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import HBox, VBox, gtk, pack
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import CustomizableCalObj
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.mywidgets.label import SLabel

__all__ = ["CalObj"]


@registerSignals
class CalObj(gtk.Box, CustomizableCalObj):
	objName = "statusBar"
	desc = _("Status Bar")
	itemListCustomizable = False
	hasOptions = True
	optionsPageSpacing = 15

	def __init__(self, win):
		self.win = win
		from scal3.ui_gtk.mywidgets.resize_button import ResizeButton

		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.initVars()
		# ----
		self.labelBox = HBox()
		pack(self, self.labelBox, 1, 1)
		resizeB = ResizeButton(win)
		pack(self, resizeB, 0, 0)
		if rtl:
			self.set_direction(gtk.TextDirection.LTR)
			self.labelBox.set_direction(gtk.TextDirection.LTR)

	def onConfigChange(self, *a, **kw):
		CustomizableCalObj.onConfigChange(self, *a, **kw)
		# ---
		for label in self.labelBox.get_children():
			label.destroy()
		# ---
		activeCalTypes = calTypes.active
		if conf.statusBarDatesReverseOrder.v:
			activeCalTypes = reversed(activeCalTypes)  # to not modify calTypes.active
		for calType in activeCalTypes:
			label = SLabel()
			label.calType = calType
			label.set_direction(gtk.TextDirection.LTR)
			pack(self.labelBox, label, 1)
		self.show_all()
		# ---
		self.onDateChange()

	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)
		labels = self.labelBox.get_children()
		for label in labels:
			text = ui.cells.current.format(ud.dateFormatBin, label.calType)
			if label.calType == calTypes.primary:
				text = f"<b>{text}</b>"
			if conf.statusBarDatesColorEnable.v:
				text = colorizeSpan(text, conf.statusBarDatesColor.v)
			label.set_label(text)

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import (
			CheckColorPrefItem,
			CheckPrefItem,
			ColorPrefItem,
		)

		if self.optionsWidget:
			return self.optionsWidget
		# ----
		optionsWidget = VBox(spacing=10)
		# ----
		prefItem = CheckPrefItem(
			prop=conf.statusBarDatesReverseOrder,
			label=_("Reverse the order of dates"),
			live=True,
			onChangeFunc=self.onConfigChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		# ----
		prefItem = CheckColorPrefItem(
			CheckPrefItem(prop=conf.statusBarDatesColorEnable, label=_("Dates Color")),
			ColorPrefItem(prop=conf.statusBarDatesColor, useAlpha=True),
			live=True,
			onChangeFunc=self.onDateChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		# ----
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return self.optionsWidget
