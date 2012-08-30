import pango

pfontDecode = lambda pfont: [
    pfont.get_family(),
    pfont.get_weight()==pango.WEIGHT_BOLD,
    pfont.get_style()==pango.STYLE_ITALIC,
    pfont.get_size()/1024,
]

def pfontEncode(font):
    pfont = pango.FontDescription()
    pfont.set_family(font[0])
    pfont.set_weight(pango.WEIGHT_BOLD if font[1] else pango.WEIGHT_NORMAL)
    pfont.set_style(pango.STYLE_ITALIC if font[2] else pango.STYLE_NORMAL)
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


