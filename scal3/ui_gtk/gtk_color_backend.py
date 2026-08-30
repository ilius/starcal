"""GTK 3 colour conversions."""

from __future__ import annotations

from scal3.color_utils import RGB
from scal3.ui_gtk import gdk

__all__ = ["gdkColorToRgb", "rgbToGdkColor", "rgbaToGdkRGBA"]


def rgbaToGdkRGBA(r: int, g: int, b: int, a: int = 255) -> gdk.RGBA:
	return gdk.RGBA(
		red=r / 255,
		green=g / 255,
		blue=b / 255,
		alpha=a / 255,
	)


def rgbToGdkColor(red: int, green: int, blue: int) -> gdk.Color:
	return gdk.Color(red * 257, green * 257, blue * 257)  # type: ignore[call-arg]


def gdkColorToRgb(color: gdk.RGBA) -> RGB:
	return RGB(
		int(color.red * 257),
		int(color.green * 257),
		int(color.blue * 257),
	)
