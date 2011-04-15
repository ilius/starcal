#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time

from scal2 import core
from scal2.locale_man import tr as _

from scal2.ui_gtk.drawing import *
from scal2.ui_gtk.mywidgets import MyColorButton

from scal2 import event_man
import gtk
from gtk import gdk

rootWin = gtk.gdk.get_default_root_window()
screenWidth = rootWin.get_size()[0]

class FloatingMsg(gtk.Widget):
    def on_realize(self, widget):
        self.animateStart()
    def __init__(self, text,
                       speed=100,
                       bgColor=(255, 255, 0),
                       textColor=(0, 0, 0),
                       refreshTime=10,
                       finishFunc=None,
                       finishOnClick=True,
                       createWindow=True):
        gtk.Widget.__init__(self)
        ## speed: pixels per second
        self.speed = speed
        self.bgColor = bgColor
        self.textColor = textColor
        self.refreshTime = refreshTime
        self.finishFunc = finishFunc
        self.isFinished = False
        if finishOnClick:
            self.connect('button-press-event', self.finish)
        ########
        if isinstance(text, str):
            text = text.decode('utf8')
        lines = []
        for line in text.split(u'\n'):
            line = line.strip()
            if line:
                lines.append(line)
        self.linesNum = len(lines)
        self.layoutList = [newTextLayout(self, line) for line in lines]
        self.rtlList = [self.isRtl(lines[i], self.layoutList[i])
                        for i in range(self.linesNum)]
        self.index = 0
        self.height = 30
        ########
        self.connect('expose-event', self.onExposeEvent)
        self.connect('realize', self.on_realize)
        ########
        if createWindow:
            self.win = gtk.Window(gtk.WINDOW_POPUP)#gtk.WINDOW_POPUP ## ????????????????
            self.win.add(self)
            self.win.set_decorated(False)
            self.win.set_property('skip-taskbar-hint', True)
            self.win.set_keep_above(True)
        else:
            self.win = False
    def isRtl(self, line, layout):
        for i in range(len(line)):
            if layout.index_to_pos(i)[2] != 0:
                return (layout.index_to_pos(i)[2] < 0)
        return False
    def updateLine(self):
        self.layout = self.layoutList[self.index]
        self.rtl = self.rtlList[self.index]
        self.rtlSign = 1 if self.rtl else -1
        size = self.layout.get_pixel_size()
        self.height = size[1]
        self.set_size_request(screenWidth, self.height)
        if self.win!=None:
            self.win.resize(screenWidth, self.height)
        self.textWidth = size[0]
        self.startXpos = -self.textWidth if self.rtl else screenWidth
        self.xpos = self.startXpos
    def finish(self, w=None, e=None):
        self.isFinished = True
        self.win.destroy()
        self.destroy()
        if self.finishFunc:
            self.finishFunc()
    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(
            self.get_parent_window(), 
            width=self.allocation.width, 
            height=self.allocation.height, 
            window_type=gdk.WINDOW_CHILD, 
            wclass=gdk.INPUT_OUTPUT, 
            event_mask=self.get_events() | gdk.EXPOSURE_MASK | gdk.BUTTON1_MOTION_MASK | gdk.BUTTON_PRESS_MASK
                                         | gdk.POINTER_MOTION_MASK | gdk.POINTER_MOTION_HINT_MASK
        )
        self.window.set_user_data(self)
        self.style.attach(self.window)#?????? Needed??
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)
    def onExposeEvent(self, widget, event):
        self.cr = self.window.cairo_create()
        #######
        self.cr.rectangle(0, 0, screenWidth, self.height)
        setColor(self.cr, self.bgColor)
        self.cr.fill()
        #######
        self.cr.move_to(self.xpos, 0)
        setColor(self.cr, self.textColor)
        self.cr.show_layout(self.layout)
    def animateStart(self):
        self.updateLine()
        self.startTime = time.time()
        self.animateUpdate()
    def animateUpdate(self):
        if self.isFinished:
            return
        gobject.timeout_add(self.refreshTime, self.animateUpdate)
        self.xpos = self.startXpos + (time.time()-self.startTime)*self.speed*self.rtlSign
        if self.xpos>screenWidth or self.xpos<-self.textWidth:
            if self.index >= self.linesNum-1:
                self.finish()
                return
            else:
                self.index += 1
                self.updateLine()
        self.queue_draw()
    def show(self):
        gtk.Widget.show(self)
        self.win.show()

class MyLabel(gtk.Widget):
    def __init__(self, bgColor, textColor):
        gtk.Widget.__init__(self)
        self.bgColor = bgColor
        self.textColor = textColor
        self.connect('expose-event', self.onExposeEvent)
    def set_label(self, text):
        self.text = text
        self.layout = newTextLayout(self, text)
        size = self.layout.get_pixel_size()
        self.height = size[1]
        self.width = size[0]
        self.set_size_request(self.width, self.height)
        self.rtl = self.isRtl()
        self.rtlSign = 1 if self.rtl else -1
    def do_realize(self):
        self.set_flags(self.flags() | gtk.REALIZED)
        self.window = gdk.Window(
            self.get_parent_window(), 
            width=self.allocation.width, 
            height=self.allocation.height, 
            window_type=gdk.WINDOW_CHILD, 
            wclass=gdk.INPUT_OUTPUT, 
            event_mask=self.get_events() | gdk.EXPOSURE_MASK | gdk.BUTTON1_MOTION_MASK | gdk.BUTTON_PRESS_MASK
                                         | gdk.POINTER_MOTION_MASK | gdk.POINTER_MOTION_HINT_MASK
        )
        self.window.set_user_data(self)
        self.style.attach(self.window)#?????? Needed??
        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)
    def onExposeEvent(self, widget, event):
        self.cr = self.window.cairo_create()
        #######
        self.cr.rectangle(0, 0, self.width, self.height)
        setColor(self.cr, self.bgColor)
        self.cr.fill()
        #######
        self.cr.move_to(0, 0)
        setColor(self.cr, self.textColor)
        self.cr.show_layout(self.layout)
    def isRtl(self):
        for i in range(len(self.text)):
            if self.layout.index_to_pos(i)[2] != 0:
                return (self.layout.index_to_pos(i)[2] < 0)
        return False



