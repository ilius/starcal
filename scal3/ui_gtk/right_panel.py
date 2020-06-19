from scal3 import logger
log = logger.get()

from typing import Tuple

from scal3.locale_man import tr as _
from scal3 import ui

from scal3.ui_gtk import *
from scal3.ui_gtk.decorators import registerSignals
from scal3.ui_gtk.menuitems import ImageMenuItem
from scal3.ui_gtk.event.occurrence_view import (
	DayOccurrenceView,
	# WeekOccurrenceView,
)

from scal3.ui_gtk.customize import (
	CustomizableCalObj,
	newSubPageButton
)

class RightPanelDayOccurrenceView(DayOccurrenceView):
	def __init__(self, rightPanel=None, **kwargs):
		DayOccurrenceView.__init__(self, **kwargs)
		self.rightPanel = rightPanel
		self.updateJustification()

	def addExtraMenuItems(self, menu):
		menu.add(gtk.SeparatorMenuItem())
		menu.add(ImageMenuItem(
			_("Swap with Plugins Text"),
			imageName="switch-vertical.svg",
			func=self.onSwapClick,
		))

	def onSwapClick(self, widget):
		self.rightPanel.swapItems()


@registerSignals
class MainWinRightPanel(gtk.Paned, CustomizableCalObj):
	_name = "rightPanel"
	desc = _("Right Panel")
	itemListCustomizable = False
	optionsPageSpacing = 5

	def __init__(self):
		from scal3.ui_gtk.pluginsText import PluginsTextBox
		gtk.Paned.__init__(self, orientation=gtk.Orientation.VERTICAL)
		self.set_border_width(ui.mainWinRightPanelBorder)
		###
		self.initVars()
		self.optionsWidget = None
		self.setPosAtHeight = 0
		###
		self.connect("size-allocate", self.onSizeAllocate)
		###
		self.eventItem = RightPanelDayOccurrenceView(
			rightPanel=self,
			eventSepParam="mainWinRightPanelEventSep",
			justificationParam="mainWinRightPanelEventJustification",
			fontParams=(
				"mainWinRightPanelEventFontEnable",
				"mainWinRightPanelEventFont",
			),
			timeFontParams=(
				"mainWinRightPanelEventTimeFontEnable",
				"mainWinRightPanelEventTimeFont",
			),
			styleClass="right-panel-events",
		)
		# self.eventItem = WeekOccurrenceView()  # just temp to see it works
		self.plugItem = PluginsTextBox(
			hideIfEmpty=False,
			tabToNewline=True,
			justificationParam="mainWinRightPanelPluginsJustification",
			fontParams=(
				"mainWinRightPanelPluginsFontEnable",
				"mainWinRightPanelPluginsFont",
			),
			styleClass="right-panel-plugins",
		)
		###
		self.addItems()
		###
		self.show_all()

	def appendItem(self, item):
		CustomizableCalObj.appendItem(self, item)
		swin = gtk.ScrolledWindow()
		swin.set_policy(gtk.PolicyType.NEVER, gtk.PolicyType.AUTOMATIC)
		swin.add(item)
		frame = gtk.Frame()
		frame.set_shadow_type(gtk.ShadowType.IN)
		frame.add(swin)
		self.add(frame)
		item.show_all()

	def addItems(self):
		items = [
			self.eventItem,
			self.plugItem,
		]
		if ui.mainWinRightPanelSwap:
			items.reverse()
		for item in items:
			self.appendItem(item)

	def resetItems(self):
		for item in self.items:
			item.get_parent().remove(item)
		for child in self.get_children():
			# child is Frame, containing a ScrolledWindow, containing item
			self.remove(child)
		self.items = []
		self.addItems()

	def swapItems(self):
		ui.mainWinRightPanelSwap = not ui.mainWinRightPanelSwap
		self.resetItems()
		self.show_all()
		ui.saveConfCustomize()

	def getSubPages(self):
		if self.subPages is not None:
			return self.subPages
		self.getOptionsWidget()
		return self.subPages

	def onEventIconSizeChange(self):
		self.eventItem.onDateChange(toParent=False)

	def onBorderWidthChange(self):
		self.set_border_width(ui.mainWinRightPanelBorder)

	def updatePosition(self, height: int):
		log.debug(
			f"updatePosition: height={height}, setPosAtHeight={self.setPosAtHeight}, " +
			f"pos={self.get_position()}"
		)
		if height <= 1:
			return
		if height != self.setPosAtHeight:
			pos = int(height * ui.mainWinRightPanelRatio)
			self.set_position(pos)
			self.setPosAtHeight = height
			timeout_add(10, self.queue_resize)
			return
		ui.mainWinRightPanelRatio = self.get_position() / height
		ui.saveLiveConf()

	def onSizeAllocate(self, widget, requisition):
		self.updatePosition(requisition.height)

	def onWindowSizeChange(self, *a, **kw):
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

	def onMinimumHeightChange(self):
		self.queue_resize()

	def do_get_preferred_width(self):
		# must return minimum_size, natural_size
		if ui.mainWinRightPanelWidthRatioEnable:
			if ui.mainWin and ui.mainWin.is_maximized():
				winWidth = ui.mainWin.get_size()[0]
			else:
				winWidth = ui.winWidth
			width = ui.mainWinRightPanelWidthRatio * winWidth
		else:
			width = ui.mainWinRightPanelWidth
		return width, width

	def do_get_preferred_width_for_height(self, size: int) -> Tuple[int, int]:
		return self.do_get_preferred_width()

	def getOptionsWidget(self):
		from scal3.ui_gtk.pref_utils import (
			SpinPrefItem,
			CheckPrefItem,
		)
		from scal3.ui_gtk.pref_utils_extra import FixedSizeOrRatioPrefItem
		from scal3.ui_gtk.stack import StackPage
		if self.optionsWidget is not None:
			return self.optionsWidget
		optionsWidget = VBox(spacing=10)
		subPages = []
		###
		sizesVBox = gtk.VBox(spacing=10)
		page = StackPage()
		page.pageWidget = sizesVBox
		page.pageName = "sizes"
		page.pageTitle = _("Sizes")
		page.pageLabel = _("Sizes")
		page.pageIcon = ""
		subPages.append(page)
		###
		button = newSubPageButton(self, page, borderWidth=10)
		pack(optionsWidget, button)
		#####
		prefItem = FixedSizeOrRatioPrefItem(
			ui,
			ratioEnableVarName="mainWinRightPanelWidthRatioEnable",
			fixedLabel=_("Fixed width"),
			fixedItem=SpinPrefItem(ui, "mainWinRightPanelWidth", 1, 9999, digits=0),
			ratioLabel=_("Relative to window"),
			ratioItem=SpinPrefItem(ui, "mainWinRightPanelWidthRatio", 0, 1, digits=3),
			onChangeFunc=self.queue_resize,
			vspacing=3,
			hspacing=0,
		)
		frame = gtk.Frame(label=_("Width"))
		frame.add(prefItem.getWidget())
		frame.set_border_width(0)
		pack(sizesVBox, frame)
		###
		prefItem = SpinPrefItem(
			ui,
			"mainWinRightPanelBorder",
			1, 999,
			digits=1, step=1,
			unitLabel=_("pixels"),
			label=_("Border Width"),
			live=True,
			onChangeFunc=self.onBorderWidthChange,
		)
		pack(sizesVBox, prefItem.getWidget())
		######
		eventsVBox = gtk.VBox(spacing=10)
		page = StackPage()
		page.pageWidget = eventsVBox
		page.pageName = "events"
		page.pageTitle = _("Events")
		page.pageLabel = _("Events Text")
		page.pageIcon = ""
		subPages.append(page)
		###
		button = newSubPageButton(self, page, borderWidth=10)
		pack(optionsWidget, button)
		###
		prefItem = SpinPrefItem(
			ui,
			"rightPanelEventIconSize",
			5, 128,
			digits=1, step=1,
			label=_("Event Icon Size"),
			live=True,
			onChangeFunc=self.onEventIconSizeChange,
		)
		pack(eventsVBox, prefItem.getWidget())
		###
		pack(eventsVBox, self.eventItem.getOptionsWidget())
		######
		pluginsVBox = gtk.VBox(spacing=10)
		page = StackPage()
		page.pageWidget = pluginsVBox
		page.pageName = "plugins"
		page.pageTitle = _("Plugins")
		page.pageLabel = _("Plugins Text")
		page.pageIcon = ""
		subPages.append(page)
		###
		button = newSubPageButton(self, page, borderWidth=10)
		pack(optionsWidget, button)
		###
		pack(pluginsVBox, self.plugItem.getOptionsWidget())
		######
		prefItem = CheckPrefItem(
			ui,
			"mainWinRightPanelResizeOnToggle",
			label=_("Resize on show/hide\nfrom window controller"),
			tooltip="",
			live=True,
			onChangeFunc=None,
		)
		pack(optionsWidget, prefItem.getWidget())
		######
		self.optionsWidget = optionsWidget
		self.subPages = subPages
		return optionsWidget
