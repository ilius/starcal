#!/usr/bin/env python3
from gi.repository import Pango as pango
from scal3 import ui

W_NORMAL = pango.Weight.NORMAL
S_NORMAL = pango.Style.NORMAL
BOLD = pango.Weight.BOLD
ITALIC = pango.Style.ITALIC

#import pango
#W_NORMAL = pango.WEIGHT_NORMAL
#S_NORMAL = pango.STYLE_NORMAL
#BOLD = pango.WEIGHT_BOLD
#ITALIC = pango.STYLE_ITALIC


def pfontDecode(pfont):
	return ui.Font(
		family=pfont.get_family(),
		bold=pfont.get_weight() == BOLD,
		italic=pfont.get_style() == ITALIC,
		size=pfont.get_size() / 1024,
	)


def pfontEncode(font):
	pfont = pango.FontDescription()
	pfont.set_family(font.family)
	pfont.set_weight(BOLD if font.bold else W_NORMAL)
	pfont.set_style(ITALIC if font.italic else S_NORMAL)
	pfont.set_size(int(font.size * 1024))
	return pfont


def gfontDecode(gfont):
	# gfont is a string like "FreeSans 12"
	return pfontDecode(pango.FontDescription(gfont))


def gfontEncode(font):
	return pfontEncode(font).to_string()


def getFontFamilyList(widget):
	return sorted(
		(
			f.get_name()
			for f in widget.get_pango_context().list_families()
		),
		key=str.upper,
	)
