from typing import Any, Protocol

from gi.repository import Gdk as gdk
from gi.repository import Gtk as gtk

from scal3.ui_gtk.customize import CustomizableCalObj
from scal3.ui_gtk.signals import SignalHandlerType

__all__ = ["MainWinType"]


type OptWidget = gtk.Widget | None
type OptEvent = gdk.Event | None


class MainWinType(Protocol):
	w: gtk.ApplicationWindow
	app: gtk.Application

	def onStatusIconClick(self, _w: OptWidget = None) -> None: ...
	def getStatusIconPopupItems(self) -> list[gtk.MenuItem]: ...
	def dayInfoShow(self, _sig: SignalHandlerType | None = None) -> None: ...
	def eventSearchShow(
		self,
		_widget: OptWidget = None,
		_gevent: OptEvent = None,
	) -> None: ...
	def autoResize(self) -> None: ...
	def screenSizeChanged(self, rect: gdk.Rectangle) -> None: ...
	def statusIconUpdateTooltip(self) -> None: ...
	def goToday(self, _w: OptWidget = None) -> None: ...
	def selectDateShow(self, _w: OptWidget = None) -> None: ...
	def customizeShow(
		self,
		_widget: OptWidget = None,
		_gevent: OptEvent = None,
	) -> None: ...
	def prefShow(
		self,
		_widget: OptWidget = None,
		_gevent: OptEvent = None,
	) -> None: ...
	def eventManShow(
		self,
		_widget: OptWidget = None,
		_gevent: OptEvent = None,
	) -> None: ...
	def onExportClick(self, _w: OptWidget = None) -> None: ...
	def aboutShow(self, _w: OptWidget = None, _data: Any = None) -> None: ...
	def onQuitClick(
		self,
		_widget: OptWidget = None,
		_event: OptEvent = None,
	) -> None: ...

	def childButtonPress(
		self,
		widget: gtk.Widget,  # noqa: ARG002
		gevent: gdk.EventButton,
	) -> bool: ...

	def menuMainPopup(
		self,
		_sig: SignalHandlerType,
		x: int,
		y: int,
		item: CustomizableCalObj,
	) -> None: ...

	def menuCellPopup(
		self,
		_sig: SignalHandlerType,
		x: int,
		y: int,
		item: CustomizableCalObj,
	) -> None: ...

	@staticmethod
	def prefUpdateBgColor(_sig: SignalHandlerType) -> None: ...

	@staticmethod
	def getStatusIconTooltip() -> str: ...

	def getMainWinMenuItem(self) -> gtk.MenuItem: ...
	@staticmethod
	def dayCalWinShow(
		_widget: OptWidget = None,
		_gevent: OptEvent = None,
	) -> None: ...
