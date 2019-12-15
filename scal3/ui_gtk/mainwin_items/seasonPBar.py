#!/usr/bin/env python3
from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl, textNumEncode
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.pbar import MyProgressBar
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.customize import CustomizableCalObj


@registerSignals
class CalObj(gtk.Frame, CustomizableCalObj):
	_name = "seasonPBar"
	desc = _("Season Progress Bar")
	itemListCustomizable = False

	def __init__(self):
		gtk.Frame.__init__(self)
		self.set_shadow_type(gtk.ShadowType.ETCHED_IN)
		self.set_border_width(0)
		self.pbar = MyProgressBar()
		self.add(self.pbar)
		self.pbar.show()
		self.initVars()

	def onDateChange(self, *a, **kw):
		from scal3.season import getSeasonNamePercentFromJd
		CustomizableCalObj.onDateChange(self, *a, **kw)
		name, frac = getSeasonNamePercentFromJd(
			ui.cell.jd,
			ui.seasonPBar_southernHemisphere,
		)
		if rtl:
			percent = f"{int(frac * 100)}%"
		else:
			percent = f"%{int(frac * 100)}"
		self.pbar.set_text(
			_(name) +
			" - " +
			textNumEncode(
				percent,
				changeDot=True,
			)
		)
		self.pbar.set_fraction(frac)

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import CheckPrefItem
		if self.optionsWidget:
			return self.optionsWidget
		####
		self.optionsWidget = HBox()
		prefItem = CheckPrefItem(
			ui,
			"seasonPBar_southernHemisphere",
			label=_("Southern Hemisphere"),
			live=True,
			onChangeFunc=self.onDateChange,
		)
		pack(self.optionsWidget, prefItem.getWidget())
		####
		self.optionsWidget.show_all()
		return self.optionsWidget
