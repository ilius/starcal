from __future__ import annotations

from typing import TYPE_CHECKING

from scal3.locale_man import tr as _
from scal3.ui_gtk import gtk, pack
from scal3.ui_gtk.event import common

if TYPE_CHECKING:
	from scal3.event_lib.menstrual import MenstrualFertileEvent

__all__ = ["WidgetClass"]


class WidgetClass(common.WidgetClass):
	_event: MenstrualFertileEvent

	def __init__(self, event: MenstrualFertileEvent) -> None:
		common.WidgetClass.__init__(self, event)
		label = gtk.Label(
			label=_(
				"Derived prediction generated from the recorded periods. "
				"Change the cycle settings in the group editor.",
			),
		)
		label.set_xalign(0)
		label.set_line_wrap(True)
		pack(self, label)
