#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.
from __future__ import annotations

from scal3 import logger
from scal3.ui import conf
from scal3.ui_gtk.pref_utils import IntSpinPrefItem

log = logger.get()

from math import sqrt
from typing import TYPE_CHECKING

from gi.repository.PangoCairo import show_layout

from scal3 import cal_types, core, ui
from scal3.cal_types import calTypes
from scal3.locale_man import rtl, rtlSgn
from scal3.locale_man import tr as _
from scal3.ui.font import getParamsFont
from scal3.ui_gtk import (
	TWO_BUTTON_PRESS,
	Dialog,
	HBox,
	VBox,
	gdk,
	getScrollValue,
	gtk,
	pack,
)
from scal3.ui_gtk.cal_base import CalBase
from scal3.ui_gtk.customize import CustomizableCalObj, newSubPageButton
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.drawing import (
	drawOutlineRoundedRect,
	drawRoundedRect,
	fillColor,
	newTextLayout,
	setColor,
)
from scal3.ui_gtk.stack import StackPage
from scal3.ui_gtk.utils import newAlignLabel, pixbufFromFile

if TYPE_CHECKING:
	import cairo

	from scal3.cell import MonthStatus
	from scal3.cell_type import CellType
	from scal3.ui.pytypes import CalTypeParamsDict
	from scal3.ui_gtk.pref_utils import PrefItem

__all__ = ["CalObj"]


