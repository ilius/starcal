from scal3.utils import toStr
from scal3 import ui
from scal3.timeline import *

from scal3.ui_gtk.drawing import *


def drawBoxBG(cr, box, x, y, w, h):
	d = box.lineW
	cr.rectangle(x, y, w, h)
	if d == 0:
		fillColor(cr, box.color)
		return
	try:
		alpha = box.color[3]
	except IndexError:
		alpha = 255
	try:
		fillColor(cr, (
			box.color[0],
			box.color[1],
			box.color[2],
			int(alpha*boxInnerAlpha),
		))
	except cairo.Error:
		return
	###
	cr.set_line_width(0)
	cr.move_to(x, y)
	cr.line_to(x+w, y)
	cr.line_to(x+w, y+h)
	cr.line_to(x, y+h)
	cr.line_to(x, y)
	cr.line_to(x+d, y)
	cr.line_to(x+d, y+h-d)
	cr.line_to(x+w-d, y+h-d)
	cr.line_to(x+w-d, y+d)
	cr.line_to(x+d, y+d)
	cr.close_path()
	fillColor(cr, box.color)


def drawBoxBorder(cr, box, x, y, w, h):
	if box.hasBorder:
		if w > 2*boxMoveBorder and h > boxMoveBorder:
			b = boxMoveBorder
			bd = boxMoveLineW
			#cr.set_line_width(bd)
			cr.move_to(x+b-bd, y+h)
			cr.line_to(x+b-bd, y+b-bd)
			cr.line_to(x+w-b+bd, y+b-bd)
			cr.line_to(x+w-b+bd, y+h)
			cr.line_to(x+w-b, y+h)
			cr.line_to(x+w-b, y+b)
			cr.line_to(x+b, y+b)
			cr.line_to(x+b, y+h)
			cr.close_path()
			fillColor(cr, box.color)
			###
			bds = 0.7 * bd
			cr.move_to(x, y)
			cr.line_to(x+bds, y)
			cr.line_to(x+b+bds, y+b)
			cr.line_to(x+b, y+b+bds)
			cr.line_to(x, y+bds)
			cr.close_path()
			fillColor(cr, box.color)
			##
			cr.move_to(x+w, y)
			cr.line_to(x+w-bds, y)
			cr.line_to(x+w-b-bds, y+b)
			cr.line_to(x+w-b, y+b+bds)
			cr.line_to(x+w, y+bds)
			cr.close_path()
			fillColor(cr, box.color)
		else:
			box.hasBorder = False


def drawBoxText(cr, box, x, y, w, h, widget):
	## now draw the text
	## how to find the best font size based in the box's width and height,
	## and font family? FIXME
	## possibly write in many lines? or just in one line and wrap if needed?
	if box.text:
		#print(box.text)
		textW = 0.9 * w
		textH = 0.9 * h
		textLen = len(toStr(box.text))
		#print('textLen=%s'%textLen)
		avgCharW = float(textW if rotateBoxLabel == 0 else max(textW, textH)) / textLen
		if avgCharW > 3:## FIXME
			font = list(ui.getFont())
			layout = widget.create_pango_layout(box.text) ## a Pango.Layout object
			layout.set_font_description(pfontEncode(font))
			layoutW, layoutH = layout.get_pixel_size()
			#print('orig font size: %s'%font[3])
			normRatio = min(
				float(textW)/layoutW,
				float(textH)/layoutH,
			)
			rotateRatio = min(
				float(textW)/layoutH,
				float(textH)/layoutW,
			)
			if rotateBoxLabel != 0 and rotateRatio > normRatio:
				font[3] *= max(normRatio, rotateRatio)
				layout.set_font_description(pfontEncode(font))
				layoutW, layoutH = layout.get_pixel_size()
				fillColor(cr, fgColor)## before cr.move_to
				#print('x=%s, y=%s, w=%s, h=%s, layoutW=%s, layoutH=%s'\)
				#	%(x,y,w,h,layoutW,layoutH)
				cr.move_to(
					x + (w - rotateBoxLabel*layoutH)/2.0,
					y + (h + rotateBoxLabel*layoutW)/2.0,
				)
				cr.rotate(-rotateBoxLabel*pi/2)
				show_layout(cr, layout)
				try:
					cr.rotate(rotateBoxLabel*pi/2)
				except:
					print('counld not rotate by %s*pi/2 = %s'%(
						rotateBoxLabel,
						rotateBoxLabel*pi/2,
					))
			else:
				font[3] *= normRatio
				layout.set_font_description(pfontEncode(font))
				layoutW, layoutH = layout.get_pixel_size()
				fillColor(cr, fgColor)## before cr.move_to
				cr.move_to(
					x + (w-layoutW)/2.0,
					y + (h-layoutH)/2.0,
				)
				show_layout(cr, layout)



