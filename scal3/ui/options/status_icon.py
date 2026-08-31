from __future__ import annotations

from os.path import join

from scal3.ui.options._base import MAIN_CONF, OptionData

__all__ = ["confOptionsData"]

confOptionsData: list[OptionData] = [
	OptionData(
		name="statusIcon.digitalClockEnable",
		v3Name="showDigClockTr",
		flags=MAIN_CONF,
		type="bool",
		where="Preferences: ... (not usable)",
		desc="Show Digital Clock: On Status Icon",
		default=True,
	),
	OptionData(
		name="statusIcon.imagePath",
		v3Name="statusIconImage",
		flags=MAIN_CONF,
		type="str",
		where="Preferences: Status Icon",
		desc="Normal Days: Icon Path",
		default=join("status-icons", "dark-green.svg"),
	),
	OptionData(
		name="statusIcon.holidayImagePath",
		v3Name="statusIconImageHoli",
		flags=MAIN_CONF,
		type="str",
		where="Preferences: Status Icon",
		desc="Holidays: Icon Path",
		default=join("status-icons", "dark-red.svg"),
	),
	OptionData(
		name="statusIcon.fontFamilyEnable",
		v3Name="statusIconFontFamilyEnable",
		flags=MAIN_CONF,
		type="bool",
		where="Preferences: Status Icon",
		desc="[ ] Change font family to",
		default=False,
	),
	OptionData(
		name="statusIcon.fontFamily",
		v3Name="statusIconFontFamily",
		flags=MAIN_CONF,
		type="str | None",
		where="Preferences: Status Icon",
		desc="Font family",
		default=None,
	),
	OptionData(
		name="statusIcon.holidayFontColorEnable",
		v3Name="statusIconHolidayFontColorEnable",
		flags=MAIN_CONF,
		type="bool",
		where="Preferences: Status Icon",
		desc="Holiday font color",
		default=False,
	),
	OptionData(
		name="statusIcon.holidayFontColor",
		v3Name="statusIconHolidayFontColor",
		flags=MAIN_CONF,
		type="ColorType | None",
		where="Preferences: Status Icon",
		desc="Holiday font color",
		default=None,
	),
	OptionData(
		name="statusIcon.localizeNumber",
		v3Name="statusIconLocalizeNumber",
		flags=MAIN_CONF,
		type="bool",
		where="Preferences: Status Icon",
		desc="Localize the number",
		default=True,
	),
	OptionData(
		name="statusIcon.fixedSizeEnable",
		v3Name="statusIconFixedSizeEnable",
		flags=MAIN_CONF,
		type="bool",
		where="Preferences: Status Icon",
		desc="[ ] Fixed Size",
		default=False,
	),
	OptionData(
		name="statusIcon.fixedSizeWH",
		v3Name="statusIconFixedSizeWH",
		flags=MAIN_CONF,
		type="tuple[int, int]",
		where="Preferences: Status Icon",
		desc="Fixed Size (width, height)",
		default=(24, 24),
	),
	OptionData(
		name="statusIcon.pluginsText",
		v3Name="pluginsTextStatusIcon",
		flags=MAIN_CONF,
		type="bool",
		where="Preferences: Status Icon",
		desc="Show in Status Icon (for today)",
		default=False,
	),
]
