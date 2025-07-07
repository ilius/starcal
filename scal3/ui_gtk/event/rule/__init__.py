# class MultiValueRule(gtk.Box):
# 	def __init__(self, rule, ValueWidgetClass):
# 		from scal3.ui_gtk.utils import labelImageButton
# 		self.rule = rule
# 		self.ValueWidgetClass = ValueWidgetClass
# 		# --
# 		gtk.Box.__init__(self, orientation=gtk.Orientation.HORIZONTAL)
# 		self.widgetsBox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
# 		pack(self, self.widgetsBox)
# 		# --
# 		self.removeButton = labelImageButton(
# 			label=_("_Remove"),
# 			imageName="list-remove.svg",
# 		)
# 		self.removeButton.connect("clicked", self.removeLastWidget)
# 		# --
# 		self.removeButton.hide()-- FIXME.

# 	def removeLastWidget(self, obj=None):

# 	def addWidget(self, obj=None):
# 		widget = self.ValueWidgetClass()
