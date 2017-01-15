#from scal3.locale_man import tr as _
from scal3.ui_gtk import *


class AboutDialog(gtk.AboutDialog):
	def __init__(
		self,
		name="",
		version="",
		title="",
		authors=[],
		comments="",
		license="",
		website="",
		**kwargs
	):
		gtk.AboutDialog.__init__(self, **kwargs)
		self.set_name(name)
		self.set_program_name(name)
		self.set_version(version)
		self.set_title(title)  # must call after set_name and set_version !
		self.set_authors(authors)
		self.set_comments(comments)
		if license:
			self.set_license(license)
			self.set_wrap_license(True)
		if website:
			self.set_website(website)  # A plain label (not link)
