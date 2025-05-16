from __future__ import annotations

from scal3.ui_gtk import gdk, gtk, timeout_add

__all__ = ["setupMenuHideOnLeave"]


def setupMenuHideOnLeave(menu: gtk.Menu) -> None:
	from time import time as now

	def menuLeaveNotify(m: gtk.Menu, _e: gdk.Event) -> None:
		t0 = now()
		if t0 - m.lastLeaveNotify < 0.001:
			timeout_add(500, m.hide)
		m.lastLeaveNotify = t0

	menu.lastLeaveNotify = 0
	menu.connect("leave-notify-event", menuLeaveNotify)
