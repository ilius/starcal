from scal3 import core
from scal3.locale_man import tr as _
from scal3.locale_man import rtl, textNumEncode
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.pbar import MyProgressBar
from scal3.ui_gtk.decorators import *
from scal3.ui_gtk.customize import CustomizableCalObj


@registerSignals
class CalObj(MyProgressBar, CustomizableCalObj):
	_name = "seasonPBar"
	desc = _("Season Progress Bar")

	def __init__(self):
		MyProgressBar.__init__(self)
		self.initVars()

	def onConfigChange(self, *a, **kw):
		self.update_font()

	def onDateChange(self, *a, **kw):
		from scal3.season import getSeasonNamePercentFromJd
		CustomizableCalObj.onDateChange(self, *a, **kw)
		name, frac = getSeasonNamePercentFromJd(ui.cell.jd, ui.seasonPBar_southernHemisphere)
		if rtl:
			percent = "%d%%" % (frac * 100)
		else:
			percent = "%%%d" % (frac * 100)
		self.set_text(
			_(name) +
			" - " +
			textNumEncode(
				percent,
				changeDot=True,
			)
		)
		self.set_fraction(frac)

	def optionsWidgetCreate(self):
		from scal3.ui_gtk.pref_utils import LiveCheckPrefItem
		if self.optionsWidget:
			return
		####
		self.optionsWidget = gtk.HBox()
		prefItem = LiveCheckPrefItem(
			ui,
			"seasonPBar_southernHemisphere",
			label=_("Southern Hemisphere"),
			onChangeFunc=self.onDateChange,
		)
		pack(self.optionsWidget, prefItem._widget)
		####
		self.optionsWidget.show_all()

