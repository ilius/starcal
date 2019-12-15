#!/usr/bin/env python3
#from scal3.locale_man import tr as _
from scal3.ui_gtk import *
from scal3.ui_gtk.utils import pixbufFromFile


class AboutDialog(gtk.AboutDialog):
	def __init__(
		self,
		name: str = "",
		version: str = "",
		title: str = "",
		authors: "List[str]" = [],
		comments: str = "",
		license: str = "",
		website: str = "",
		logo: "GdkPixbuf.Pixbuf" = None,
		**kwargs
	):
		gtk.AboutDialog.__init__(self, **kwargs)
		self.set_name(name)
		self.set_program_name(name)
		self.set_version("Version:" + " <b>" + version + "</b>")
		self.set_title(title)  # must call after set_name and set_version !
		self.set_authors(authors)
		self.set_comments(comments)
		if license:
			self.set_license(license)
			self.set_wrap_license(True)
		if website:
			self.set_website(website)  # A plain label (not link)
		if logo is None:
			logo = pixbufFromFile("empty-pixel.png")
		self.set_logo(logo)
