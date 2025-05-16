from scal3 import logger

log = logger.get()

from scal3.ui_gtk import VBox, gdk, gtk, pack
from scal3.ui_gtk.mywidgets.buttonbox import MyHButtonBox
from scal3.ui_gtk.mywidgets.dialog import MyDialog
from scal3.ui_gtk.stack import MyStack, StackPage

__all__ = ["WizardWindow"]


class WizardWindow(gtk.Window, MyDialog):
	stepClasses = []

	def __init__(self, title: str) -> None:
		gtk.Window.__init__(self)
		self.set_title(title)
		self.connect("delete-event", lambda _w, _e: self.destroy())
		self.connect("key-press-event", self.onKeyPress)
		self.vbox = VBox()
		self.stack = MyStack(
			header=False,
		)
		pack(self.vbox, self.stack, 1, 1)
		self.add(self.vbox)
		self.steps = []
		self.stepIndex = 0
		# ----
		for index, cls in enumerate(self.stepClasses):
			step = cls(self)
			self.steps.append(step)
			# --
			page = StackPage()
			page.pageWidget = step
			page.pageParent = str(index - 1) if index > 0 else ""
			page.pageName = str(index)
			page.pagePath = str(index)
			page.pageTitle = step.desc
			page.pageLabel = step.desc
			page.pageIcon = ""
			page.pageExpand = True
			self.stack.addPage(page)
		# ----
		self.buttonBox = MyHButtonBox()
		self.buttonBox.set_spacing(15)
		self.buttonBox.set_border_width(15)
		pack(self.vbox, self.buttonBox)
		# ----
		self.showStep(0)
		self.show_all()
		# log.debug(id(self.get_action_area()))

	def onKeyPress(self, _widget: gtk.Widget, gevent: gdk.EventKey) -> bool:
		kname = gdk.keyval_name(gevent.keyval).lower()
		if kname == "escape":
			self.destroy()
		return True

	def showStep(self, stepIndex: int, *args) -> None:
		backward = stepIndex < self.stepIndex
		self.stack.gotoPage(str(stepIndex), backward=backward)
		step = self.steps[stepIndex]
		step.run(*args)
		self.stepIndex = stepIndex
		# ---
		bbox = self.buttonBox
		for child in bbox.get_children():
			child.destroy()
		for label, func in step.buttons:
			button = gtk.Button(label=label)
			button.connect("clicked", func)
			bbox.add(button)
			# pack(bbox, button)
		bbox.show_all()