class NoFillFloatingMsgWindow(gtk.Window):
    def __init__(self, text,
                       speed=100,
                       bgColor=(255, 255, 0),
                       textColor=(0, 0, 0),
                       refreshTime=10,
                       finishFunc=None,
                       finishOnClick=True):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)#gtk.WINDOW_POPUP ## ????????????????
        self.set_decorated(False)
        self.set_property('skip-taskbar-hint', True)
        self.set_keep_above(True)
        self.label = MyLabel(bgColor, textColor)
        self.add(self.label)
        self.label.show()
        ## speed: pixels per second
        self.speed = speed
        self.refreshTime = refreshTime
        self.finishFunc = finishFunc
        self.isFinished = False
        if finishOnClick:
            self.connect('button-press-event', self.finish)
        ########
        if isinstance(text, str):
            text = text.decode('utf8')
        text = text.replace('\\n', '\n').replace('\\t', '\t')
        lines = []
        for line in text.split(u'\n'):
            line = line.strip()
            if line:
                lines.append(line)
        self.linesNum = len(lines)
        self.lines = lines
        self.index = 0
        ########
        self.connect('realize', lambda widget: self.animateStart())
    def updateLine(self):
        self.label.set_label(self.lines[self.index])
        self.startXpos = -self.label.width if self.label.rtl else screenWidth
        self.startTime = time.time()
    def finish(self, w=None, e=None):
        self.isFinished = True
        self.destroy()
        if self.finishFunc:
            self.finishFunc()
    def animateStart(self):
        self.updateLine()
        self.animateUpdate()
    def animateUpdate(self):
        if self.isFinished:
            return
        gobject.timeout_add(self.refreshTime, self.animateUpdate)
        xpos = int(self.startXpos + (time.time()-self.startTime)*self.speed*self.label.rtlSign)
        self.move(xpos, 0)
        self.resize(1, 1)
        if xpos>screenWidth or xpos<-self.label.width:
            if self.index >= self.linesNum-1:
                self.finish()
                return
            else:
                self.index += 1
                self.updateLine()


class FloatingMsgNotifierWidget(gtk.HBox):
    def __init__(self, notifier):
        self.notifier = notifier
        ##
        gtk.HBox.__init__(self)
        ## [_] Fill Screen Width       Speed [__]      BG Color [__]     Text Color [__]
        ##
        self.fillWidthCb = gtk.CheckButton(_('Fill Width'))
        self.pack_start(self.fillWidthCb, 0, 0)
        self.pack_start(gtk.Label(''), 1, 1)
        ##
        speedSpin = gtk.SpinButton()
        speedSpin.set_increments(1, 10)
        speedSpin.set_range(1, 999)
        speedSpin.set_digits(0)
        speedSpin.set_direction(gtk.TEXT_DIR_LTR)
        self.speedSpin = speedSpin
        self.pack_start(gtk.Label(_('Speed')), 0, 0)
        self.pack_start(speedSpin, 0, 0)
        self.pack_start(gtk.Label(''), 1, 1)
        ##
        self.bgColorButton = MyColorButton()
        self.pack_start(gtk.Label(_('BG Color')), 0, 0)
        self.pack_start(self.bgColorButton, 0, 0)
        self.pack_start(gtk.Label(''), 1, 1)
        ##
        self.textColorButton = MyColorButton()
        self.pack_start(gtk.Label(_('Text Color')), 0, 0)
        self.pack_start(self.textColorButton, 0, 0)
        self.pack_start(gtk.Label(''), 1, 1)
        ##
        self.updateWidget()
    def updateWidget(self):
        self.fillWidthCb.set_active(self.notifier.fillWidth)
        self.speedSpin.set_value(self.notifier.speed)
        self.bgColorButton.set_color(self.notifier.bgColor)
        self.textColorButton.set_color(self.notifier.textColor)
    def updateVars(self):
        self.notifier.fillWidth = self.fillWidthCb.get_active()
        self.notifier.speed = self.speedSpin.get_value()
        self.notifier.bgColor = self.bgColorButton.get_color()
        self.notifier.textColor = self.textColorButton.get_color()

def notify(notifier, finishFunc):## FIXME
    cls = FloatingMsg if notifier.fillWidth else NoFillFloatingMsgWindow
    text = notifier.event.summary
    if notifier.event.description:
        text = text + ': ' + notifier.event.description
    msg = cls(
        text,
        speed = notifier.speed,
        bgColor = notifier.bgColor,
        textColor = notifier.textColor,
        finishFunc = finishFunc
    )
    msg.show()


gobject.type_register(FloatingMsg)
gobject.type_register(MyLabel)
gobject.type_register(NoFillFloatingMsgWindow)

event_man.FloatingMsgNotifier.WidgetClass = FloatingMsgNotifierWidget
event_man.FloatingMsgNotifier.notify = notify


if __name__=='__main__':
    import sys
    if len(sys.argv)<2:
        sys.exit(1)
    text = ' '.join(sys.argv[1:])
    msg = NoFillFloatingMsgWindow(text, speed=200, finishFunc=gtk.main_quit)
    #msg = FloatingMsg(text, speed=200, finishFunc=gtk.main_quit)
    msg.show()
    gtk.main()


