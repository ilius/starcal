from __future__ import annotations

from gi.repository import Gdk as gdk

from scal3.color_utils import RGB

__all__ = [
	"gdkColorToRgb",
	"rgbaToGdkRGBA",
]


def rgbaToGdkRGBA(r: int, g: int, b: int, a: int = 255) -> gdk.RGBA:
	return gdk.RGBA(
		red=r / 255,
		green=g / 255,
		blue=b / 255,
		alpha=a / 255,
	)


def rgbToGdkColor(red: int, green: int, blue: int) -> gdk.Color:
	return gdk.Color(  # type: ignore[call-arg]
		int(red * 257),
		int(green * 257),
		int(blue * 257),
	)


def gdkColorToRgb(gc: gdk.RGBA) -> RGB:
	assert isinstance(gc, gdk.RGBA), f"{gc=}"
	return RGB(
		int(gc.red * 257),
		int(gc.green * 257),
		int(gc.blue * 257),
	)


# def htmlColorToGdk(hc):
# 	return gdk.color_parse(hc)


# def gdkColorToHtml(gc):
# 	return f"#{gc.red/256:02x}{gc.green/256:02x}{gc.blue/256:02x}"
