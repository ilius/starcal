from __future__ import annotations

from scal3.ui.options._base import MAIN_CONF, OptionData

__all__ = ["confOptionsData"]

confOptionsData: list[OptionData] = [
	OptionData(
		name="maxDayCacheSize",
		v3Name="maxDayCacheSize",
		flags=MAIN_CONF,
		type="int",
		valid="IntSpin(100, 9999, 10)",
		where="Preferences: Advanced",
		desc="Days maximum cache size",
		default=100,
	),
	OptionData(
		name="eventDayView.timeFormat",
		v3Name="eventDayViewTimeFormat",
		flags=MAIN_CONF,
		type="str",
		where="Preferences: Advanced",
		desc="Event Time Format",
		default="HM$",
	),
	OptionData(
		name="cellMenuHorizontalOffset",
		v3Name="cellMenuXOffset",
		flags=MAIN_CONF,
		type="int",
		valid="IntSpin(0, 999, 1)",
		where="Preferences: Advanced",
		desc="Horizontal offset for day right-click menu",
		default=0,
	),
]
