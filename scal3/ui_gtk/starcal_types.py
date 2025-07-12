from typing import Any, Protocol

from gi.repository import Gdk as gdk
from gi.repository import Gtk as gtk

from scal3.ui_gtk.customize import CustomizableCalObj
from scal3.ui_gtk.signals import SignalHandlerType

__all__ = ["MainWinType"]


class MainWinType(Protocol):
	w: gtk.ApplicationWindow
	app: gtk.Application

	def onStatusIconClick(self, _w: gtk.Widget | None = None) -> None: ...
	def getStatusIconPopupItems(self) -> list[gtk.MenuItem]: ...
	def dayInfoShow(self, _sig: SignalHandlerType | None = None) -> None: ...
	def eventSearchShow(
		self,
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None: ...
	def autoResize(self) -> None: ...
	def screenSizeChanged(self, rect: gdk.Rectangle) -> None: ...
	def statusIconUpdateTooltip(self) -> None: ...
	def goToday(self, _w: gtk.Widget | None = None) -> None: ...
	def selectDateShow(self, _w: gtk.Widget | None = None) -> None: ...
	def customizeShow(
		self,
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None: ...
	def prefShow(
		self,
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None: ...
	def eventManShow(
		self,
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None: ...
	def onExportClick(self, _w: gtk.Widget | None = None) -> None: ...
	def aboutShow(self, _w: gtk.Widget | None = None, _data: Any = None) -> None: ...
	def onQuitClick(
		self,
		_widget: gtk.Widget | None = None,
		_event: gdk.Event | None = None,
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
		_widget: gtk.Widget | None = None,
		_gevent: gdk.Event | None = None,
	) -> None: ...
