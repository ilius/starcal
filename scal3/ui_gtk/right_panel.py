from __future__ import annotations

from scal3 import logger
from scal3.ui_gtk.cal_obj_base import CustomizableCalObj
from scal3.ui_gtk.option_ui import FloatSpinOptionUI

log = logger.get()


from typing import TYPE_CHECKING

from scal3 import ui
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import gdk, gtk, pack, timeout_add
from scal3.ui_gtk.customize import newSubPageButton
from scal3.ui_gtk.event.occurrence_view import (
	DayOccurrenceView,
)
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.pluginsText import PluginsTextBox

if TYPE_CHECKING:
	from collections.abc import Callable

	from scal3.font import Font
	from scal3.option import Option
	from scal3.ui_gtk.option_ui import OptionUI
	from scal3.ui_gtk.pytypes import CustomizableCalObjType, StackPageType

__all__ = ["MainWinRightPanel"]


class RightPanelDayOccurrenceView(DayOccurrenceView):
	def __init__(
		self,
		rightPanel: MainWinRightPanel | None = None,
		eventSepParam: Option[str] | None = None,
		justificationParam: Option[str] | None = None,
		fontEnableParam: Option[bool] | None = None,
		fontParam: Option[Font | None] | None = None,
		timeFontEnableParam: Option[bool] | None = None,
		timeFontParam: Option[Font | None] | None = None,
		styleClass: str = "",
		wrapMode: gtk.WrapMode = gtk.WrapMode.WORD_CHAR,
	) -> None:
		DayOccurrenceView.__init__(
			self,
			eventSepParam=eventSepParam,
			justificationParam=justificationParam,
			fontEnableParam=fontEnableParam,
			fontParam=fontParam,
			timeFontEnableParam=timeFontEnableParam,
			timeFontParam=timeFontParam,
			styleClass=styleClass,
			wrapMode=wrapMode,
		)
		self.rightPanel = rightPanel
		self.updateJustification()

	def addExtraMenuItems(self, menu: gtk.Menu) -> None:
		menu.add(gtk.SeparatorMenuItem())
		menu.add(
			ImageMenuItem(
				_("Swap with Plugins Text"),
				imageName="switch-vertical.svg",
				func=self.onSwapClick,
			),
		)

	def onSwapClick(self, _w: gtk.Widget) -> None:
		assert self.rightPanel is not None
		self.rightPanel.swapItems()


class RightPanelPluginsTextBox(PluginsTextBox):
	def __init__(
		self,
		rightPanel: MainWinRightPanel | None = None,
		hideIfEmpty: bool = True,
		tabToNewline: bool = False,
		insideExpanderParam: Option[bool] | None = None,
		justificationParam: Option[str] | None = None,
		fontEnableParam: Option[bool] | None = None,
		fontParam: Option[Font | None] | None = None,
		styleClass: str = "",
	) -> None:
		PluginsTextBox.__init__(
			self,
			hideIfEmpty=hideIfEmpty,
			tabToNewline=tabToNewline,
			insideExpanderParam=insideExpanderParam,
			justificationParam=justificationParam,
			fontEnableParam=fontEnableParam,
			fontParam=fontParam,
			styleClass=styleClass,
		)
		self.rightPanel = rightPanel
		self.updateJustification()
		self.textview.addExtraMenuItems = self.addExtraMenuItems  # type: ignore[method-assign]

	def addExtraMenuItems(self, menu: gtk.Menu) -> None:
		if self.rightPanel:
			menu.add(gtk.SeparatorMenuItem())
			menu.add(
				ImageMenuItem(
					_("Swap with Events Text"),
					imageName="switch-vertical.svg",
					func=self.onSwapClick,
				),
			)

	def onSwapClick(self, _w: gtk.Widget) -> None:
		assert self.rightPanel is not None
		self.rightPanel.swapItems()


class VericalPanedWithWidthFunc(gtk.Paned):
	def __init__(self, getWidth: Callable[[], int]) -> None:
		gtk.Paned.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.getWidth = getWidth

	def do_get_preferred_width(self) -> tuple[int, int]:  # noqa: PLR6301
		# must return minimum_size, natural_size
		width = self.getWidth()
		return width, width

	def do_get_preferred_width_for_height(self, _size: int) -> tuple[int, int]:
		return self.do_get_preferred_width()


