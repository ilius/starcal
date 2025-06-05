from __future__ import annotations

from scal3 import logger
from scal3.ui_gtk.pref_utils import FloatSpinPrefItem, PrefItem

log = logger.get()


from typing import TYPE_CHECKING

from scal3 import ui
from scal3.locale_man import tr as _
from scal3.ui import conf
from scal3.ui_gtk import VBox, gtk, pack, timeout_add
from scal3.ui_gtk.customize import CustomizableCalObj, newSubPageButton
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.event.occurrence_view import (
	DayOccurrenceView,
)
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.pluginsText import PluginsTextBox

if TYPE_CHECKING:
	from scal3.ui_gtk.stack import StackPage

__all__ = ["MainWinRightPanel"]


class RightPanelDayOccurrenceView(DayOccurrenceView):
	def __init__(self, rightPanel: MainWinRightPanel | None = None, **kwargs) -> None:
		DayOccurrenceView.__init__(self, **kwargs)
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
	def __init__(self, rightPanel: MainWinRightPanel | None = None, **kwargs) -> None:
		PluginsTextBox.__init__(self, **kwargs)
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


@registerSignals
class MainWinRightPanel(gtk.Paned, CustomizableCalObj):  # type: ignore[misc]
	objName = "rightPanel"
	desc = _("Right Panel")
	itemListCustomizable = False
	optionsPageSpacing = 5

	def __init__(self) -> None:
		gtk.Paned.__init__(self, orientation=gtk.Orientation.VERTICAL)
		# ---
		self.initVars()
		self.setPosAtHeight = 0
		# ---
		self.connect("size-allocate", self.onSizeAllocate)
		# ---
		self.eventItem = RightPanelDayOccurrenceView(
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
			rightPanel=self,
			hideIfEmpty=False,
			tabToNewline=True,
			justificationParam=conf.mainWinRightPanelPluginsJustification,
			fontEnableParam=conf.mainWinRightPanelPluginsFontEnable,
			fontParam=conf.mainWinRightPanelPluginsFont,
			styleClass="right-panel-plugins",
		)
		# ---
		self.enablePrefItem = None  # will be set in customize_dialog.py
		# ---
		self.addItems()
		# ---
		self.show_all()
		self.onBorderWidthChange()

	def onToggleFromMainWin(self) -> None:
		if self.enablePrefItem is None:
			return
		self.enablePrefItem.set(not self.enablePrefItem.get())

	def appendItem(self, item: CustomizableCalObj) -> None:
		CustomizableCalObj.appendItem(self, item)
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.NEVER, gtk.PolicyType.AUTOMATIC)
		swin.add(item)
		frame = gtk.Frame()
		frame.set_shadow_type(gtk.ShadowType.IN)
		frame.add(swin)
		self.add(frame)
		item.show_all()

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
			item.get_parent().remove(item)
		for child in self.get_children():
			# child is Frame, containing a ScrolledWindow, containing item
			self.remove(child)
		self.items = []
		self.addItems()

	def swapItems(self) -> None:
		conf.mainWinRightPanelSwap.v = not conf.mainWinRightPanelSwap.v
		self.resetItems()
		self.show_all()
		ui.saveConfCustomize()

	def getSubPages(self) -> list[StackPage]:
		if self.subPages is not None:
			return self.subPages
		self.getOptionsWidget()
		return self.subPages

	def onEventIconSizeChange(self) -> None:
		self.eventItem.onDateChange(toParent=False)

	def onBorderWidthChange(self) -> None:
		self.set_border_width(conf.mainWinRightPanelBorderWidth.v)

	def updatePosition(self, height: int) -> None:
		log.debug(
			f"updatePosition: {height=}, {self.setPosAtHeight=}, "
			f"pos={self.get_position()}",
		)
		if height <= 1:
			return
		if height != self.setPosAtHeight:
			pos = int(height * conf.mainWinRightPanelRatio.v)
			self.set_position(pos)
			self.setPosAtHeight = height
			timeout_add(10, self.queue_resize)
			return
		conf.mainWinRightPanelRatio.v = self.get_position() / height
		ui.saveLiveConf()

	def onSizeAllocate(self, _w: gtk.Widget, requisition: gtk.Requisition) -> None:
		self.updatePosition(requisition.height)

	def onWindowSizeChange(self, *_a, **_kw) -> None:
		self.queue_resize()

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

	def onMinimumHeightChange(self) -> None:
		self.queue_resize()

	def do_get_preferred_width(self) -> tuple[int, int]:  # noqa: PLR6301
		# must return minimum_size, natural_size
		if conf.mainWinRightPanelWidthRatioEnable.v:
			if ui.mainWin and ui.mainWin.is_maximized():
				winWidth = ui.mainWin.get_size()[0]
			else:
				winWidth = conf.winWidth.v
			width = int(conf.mainWinRightPanelWidthRatio.v * winWidth)
		else:
			width = conf.mainWinRightPanelWidth.v
		return width, width

	def do_get_preferred_width_for_height(self, _size: int) -> tuple[int, int]:
		return self.do_get_preferred_width()

	def getOptionsWidget(self) -> gtk.Widget | None:
		from scal3.ui_gtk.pref_utils import (
			CheckPrefItem,
			IntSpinPrefItem,
		)
		from scal3.ui_gtk.pref_utils_extra import FixedSizeOrRatioPrefItem
		from scal3.ui_gtk.stack import StackPage

		if self.optionsWidget is not None:
			return self.optionsWidget
		optionsWidget = VBox(spacing=10)
		subPages = []
		# ---
		sizesVBox = gtk.VBox(spacing=10)
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
		prefItem: PrefItem
		# -----
		prefItem = FixedSizeOrRatioPrefItem(
			ratioEnableProp=conf.mainWinRightPanelWidthRatioEnable,
			fixedLabel=_("Fixed width"),
			fixedItem=IntSpinPrefItem(
				prop=conf.mainWinRightPanelWidth,
				bounds=(1, 9999),
			),
			ratioLabel=_("Relative to window"),
			ratioItem=FloatSpinPrefItem(
				prop=conf.mainWinRightPanelWidthRatio,
				bounds=(0, 1),
				digits=3,
			),
			onChangeFunc=self.queue_resize,
			vspacing=3,
			# hspacing=0,
		)
		frame = gtk.Frame(label=_("Width"))
		frame.add(prefItem.getWidget())
		frame.set_border_width(0)
		pack(sizesVBox, frame)
		# ---
		prefItem = IntSpinPrefItem(
			prop=conf.mainWinRightPanelBorderWidth,
			bounds=(1, 999),
			step=1,
			unitLabel=_("pixels"),
			label=_("Border Width"),
			live=True,
			onChangeFunc=self.onBorderWidthChange,
		)
		pack(sizesVBox, prefItem.getWidget())
		# ------
		eventsVBox = gtk.VBox(spacing=10)
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
		prefItem = IntSpinPrefItem(
			prop=conf.rightPanelEventIconSize,
			bounds=(5, 128),
			step=1,
			label=_("Event Icon Size"),
			live=True,
			onChangeFunc=self.onEventIconSizeChange,
		)
		pack(eventsVBox, prefItem.getWidget())
		# ---
		eventOptionsWidget = self.eventItem.getOptionsWidget()
		assert eventOptionsWidget is not None
		pack(eventsVBox, eventOptionsWidget)
		# ------
		pluginsVBox = gtk.VBox(spacing=10)
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
		prefItem = CheckPrefItem(
			prop=conf.mainWinRightPanelResizeOnToggle,
			label=_("Resize on show/hide\nfrom window controller"),
			# tooltip="",
			live=True,
			# onChangeFunc=None,
		)
		pack(optionsWidget, prefItem.getWidget())
		# ------
		self.optionsWidget = optionsWidget
		self.subPages = subPages
		return optionsWidget