@registerSignals
class CalObj(gtk.DrawingArea, CalBase):  # type: ignore[misc]
	objName = "monthCal"
	desc = _("Month Calendar")
	expand = True
	itemListCustomizable = False
	optionsPageSpacing = 5
	cx = [0, 0, 0, 0, 0, 0, 0]
	myKeys = CalBase.myKeys | {
		"up",
		"down",
		"right",
		"left",
		"page_up",
		"k",
		"p",
		"page_down",
		"j",
		"n",
		"end",
		"f10",
		"m",
	}

	def do_get_preferred_height(self) -> tuple[int, int]:  # noqa: PLR6301
		return 0, int(conf.winHeight.v / 3)

	def updateTypeParamsWidget(self) -> None:
		from scal3.ui_gtk.cal_type_params import CalTypeParamWidget

		try:
			vbox = self.typeParamsVbox
		except AttributeError:
			return
		for child in vbox.get_children():
			child.destroy()
		# ---
		subPages = [self.cursorPage]
		n = len(calTypes.active)
		while len(conf.mcalTypeParams.v) < n:
			conf.mcalTypeParams.v.append(
				{
					"pos": (0, 0),
					"font": ui.getFont(0.6),
					"color": conf.textColor.v,
				},
			)
		sgroupLabel = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		for index, calType in enumerate(calTypes.active):
			module = calTypes[calType]
			if module is None:
				raise RuntimeError(f"cal type '{calType}' not found")
			pageWidget = CalTypeParamWidget(
				params=conf.mcalTypeParams,  # type: ignore[arg-type]
				index=index,
				cal=self,
				sgroupLabel=sgroupLabel,
				calType=calType,
				hasEnable=(index > 0),
			)
			pageWidget.show_all()
			page = StackPage()
			page.pageWidget = pageWidget
			page.pageName = module.name
			# setting pageParent and pagePath here is ugly, but it's needed
			page.pageParent = self.pagePath
			page.pagePath = page.pageParent + "." + page.pageName
			page.pageTitle = page.pageLabel = _("{calType} Calendar").format(
				calType=_(module.desc, ctx="calendar"),
			)
			page.pageExpand = False
			subPages.append(page)
			button = newSubPageButton(self, page, borderWidth=7)
			pack(vbox, button, padding=3)
		# ---
		vbox.show_all()
		self.subPages = subPages

	@staticmethod
	def drawCursorOutline(
		cr: cairo.Context,
		cx0: float,
		cy0: float,
		cw: float,
		ch: float,
	) -> None:
		cursorRadius = conf.mcalCursorRoundingFactor.v * min(cw, ch) * 0.5
		cursorLineWidth = conf.mcalCursorLineWidthFactor.v * min(cw, ch) * 0.5
		drawOutlineRoundedRect(cr, cx0, cy0, cw, ch, cursorRadius, cursorLineWidth)

	@staticmethod
	def drawCursorBg(
		cr: cairo.Context,
		cx0: float,
		cy0: float,
		cw: float,
		ch: float,
	) -> None:
		cursorRadius = conf.mcalCursorRoundingFactor.v * min(cw, ch) * 0.5
		drawRoundedRect(cr, cx0, cy0, cw, ch, cursorRadius)

	def __init__(self, win: gtk.Window) -> None:
		self.win = win
		gtk.DrawingArea.__init__(self)
		self.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		self.initCal()
		self.pagePath = f"mainWin.mainPanel.{self.objName}"
		# ----------------------
		# self.kTime = 0
		# ----------------------
		self.connect("draw", self.drawAll)
		self.connect("button-press-event", self.onButtonPress)
		# self.connect("screen-changed", self.screenChanged)
		self.connect("scroll-event", self.scroll)
		# ----------------------
		# self.updateTextWidth()

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.pref_utils import (
			CheckColorPrefItem,
			CheckPrefItem,
			ColorPrefItem,
			FloatSpinPrefItem,
		)

		if self.optionsWidget:
			return self.optionsWidget

		optionsWidget = VBox(spacing=self.optionsPageSpacing)
		labelSizeGroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		prefItem: PrefItem
		# -------
		prefItem = IntSpinPrefItem(
			prop=conf.mcalLeftMargin,
			bounds=(0, 999),
			step=1,
			label=_("Left Margin"),
			labelSizeGroup=labelSizeGroup,
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(optionsWidget, prefItem.getWidget())
		# ----
		prefItem = IntSpinPrefItem(
			prop=conf.mcalTopMargin,
			bounds=(0, 999),
			step=1,
			label=_("Top Margin"),
			labelSizeGroup=labelSizeGroup,
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(optionsWidget, prefItem.getWidget())
		# --------
		prefItem = CheckColorPrefItem(
			CheckPrefItem(prop=conf.mcalGrid, label=_("Grid")),
			ColorPrefItem(prop=conf.mcalGridColor, useAlpha=True),
			live=True,
			onChangeFunc=self.queue_draw,
		)
		hbox = prefItem.getWidget()
		pack(optionsWidget, hbox)
		# ---
		hbox = HBox(spacing=10)
		pack(hbox, newAlignLabel(label=_("Corner Menu Text Color")))
		prefItem = ColorPrefItem(
			prop=conf.mcalCornerMenuTextColor,
			useAlpha=True,
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(hbox, prefItem.getWidget())
		pack(hbox, gtk.Label(), 1, 1)
		pack(optionsWidget, hbox)
		# ------------
		pageVBox = VBox(spacing=20)
		pageVBox.set_border_width(10)
		sgroup = gtk.SizeGroup(mode=gtk.SizeGroupMode.HORIZONTAL)
		# ----
		prefItem = FloatSpinPrefItem(
			prop=conf.mcalCursorLineWidthFactor,
			bounds=(0, 1),
			digits=2,
			step=0.1,
			label=_("Line Width Factor"),
			labelSizeGroup=sgroup,
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(pageVBox, prefItem.getWidget())
		# ---
		prefItem = FloatSpinPrefItem(
			prop=conf.mcalCursorRoundingFactor,
			bounds=(0, 1),
			digits=2,
			step=0.1,
			label=_("Rounding Factor"),
			labelSizeGroup=sgroup,
			live=True,
			onChangeFunc=self.queue_draw,
		)
		pack(pageVBox, prefItem.getWidget())
		# ---
		pageVBox.show_all()
		# ---
		page = StackPage()
		page.pageWidget = pageVBox
		page.pageName = "cursor"
		page.pageTitle = _("Cursor")
		page.pageLabel = _("Cursor")
		page.pageIcon = ""
		self.cursorPage = page
		# ---
		button = newSubPageButton(self, page, borderWidth=7)
		pack(optionsWidget, button, padding=5)
		# --------
		self.optionsWidget = optionsWidget
		# ----
		self.typeParamsVbox = VBox()
		pack(optionsWidget, self.typeParamsVbox, padding=5)
		optionsWidget.show_all()
		self.updateTypeParamsWidget()  # FIXME
		return optionsWidget

	def getSubPages(self) -> list[StackPage]:
		if self.subPages is not None:
			return self.subPages
		self.getOptionsWidget()
		assert self.subPages is not None
		return self.subPages

	def drawAll(self, _w: gtk.Widget | None = None, cursor: bool = True) -> None:
		win = self.get_window()
		assert win is not None
		region = win.get_visible_region()
		# FIXME: This must be freed with cairo_region_destroy() when you are done.
		# where is cairo_region_destroy? No region.destroy() method
		dctx = win.begin_draw_frame(region)
		if dctx is None:
			raise RuntimeError("begin_draw_frame returned None")
		cr = dctx.get_cairo_context()
		try:
			self.drawWithContext(cr, cursor)
		finally:
			win.end_draw_frame(dctx)

	def _drawBorder(
		self,
		cr: cairo.Context,
		w: float,
		h: float,
		status: MonthStatus,
	) -> None:
		if conf.mcalTopMargin.v > 0:
			# Drawing border top background
			# mcalMenuCellBgColor == borderColor
			cr.rectangle(0, 0, w, conf.mcalTopMargin.v)
			fillColor(cr, conf.borderColor.v)
			# ------ Drawing weekDays names
			setColor(cr, conf.borderTextColor.v)
			wdayAb = self.wdaysWidth > w
			for i in range(7):
				weekDayLayout = newTextLayout(
					self, core.getWeekDayAuto(i, abbreviate=wdayAb)
				)
				assert weekDayLayout is not None
				try:
					fontw, fonth = weekDayLayout.get_pixel_size()
				except Exception:
					log.exception("")
					fontw, fonth = weekDayLayout.get_pixel_size()
				cr.move_to(
					self.cx[i] - fontw / 2,
					(conf.mcalTopMargin.v - fonth) / 2 - 1,
				)
				show_layout(cr, weekDayLayout)
			# ------ Drawing "Menu" label
			setColor(cr, conf.mcalCornerMenuTextColor.v)
			menuLayout = newTextLayout(self, _("Menu"))
			assert menuLayout is not None
			fontw, fonth = menuLayout.get_pixel_size()
			if rtl:
				cr.move_to(
					w - (conf.mcalLeftMargin.v + fontw) / 2 - 3,
					(conf.mcalTopMargin.v - fonth) / 2 - 1,
				)
			else:
				cr.move_to(
					(conf.mcalLeftMargin.v - fontw) / 2,
					(conf.mcalTopMargin.v - fonth) / 2 - 1,
				)
			show_layout(cr, menuLayout)
		if conf.mcalLeftMargin.v > 0:
			# Drawing border left background
			if rtl:
				cr.rectangle(
					w - conf.mcalLeftMargin.v,
					conf.mcalTopMargin.v,
					conf.mcalLeftMargin.v,
					h - conf.mcalTopMargin.v,
				)
			else:
				cr.rectangle(
					0,
					conf.mcalTopMargin.v,
					conf.mcalLeftMargin.v,
					h - conf.mcalTopMargin.v,
				)
			fillColor(cr, conf.borderColor.v)
			# Drawing week numbers
			setColor(cr, conf.borderTextColor.v)
			for i in range(6):
				layout = newTextLayout(self, _(status.weekNum[i]))
				assert layout is not None
				fontw, fonth = layout.get_pixel_size()
				if rtl:
					cr.move_to(
						w - (conf.mcalLeftMargin.v + fontw) / 2,
						self.cy[i] - fonth / 2 + 2,
					)
				else:
					cr.move_to(
						(conf.mcalLeftMargin.v - fontw) / 2,
						self.cy[i] - fonth / 2 + 2,
					)
				show_layout(cr, layout)

	def _drawTodayMarker(self, cr: cairo.Context) -> None:
		tx, ty = ui.cells.today.monthPos  # today x and y
		x0 = self.cx[tx] - self.dx / 2
		y0 = self.cy[ty] - self.dy / 2
		cr.rectangle(x0, y0, self.dx, self.dy)
		fillColor(cr, conf.todayCellColor.v)

	def _drawEventIcons(
		self,
		cr: cairo.Context,
		cell: CellType,
		x0: float,
		y0: float,
	) -> None:
		iconList = cell.getMonthEventIcons()
		if not iconList:
			return
		iconSizeMax = conf.mcalEventIconSizeMax.v

		iconsN = len(iconList)
		scaleFact = 1 / sqrt(iconsN)
		fromRight = 0
		for icon in iconList:
			# if len(iconList) > 1  # FIXME
			try:
				pixbuf = pixbufFromFile(icon, size=iconSizeMax)
			except Exception:
				log.exception("")
				continue
			if pixbuf is None:
				log.error(f"pixbuf=None, {icon=}")
				continue
			pix_w = pixbuf.get_width()
			pix_h = pixbuf.get_height()
			# right buttom corner ???
			# right side:
			x1 = (x0 + self.dx / 2) / scaleFact - fromRight - pix_w
			# buttom side:
			y1 = (y0 + self.dy / 2) / scaleFact - pix_h
			cr.scale(scaleFact, scaleFact)
			gdk.cairo_set_source_pixbuf(cr, pixbuf, x1, y1)
			cr.rectangle(x1, y1, pix_w, pix_h)
			cr.fill()
			cr.scale(1 / scaleFact, 1 / scaleFact)
			fromRight += pix_w

	def _drawCellSecondaryCalNumbers(
		self,
		cr: cairo.Context,
		cell: CellType,
		x0: float,
		y0: float,
		activeParams: list[tuple[int, CalTypeParamsDict]],
		cellHasCursor: bool,
	) -> None:
		for calType, params in activeParams[1:]:
			if not params.get("enable", True):
				continue
			dayNumLayout = newTextLayout(
				self,
				_(cell.dates[calType][2], calType),
				getParamsFont(params),
			)
			assert dayNumLayout is not None
			fontw, fonth = dayNumLayout.get_pixel_size()
			setColor(cr, params["color"])
			cr.move_to(
				x0 - fontw / 2 + params["pos"][0],
				y0 - fonth / 2 + params["pos"][1],
			)
			show_layout(cr, dayNumLayout)
		if cellHasCursor:
			# Drawing Cursor Outline
			cx0 = x0 - self.dx / 2 + 1
			cy0 = y0 - self.dy / 2 + 1
			cw = self.dx - 1
			ch = self.dy - 1
			# ------- Circular Rounded
			self.drawCursorOutline(cr, cx0, cy0, cw, ch)
			fillColor(cr, conf.cursorOutColor.v)
			# end of Drawing Cursor Outline

	def drawWithContext(self, cr: cairo.Context, cursor: bool) -> bool:
		# gevent = gtk.get_current_event()
		# FIXME: must enhance (only draw few cells, not all cells)
		self.calcCoord()
		w = self.get_allocation().width
		h = self.get_allocation().height
		cr.rectangle(0, 0, w, h)
		fillColor(cr, conf.bgColor.v)
		status = ui.cells.getCurrentMonthStatus()

		# Drawing Border
		self._drawBorder(cr=cr, w=w, h=h, status=status)

		currentCell: CellType = ui.cells.current
		selectedCellPos = currentCell.monthPos

		if ui.cells.today.date[:2] == currentCell.date[:2]:
			self._drawTodayMarker(cr)

		activeParams = ui.getActiveMonthCalParams()

		for yPos in range(6):
			for xPos in range(7):
				c = status[yPos][xPos]
				x0 = self.cx[xPos]
				y0 = self.cy[yPos]
				cellInactive = c.month != currentCell.month
				cellHasCursor = cursor and (xPos, yPos) == selectedCellPos
				if cellHasCursor:
					# Drawing Cursor
					cx0 = x0 - self.dx / 2 + 1
					cy0 = y0 - self.dy / 2 + 1
					cw = self.dx - 1
					ch = self.dy - 1
					# ------- Circular Rounded
					self.drawCursorBg(cr, cx0, cy0, cw, ch)
					fillColor(cr, conf.cursorBgColor.v)
				# ------ end of Drawing Cursor
				if not cellInactive:
					self._drawEventIcons(cr=cr, cell=c, x0=x0, y0=y0)
				# Drawing numbers inside every cell
				calType = calTypes.primary
				params = conf.mcalTypeParams.v[0]
				dayNumLayout = newTextLayout(
					self,
					_(c.dates[calType][2], calType),
					getParamsFont(params),
				)
				assert dayNumLayout is not None
				fontw, fonth = dayNumLayout.get_pixel_size()
				if cellInactive:
					setColor(cr, conf.inactiveColor.v)
				elif c.holiday:
					setColor(cr, conf.holidayColor.v)
				else:
					setColor(cr, params["color"])
				cr.move_to(
					x0 - fontw / 2 + params["pos"][0],
					y0 - fonth / 2 + params["pos"][1],
				)
				show_layout(cr, dayNumLayout)
				if not cellInactive:
					self._drawCellSecondaryCalNumbers(
						cr=cr,
						cell=c,
						x0=x0,
						y0=y0,
						activeParams=activeParams,
						cellHasCursor=cellHasCursor,
					)

		# -------------- end of drawing cells
		# drawGrid
		if conf.mcalGrid.v:
			setColor(cr, conf.mcalGridColor.v)
			for i in range(7):
				cr.rectangle(
					self.cx[i] + rtlSgn() * self.dx / 2,
					0,
					1,
					h,
				)
				cr.fill()
			for i in range(6):
				cr.rectangle(
					0,
					self.cy[i] - self.dy / 2,
					w,
					1,
				)
				cr.fill()
		return False

	def updateTextWidth(self) -> None:
		# update width of week days names to be able to find out
		# whether or not they should be shortened for the UI
		layout = newTextLayout(self)
		assert layout is not None
		wm = 0  # max width
		for i in range(7):
			wday = core.weekDayName[i]
			layout.set_markup(text=wday, length=-1)
			w = layout.get_pixel_size()[0]  # FIXME
			# w = lay.get_pixel_extents()[0]  # FIXME
			# log.debug(w,)
			wm = max(w, wm)
		self.wdaysWidth = wm * 7 + conf.mcalLeftMargin.v
		# self.wdaysWidth = wm * 7 * 0.7 + conf.mcalLeftMargin.v
		# log.debug("max =", wm, "     wdaysWidth =", self.wdaysWidth)

	def onButtonPress(self, _w: gtk.Widget, gevent: gdk.EventButton) -> bool:
		# self.winActivate() #?????????
		b = gevent.button
		(
			x,
			y,
		) = self.get_pointer()
		# foo, x, y, flags = self.get_window().get_pointer()
		self.pointer = (x, y)
		if b == 2:
			return False
		xPos = -1
		yPos = -1
		for i in range(7):
			if abs(x - self.cx[i]) <= self.dx / 2:
				xPos = i
				break
		for i in range(6):
			if abs(y - self.cy[i]) <= self.dy / 2:
				yPos = i
				break
		status = ui.cells.getCurrentMonthStatus()
		if -1 in {yPos, xPos}:
			self.emit("popup-main-menu", gevent.x, gevent.y)
		elif yPos >= 0 and xPos >= 0:
			cell = status[yPos][xPos]
			self.changeDate(*cell.dates[calTypes.primary])
			if gevent.type == TWO_BUTTON_PRESS:
				self.emit("double-button-press")
			if (
				b == 3 and cell.month == ui.cells.current.month
			):  # right click on a normal cell
				# self.emit("popup-cell-menu", *self.getCellPos())
				self.emit("popup-cell-menu", gevent.x, gevent.y)
		return True

	def calcCoord(self) -> None:  # calculates coordidates (x and y of cells centers)
		w = self.get_allocation().width
		h = self.get_allocation().height
		# self.cx is centers x, self.cy is centers y
		if rtl:
			self.cx = [
				int((w - conf.mcalLeftMargin.v) * (13 - 2 * i) / 14) for i in range(7)
			]
		else:
			self.cx = [
				int(
					conf.mcalLeftMargin.v
					+ ((w - conf.mcalLeftMargin.v) * (1 + 2 * i) / 14)
				)
				for i in range(7)
			]
		self.cy = [
			conf.mcalTopMargin.v + (h - conf.mcalTopMargin.v) * (1 + 2 * i) / 12
			for i in range(6)
		]
		self.dx = (w - conf.mcalLeftMargin.v) / 7  # delta x
		self.dy = (h - conf.mcalTopMargin.v) / 6  # delta y

	def monthPlus(self, plus: int) -> None:
		ui.cells.monthPlus(plus)
		self.onDateChange()

	def onKeyPress(self, arg: gtk.Widget, gevent: gdk.EventKey) -> bool:
		if CalBase.onKeyPress(self, arg, gevent):
			return True
		kname = gdk.keyval_name(gevent.keyval)
		if not kname:
			return False
		kname = kname.lower()
		# if kname.startswith("alt"):
		# 	return True
		if kname == "up":
			self.jdPlus(-7)
		elif kname == "down":
			self.jdPlus(7)
		elif kname == "right":
			if rtl:
				self.jdPlus(-1)
			else:
				self.jdPlus(1)
		elif kname == "left":
			if rtl:
				self.jdPlus(1)
			else:
				self.jdPlus(-1)
		elif kname == "end":
			self.changeDate(
				ui.cells.current.year,
				ui.cells.current.month,
				cal_types.getMonthLen(
					ui.cells.current.year,
					ui.cells.current.month,
					calTypes.primary,
				),
			)
		elif kname in {"page_up", "k", "p"}:
			self.monthPlus(-1)
		elif kname in {"page_down", "j", "n"}:
			self.monthPlus(1)
		elif kname in {"f10", "m"}:
			if gevent.get_state() & gdk.ModifierType.SHIFT_MASK:
				# Simulate right click (key beside Right-Ctrl)
				self.emit("popup-cell-menu", *self.getCellPos())
			else:
				self.emit("popup-main-menu", *self.getMainMenuPos())
		else:
			return False
		return True

	def scroll(self, _w: gtk.Widget, gevent: gdk.EventScroll) -> bool | None:
		d = getScrollValue(gevent)
		if d == "up":
			self.jdPlus(-7)
			return None
		if d == "down":
			self.jdPlus(7)
			return None
		return False

	def getCellPos(self, *_args) -> tuple[int, int]:
		return (
			int(self.cx[ui.cells.current.monthPos[0]]),
			int(self.cy[ui.cells.current.monthPos[1]] + self.dy / 2),
		)

	def getMainMenuPos(self, *_args) -> tuple[int, int]:  # FIXME
		if rtl:
			return (
				int(self.get_allocation().width - conf.mcalLeftMargin.v / 2),
				int(conf.mcalTopMargin.v / 2),
			)
		return (
			int(conf.mcalLeftMargin.v / 2),
			int(conf.mcalTopMargin.v / 2),
		)

	def onDateChange(self, *a, **kw) -> None:
		CustomizableCalObj.onDateChange(self, *a, **kw)
		self.queue_draw()

	def onConfigChange(self, *a, **kw) -> None:
		CustomizableCalObj.onConfigChange(self, *a, **kw)
		self.updateTextWidth()
		self.updateTypeParamsWidget()


if __name__ == "__main__":
	win = Dialog()
	cal = CalObj(win)
	win.add_events(gdk.EventMask.ALL_EVENTS_MASK)
	pack(win.vbox, cal, 1, 1)
	win.vbox.show_all()
	win.resize(600, 400)
	win.set_title(cal.desc)
	win.run()
