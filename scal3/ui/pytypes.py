from __future__ import annotations

from typing import TYPE_CHECKING, NotRequired, TypedDict

from scal3.font import Font

if TYPE_CHECKING:
	from scal3.color_utils import RawColor
	from scal3.font import FontTuple

__all__ = [
	"ButtonGeoDict",
	"CalTypeParamsDict",
	"CustomizableToolBoxDict",
	"DayCalNameTypeParamsDict",
	"DayCalTypeParamsDict",
	"DictWithFont",
	"GenericTypeParamsDict",
	"PieGeoDict",
	"WeekCalDayNumParamsDict",
]

type FontType = FontTuple | Font | None


class DictWithFont(TypedDict):
	font: FontType


class WeekCalDayNumParamsDict(TypedDict):
	font: FontType


class CalTypeParamsDict(TypedDict):
	pos: tuple[float, float]
	font: FontType
	color: RawColor  # | None?


class DayCalTypeParamsDict(TypedDict):
	pos: tuple[float, float]
	font: FontType
	color: RawColor  # | None?
	enable: bool
	xalign: str
	yalign: str


class DayCalNameTypeParamsDict(TypedDict):
	pos: tuple[float, float]
	font: FontType
	color: RawColor  # | None?
	enable: bool
	xalign: str
	yalign: str
	abbreviate: bool
	uppercase: bool


class GenericTypeParamsDict(TypedDict):
	pos: tuple[float, float]
	font: FontType
	color: RawColor  # | None?
	enable: NotRequired[bool]
	xalign: NotRequired[str]
	yalign: NotRequired[str]
	abbreviate: NotRequired[bool]
	uppercase: NotRequired[bool]


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


class CustomizableToolBoxDict(TypedDict):
	items: list[tuple[str, bool]]
	iconSize: NotRequired[str]  # just for compatibilty
	iconSizePixel: float
	buttonBorder: int
	buttonPadding: int
	preferIconName: bool
