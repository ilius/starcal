from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
	from gi.repository import GObject
	from gi.repository import Gtk as gtk

	from scal3.pytypes import WeekStatusType
	from scal3.ui_gtk.signals import SignalHandlerType

__all__ = ["ColumnParent", "WeekCalType"]


class ColumnParent(Protocol):
	def set_child_packing(
		self,
		child: gtk.Widget,
		expand: bool,
		fill: bool,
		padding: int,
		pack_type: gtk.PackType,
	) -> None: ...


class WeekCalType(Protocol):
	w: gtk.Widget
	s: SignalHandlerType
	box: gtk.Box
	status: WeekStatusType | None
	cellIndex: int

	def updateStatus(self) -> None: ...
	def goBackward4(self, _obj: GObject.Object) -> None: ...
	def goBackward(self, _obj: GObject.Object) -> None: ...
	def goForward(self, _obj: GObject.Object) -> None: ...
	def goForward4(self, _obj: GObject.Object) -> None: ...
	def goToday(self, _w: GObject.Object | None = None) -> None: ...
