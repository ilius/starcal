from scal3.ui_gtk import *
from scal3.ui_gtk.utils import hideList


class WizardWindow(gtk.Window):
	stepClasses = []

	def __init__(self, title):
		gtk.Window.__init__(self)
		self.set_title(title)
		self.connect('delete-event', lambda obj, e: self.destroy())
		self.connect('key-press-event', self.keyPress)
		self.vbox = gtk.VBox()
		self.add(self.vbox)
		####
		self.steps = []
		for cls in self.stepClasses:
			step = cls(self)
			self.steps.append(step)
			pack(self.vbox, step, 1, 1)
		self.stepIndex = 0
		####
		self.buttonBox = gtk.HButtonBox()
		self.buttonBox.set_layout(gtk.ButtonBoxStyle.END)
		self.buttonBox.set_spacing(15)
		self.buttonBox.set_border_width(15)
		pack(self.vbox, self.buttonBox)
		####
		self.showStep(0)
		self.vbox.show()
		#self.vbox.pack_end(
		#print(id(self.get_action_area()))

	def keyPress(self, arg, gevent):
		kname = gdk.keyval_name(gevent.keyval).lower()
		if kname == 'escape':
			self.destroy()
		return True

	def showStep(self, stepIndex, *args):
		step = self.steps[stepIndex]
		step.run(*args)
		hideList(self.steps)
		step.show()
		self.stepIndex = stepIndex
		###
		bbox = self.buttonBox
		for child in bbox.get_children():
			child.destroy()
		for label, func in step.buttons:
			#print(label, func)
			button = gtk.Button(label)
			button.connect('clicked', func)
			bbox.add(button)
			#pack(bbox, button)
		bbox.show_all()
