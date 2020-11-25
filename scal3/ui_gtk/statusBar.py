#!/usr/bin/env python3

from scal3.color_utils import colorizeSpan
from scal3.cal_types import calTypes
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.mywidgets.label import SLabel
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.customize import CustomizableCalObj


@registerSignals
class CalObj(gtk.Box, CustomizableCalObj):
	_name = "statusBar"
	desc = _("Status Bar")
	itemListCustomizable = False
	hasOptions = True
	optionsPageSpacing = 15

	def __init__(self, win):
		self.win = win
		from scal3.ui_gtk.mywidgets.resize_button import ResizeButton
		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
		self.initVars()
		####
		self.labelBox = HBox()
		pack(self, self.labelBox, 1, 1)
		resizeB = ResizeButton(win)
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
		activeCalTypes = calTypes.active
		if ui.statusBarDatesReverseOrder:
			activeCalTypes = reversed(activeCalTypes)
		for calType in activeCalTypes:
			label = SLabel()
			label.calType = calType
			label.set_direction(gtk.TextDirection.LTR)
			pack(self.labelBox, label, 1)
		self.show_all()
		###
		self.onDateChange()

	def onDateChange(self, *a, **kw):
		CustomizableCalObj.onDateChange(self, *a, **kw)
		labels = self.labelBox.get_children()
		for i, label in enumerate(labels):
			text = ui.cell.format(ud.dateFormatBin, label.calType)
			if label.calType == calTypes.primary:
				text = f"<b>{text}</b>"
			if ui.statusBarDatesColorEnable:
				text = colorizeSpan(text, ui.statusBarDatesColor)
			label.set_label(text)

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import (
			CheckPrefItem,
			ColorPrefItem,
			CheckColorPrefItem,
		)
		if self.optionsWidget:
			return self.optionsWidget
		####
		optionsWidget = VBox(spacing=10)
		####
		prefItem = CheckPrefItem(
			ui,
			"statusBarDatesReverseOrder",
			label=_("Reverse the order of dates"),
			live=True,
			onChangeFunc=self.onConfigChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		####
		prefItem = CheckColorPrefItem(
			CheckPrefItem(ui, "statusBarDatesColorEnable", _("Dates Color")),
			ColorPrefItem(ui, "statusBarDatesColor", True),
			live=True,
			onChangeFunc=self.onDateChange,
		)
		pack(optionsWidget, prefItem.getWidget())
		####
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return self.optionsWidget
