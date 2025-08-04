from __future__ import annotations

from scal3 import ui
from scal3.locale_man import rtl, textNumEncode
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
from scal3.ui_gtk.pbar import MyProgressBar

__all__ = ["CalObj"]


class CalObj(CustomizableCalObj):
	objName = "seasonPBar"
	desc = _("Season Progress Bar")
	itemListCustomizable = False

	def __init__(self, win: gtk.Window) -> None:
		super().__init__()
		self.frame = gtk.Frame()
		self.w: gtk.Widget = self.frame
		self.parentWin = win
		self.frame.set_shadow_type(gtk.ShadowType.ETCHED_IN)
		self.frame.set_border_width(0)
		self.pbar = MyProgressBar()
		self.frame.add(self.pbar.w)
		self.pbar.w.show()
		self.initVars()

	def onDateChange(self) -> None:
		from scal3.season import getSeasonNamePercentFromJd

		super().onDateChange()
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

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui.check import CheckOptionUI

		if self.optionsWidget:
			return self.optionsWidget
		# ----
		optionsWidget = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		option = CheckOptionUI(
			option=conf.seasonPBar_southernHemisphere,
			label=_("Southern Hemisphere"),
			live=True,
			onChangeFunc=self.onSouthernHemisphereChange,
		)
		pack(optionsWidget, option.getWidget())
		# ----
		optionsWidget.show_all()
		self.optionsWidget = optionsWidget
		return optionsWidget

	def onSouthernHemisphereChange(self) -> None:
		self.onDateChange()