class MainWinRightPanel(CustomizableCalObj):
	objName = "rightPanel"
	desc = _("Right Panel")
	itemListCustomizable = False
	optionsPageSpacing = 5

	def __init__(self) -> None:
		super().__init__()
		self.paned = VericalPanedWithWidthFunc(getWidth=self.getWidth)
		self.w: gtk.Widget = self.paned
		self.w.add_events(gdk.EventMask.ALL_EVENTS_MASK)
		# ---
		self.initVars()
		self.setPosAtHeight = 0
		# ---
		self.w.connect("size-allocate", self.onSizeAllocate)
		# ---
		self.eventItem = RightPanelDayOccurrenceView(
			# getWidth=self.getWidth,
			rightPanel=self,
			eventSepParam=conf.mainWinRightPanelEventSep,
			justificationParam=conf.mainWinRightPanelEventJustification,
			fontEnableParam=conf.mainWinRightPanelEventFontEnable,
			fontParam=conf.mainWinRightPanelEventFont,
			timeFontEnableParam=conf.mainWinRightPanelEventTimeFontEnable,
			timeFontParam=conf.mainWinRightPanelEventTimeFont,
			styleClass="right-panel-events",
		)
		# self.eventItem = WeekOccurrenceView()  # just temp to see it works
		self.plugItem = RightPanelPluginsTextBox(
			# getWidth=self.getWidth,
			rightPanel=self,
			hideIfEmpty=False,
			tabToNewline=True,
			justificationParam=conf.mainWinRightPanelPluginsJustification,
			fontEnableParam=conf.mainWinRightPanelPluginsFontEnable,
			fontParam=conf.mainWinRightPanelPluginsFont,
			styleClass="right-panel-plugins",
		)
		# ---
		self.enableOptionUI = None  # will be set in customize_dialog.py
		# ---
		self.addItems()
		# ---
		self.w.show_all()
		self.onBorderWidthChange()

	def onToggleFromMainWin(self) -> None:
		if self.enableOptionUI is None:
			return
		self.enableOptionUI.set(not self.enableOptionUI.get())

	def appendItem(self, item: CustomizableCalObjType) -> None:
		CustomizableCalObj.appendItem(self, item)
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.NEVER, gtk.PolicyType.AUTOMATIC)
		swin.add(item.w)
		frame = gtk.Frame()
		frame.set_shadow_type(gtk.ShadowType.IN)
		frame.add(swin)
		self.paned.add(frame)
		item.show()

	def addItems(self) -> None:
		items: list[CustomizableCalObj] = [
			self.eventItem,
			self.plugItem,
		]
		if conf.mainWinRightPanelSwap.v:
			items.reverse()
		for item in items:
			self.appendItem(item)

	def resetItems(self) -> None:
		for item in self.items:
			parent = item.w.get_parent()
			assert isinstance(parent, gtk.Container), f"{parent=}"
			parent.remove(item.w)
		for child in self.paned.get_children():
			# child is Frame, containing a ScrolledWindow, containing item
			self.paned.remove(child)
		self.items = []
		self.addItems()

	def swapItems(self) -> None:
		conf.mainWinRightPanelSwap.v = not conf.mainWinRightPanelSwap.v
		self.resetItems()
		self.w.show_all()
		ui.saveConfCustomize()

	def getSubPages(self) -> list[StackPageType]:
		if self.subPages is not None:
			return self.subPages
		self.getOptionsWidget()
		return self.subPages

	def onEventIconSizeChange(self) -> None:
		self.eventItem.onDateChange()

	def onBorderWidthChange(self) -> None:
		self.paned.set_border_width(conf.mainWinRightPanelBorderWidth.v)

	def updatePosition(self, height: int) -> None:
		log.debug(
			f"updatePosition: {height=}, {self.setPosAtHeight=}, "
			f"pos={self.paned.get_position()}",
		)
		if height <= 1:
			return
		if height != self.setPosAtHeight:
			pos = int(height * conf.mainWinRightPanelRatio.v)
			self.paned.set_position(pos)
			self.setPosAtHeight = height
			timeout_add(10, self.updateWidth)
			return
		conf.mainWinRightPanelRatio.v = self.paned.get_position() / height
		ui.saveLiveConf()

	def onSizeAllocate(self, _w: gtk.Widget, requisition: gtk.Requisition) -> None:
		self.updatePosition(requisition.height)

	def updateWidth(self) -> None:
		self.w.queue_resize()  # does not work!
		# self.eventItem.w.queue_resize()

	def onWindowSizeChange(self) -> None:
		self.updateWidth()

	def onMinimumHeightChange(self) -> None:
		self.updateWidth()

	"""
	gtk_widget_queue_resize:
		Flags a widget to have its size renegotiated; should
		be called when a widget for some reason has a new size request.
		For example, when you change the text in a #GtkLabel, #GtkLabel
		queues a resize to ensure there’s enough space for the new text.
		Note that you cannot call gtk_widget_queue_resize() on a widget
		from inside its implementation of the GtkWidgetClass::size_allocate
		virtual method. Calls to gtk_widget_queue_resize() from inside
		GtkWidgetClass::size_allocate will be silently ignored.

	gtk_widget_queue_allocate:
		Flags the widget for a rerun of the GtkWidgetClass::size_allocate
		function. Use this function instead of gtk_widget_queue_resize()
		when the @widget's size request didn't change but it wants to
		reposition its contents.
	"""

	def getWidth(self) -> int:  # noqa: PLR6301
		# TODO: add self.parentWin: gtk.Window, use it instead of ui.mainWin.w
		if conf.mainWinRightPanelWidthRatioEnable.v:
			if ui.mainWin and ui.mainWin.win.is_maximized():
				winWidth = ui.mainWin.win.get_size()[0]
			else:
				winWidth = conf.winWidth.v
			return int(conf.mainWinRightPanelWidthRatio.v * winWidth)
		return conf.mainWinRightPanelWidth.v

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.option_ui import (
			CheckOptionUI,
			IntSpinOptionUI,
		)
		from scal3.ui_gtk.option_ui_extra import FixedSizeOrRatioOptionUI
		from scal3.ui_gtk.stack import StackPage

		if self.optionsWidget is not None:
			return self.optionsWidget
		optionsWidget = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=10)
		subPages: list[StackPageType] = []
		# ---
		sizesVBox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=10)
		page = StackPage()
		page.pageWidget = sizesVBox
		page.pageName = "sizes"
		page.pageTitle = _("Sizes")
		page.pageLabel = _("Sizes")
		page.pageIcon = ""
		subPages.append(page)
		# ---
		button = newSubPageButton(self, page, borderWidth=10)
		pack(optionsWidget, button)
		option: OptionUI
		# -----
		option = FixedSizeOrRatioOptionUI(
			ratioEnableOption=conf.mainWinRightPanelWidthRatioEnable,
			fixedLabel=_("Fixed width"),
			fixedItem=IntSpinOptionUI(
				option=conf.mainWinRightPanelWidth,
				bounds=(1, 9999),
				step=10,
			),
			ratioLabel=_("Relative to window"),
			ratioItem=FloatSpinOptionUI(
				option=conf.mainWinRightPanelWidthRatio,
				bounds=(0, 1),
				digits=3,
				step=0.01,
			),
			onChangeFunc=self.updateWidth,
			vspacing=3,
			# hspacing=0,
		)
		frame = gtk.Frame(label=_("Width"))
		frame.add(option.getWidget())
		frame.set_border_width(0)
		pack(sizesVBox, frame)
		# ---
		option = IntSpinOptionUI(
			option=conf.mainWinRightPanelBorderWidth,
			bounds=(0, 999),
			step=1,
			unitLabel=_("pixels"),
			label=_("Border Width"),
			live=True,
			onChangeFunc=self.onBorderWidthChange,
		)
		pack(sizesVBox, option.getWidget())
		# ------
		eventsVBox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=10)
		page = StackPage()
		page.pageWidget = eventsVBox
		page.pageName = "events"
		page.pageTitle = _("Events")
		page.pageLabel = _("Events Text")
		page.pageIcon = ""
		subPages.append(page)
		# ---
		button = newSubPageButton(self, page, borderWidth=10)
		pack(optionsWidget, button)
		# ---
		option = IntSpinOptionUI(
			option=conf.rightPanelEventIconSize,
			bounds=(5, 128),
			step=1,
			label=_("Event Icon Size"),
			live=True,
			onChangeFunc=self.onEventIconSizeChange,
		)
		pack(eventsVBox, option.getWidget())
		# ---
		eventOptionsWidget = self.eventItem.getOptionsWidget()
		assert eventOptionsWidget is not None
		pack(eventsVBox, eventOptionsWidget)
		# ------
		pluginsVBox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=10)
		page = StackPage()
		page.pageWidget = pluginsVBox
		page.pageName = "plugins"
		page.pageTitle = _("Plugins")
		page.pageLabel = _("Plugins Text")
		page.pageIcon = ""
		subPages.append(page)
		# ---
		button = newSubPageButton(self, page, borderWidth=10)
		pack(optionsWidget, button)
		# ---
		pluginOptionsWidget = self.plugItem.getOptionsWidget()
		assert pluginOptionsWidget is not None
		pack(pluginsVBox, pluginOptionsWidget)
		# ------
		option = CheckOptionUI(
			option=conf.mainWinRightPanelResizeOnToggle,
			label=_("Resize on show/hide\nfrom window controller"),
			# tooltip="",
			live=True,
			# onChangeFunc=None,
		)
		pack(optionsWidget, option.getWidget())
		# ------
		self.optionsWidget = optionsWidget
		self.subPages = subPages
		return optionsWidget
