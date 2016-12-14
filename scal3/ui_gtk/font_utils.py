from gi.repository import Pango as pango
W_NORMAL = pango.Weight.NORMAL
S_NORMAL = pango.Style.NORMAL
BOLD = pango.Weight.BOLD
ITALIC = pango.Style.ITALIC

#import pango
#W_NORMAL = pango.WEIGHT_NORMAL
#S_NORMAL = pango.STYLE_NORMAL
#BOLD = pango.WEIGHT_BOLD
#ITALIC = pango.STYLE_ITALIC

pfontDecode = lambda pfont: [
	pfont.get_family(),
	pfont.get_weight()==BOLD,
	pfont.get_style()==ITALIC,
	pfont.get_size()/1024,
]

def pfontEncode(font):
	pfont = pango.FontDescription()
	pfont.set_family(font[0])
	pfont.set_weight(BOLD if font[1] else W_NORMAL)
	pfont.set_style(ITALIC if font[2] else S_NORMAL)
	pfont.set_size(int(font[3]*1024))
	return pfont

gfontDecode = lambda gfont: pfontDecode(pango.FontDescription(gfont))## gfont is a string like "Terafik 12"

gfontEncode = lambda font: pfontEncode(font).to_string()

getFontFamilyList = lambda widget: sorted(
	(
		f.get_name() for f in widget.get_pango_context().list_families()
	),
	key=str.upper,
)


