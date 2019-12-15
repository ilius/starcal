#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from scal3.color_utils import rgbToHtmlColor
from gi.repository import Gdk as gdk


def rgbToGdkColor(r, g, b, a=None):
	"""
	r, g, b are in range(256)
	"""
	return gdk.Color(
		int(r * 257),
		int(g * 257),
		int(b * 257),
	)


def rgbaToGdkRGBA(r, g, b, a=255):
	return gdk.RGBA(
		red=r / 255,
		green=g / 255,
		blue=b / 255,
		alpha=a / 255,
	)


def gdkColorToRgb(gc):
	assert isinstance(gc, gdk.RGBA)
	return (
		int(gc.red * 257),
		int(gc.green * 257),
		int(gc.blue * 257),
	)


#def htmlColorToGdk(hc):
#	return gdk.color_parse(hc)


#def gdkColorToHtml(gc):
#	return f"#{gc.red/256:02x}{gc.green/256:02x}{gc.blue/256:02x}"
