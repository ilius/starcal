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


def gdkColorToRgb(gc):
	return (
		gc.red // 257,
		gc.green // 257,
		gc.blue // 257,
	)


#def htmlColorToGdk(hc):
#	return gdk.color_parse(hc)


def colorize(text, color):
	return '<span color="%s">%s</span>' % (
		rgbToHtmlColor(*color),
		text,
	)
