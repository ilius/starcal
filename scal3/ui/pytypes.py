from typing import TypedDict

from scal3.color_utils import ColorType
from scal3.font import Font


class WeekCalDayNumParamsDict(TypedDict):
	font: Font | None


class CalTypeParamsDict(TypedDict):
	pos: tuple[float, float]
	font: Font | None
	color: ColorType  # | None?


class DayCalTypeParamsDict(TypedDict):
	pos: tuple[float, float]
	font: Font | None
	color: ColorType  # | None?
	enable: bool
	xalign: str
	yalign: str


class DayCalNameTypeParamsDict(TypedDict):
	pos: tuple[float, float]
	font: Font | None
	color: ColorType  # | None?
	enable: bool = True
	xalign: str
	yalign: str
	abbreviate: bool
	uppercase: bool


class ButtonGeoDict(TypedDict):
	auto_rtl: bool
	size: float
	spacing: float
	pos: tuple[float, float]
	xalign: str
	yalign: str


class PieGeoDict(TypedDict):
	size: float
	thickness: float
	pos: tuple[float, float]
	xalign: str
	yalign: str
	startAngle: float
