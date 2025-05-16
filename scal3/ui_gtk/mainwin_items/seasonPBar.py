from scal3 import ui
from scal3.locale_man import rtl, textNumEncode
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import HBox, gtk, pack
from scal3.ui_gtk.customize import CustomizableCalObj
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.pbar import MyProgressBar

__all__ = ["CalObj"]


@registerSignals
class CalObj(gtk.Frame, CustomizableCalObj):
	objName = "seasonPBar"
	desc = _("Season Progress Bar")
	itemListCustomizable = False

	def __init__(self, win: gtk.Window) -> None:
		self.win = win
		gtk.Frame.__init__(self)
		self.set_shadow_type(gtk.ShadowType.ETCHED_IN)
		self.set_border_width(0)
		self.pbar = MyProgressBar()
		self.add(self.pbar)
		self.pbar.show()
		self.initVars()

	def onDateChange(self, *a, **kw) -> None:
		from scal3.season import getSeasonNamePercentFromJd

		CustomizableCalObj.onDateChange(self, *a, **kw)
		name, frac = getSeasonNamePercentFromJd(
			ui.cells.current.jd,
			conf.seasonPBar_southernHemisphere.v,
		)
		if rtl:
			percent = f"{int(frac * 100)}%"
		else:
			percent = f"%{int(frac * 100)}"
		self.pbar.set_text(
			_(name)
			+ " - "
			+ textNumEncode(
				percent,
				changeDot=True,
			),
		)
		self.pbar.set_fraction(frac)

	def getOptionsWidget(self) -> gtk.Widget:
		from scal3.ui_gtk.pref_utils import CheckPrefItem

		if self.optionsWidget:
			return self.optionsWidget
		# ----
		self.optionsWidget = HBox()
		prefItem = CheckPrefItem(
			prop=conf.seasonPBar_southernHemisphere,
			label=_("Southern Hemisphere"),
			live=True,
			onChangeFunc=self.onDateChange,
		)
		pack(self.optionsWidget, prefItem.getWidget())
		# ----
		self.optionsWidget.show_all()
		return self.optionsWidget
