#from xml.sax.saxutils import escape, unescape
def escape(data, entities={}):
	"""
	Escape &, <, and > in a string of data.

	You can escape other strings of data by passing a dictionary as
	the optional entities parameter.  The keys and values must all be
	strings; each key will be replaced with its corresponding value.
	"""

	# must do ampersand first
	data = data.replace("&", "&amp;")
	data = data.replace(">", "&gt;")
	data = data.replace("<", "&lt;")
	if entities:
		data = __dict_replace(data, entities)
	return data


def unescape(data, entities={}):
	"""
	Unescape &amp;, &lt;, and &gt; in a string of data.

	You can unescape other strings of data by passing a dictionary as
	the optional entities parameter.  The keys and values must all be
	strings; each key will be replaced with its corresponding value.
	"""
	data = data.replace("&lt;", "<")
	data = data.replace("&gt;", ">")
	if entities:
		data = __dict_replace(data, entities)
	# must do ampersand last
	return data.replace("&amp;", "&")
