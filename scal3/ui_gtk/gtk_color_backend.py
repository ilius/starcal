"""GTK 4 colour conversions."""

from __future__ import annotations

from scal3.color_utils import RGB
from scal3.ui_gtk import gdk


def rgbaToGdkRGBA(r: int, g: int, b: int, a: int = 255) -> gdk.RGBA:
	return gdk.RGBA(
		red=r / 255,
		green=g / 255,
		blue=b / 255,
		alpha=a / 255,
	)


def rgbToGdkColor(red: int, green: int, blue: int) -> gdk.RGBA:
	return rgbaToGdkRGBA(red, green, blue)


def gdkColorToRgb(color: gdk.RGBA) -> RGB:
	return RGB(
		int(color.red * 255),
		int(color.green * 255),
		int(color.blue * 255),
	)
