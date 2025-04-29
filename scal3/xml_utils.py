# from xml.sax.saxutils import escape, unescape


from __future__ import annotations

__all__ = ["escape"]


def escape(data, entities: dict | None = None):  # noqa: ARG001
	"""
	Escape &, <, and > in a string of data.

	You can escape other strings of data by passing a dictionary as
	the optional entities parameter.  The keys and values must all be
	strings; each key will be replaced with its corresponding value.
	"""
	# must do ampersand first
	data = data.replace("&", "&amp;")
	data = data.replace(">", "&gt;")
	return data.replace("<", "&lt;")
	# if entities:
	# 	data = __dict_replace(data, entities) # FIXME


def unescape(data, entities: dict | None = None):  # noqa: ARG001
	"""
	Unescape &amp;, &lt;, and &gt; in a string of data.

	You can unescape other strings of data by passing a dictionary as
	the optional entities parameter.  The keys and values must all be
	strings; each key will be replaced with its corresponding value.
	"""
	data = data.replace("&lt;", "<")
	data = data.replace("&gt;", ">")
	# if entities:
	# 	data = __dict_replace(data, entities) # FIXME
	# must do ampersand last
	return data.replace("&amp;", "&")
