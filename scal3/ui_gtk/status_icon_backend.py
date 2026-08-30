"""GTK 3 status-icon implementation."""

from __future__ import annotations

from typing import Any

from scal3.app_info import APP_DESC

__all__ = ["create_status_icon"]


def create_status_icon(owner: Any, mode: int) -> Any | None:
	if mode == 3:
		from scal3.ui_gtk.starcal_xfce_applet import XfceAppletStatusIcon

		return XfceAppletStatusIcon(owner)

	if mode != 2:
		return None

	from scal3.ui_gtk.starcal_funcs import onStatusIconPress, shouldUseAppIndicator

	if shouldUseAppIndicator():
		from scal3.ui_gtk.starcal_appindicator import IndicatorStatusIconWrapper

		return IndicatorStatusIconWrapper(owner)

	from scal3.ui_gtk import gtk

	status_icon = gtk.StatusIcon()
	status_icon.set_title(APP_DESC)
	status_icon.set_visible(True)
	status_icon.connect("button-press-event", onStatusIconPress)
	status_icon.connect("activate", owner.onStatusIconClick)
	status_icon.connect("popup-menu", owner.statusIconPopup)
	return status_icon
