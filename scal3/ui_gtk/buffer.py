"""
Thanks to "Pier Carteri" <m3tr0@dei.unipd.it> for program Py_Shell.py
"""


class GtkBufferFile:
	"""
	Implements a file-like object for redirect the stream to the buffer
	"""

	def __init__(self, buff, tag):
		self.buffer = buff
		self.tag = tag

	def write(self, text):
		"""
		Write text into the buffer and apply self.tag
		"""
		#text = text.replace("\x00", "")
		self.buffer.insert_with_tags(
			self.buffer.get_end_iter(),
			text,
			self.tag,
		)

	def writelines(self, l):
		return list(map(self.write, l))

	def flush(self):
		return None

	def isatty(self):
		return False
