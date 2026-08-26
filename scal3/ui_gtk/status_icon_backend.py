"""GTK 4 status-icon policy."""

from __future__ import annotations

from typing import Any


def create_status_icon(owner: Any, mode: int) -> Any | None:
	# Gtk.StatusIcon was removed in GTK 4, so the tray/status icon is not
	# available here; only the Xfce panel applet backend (mode 3) is.
	if mode == 3:
		from scal3.ui_gtk.starcal_xfce_applet import XfceAppletStatusIcon

		return XfceAppletStatusIcon(owner)
	owner.statusIconMode = 0
	return None
