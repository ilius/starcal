from __future__ import annotations

from typing import TYPE_CHECKING, Any

from scal3 import logger

log = logger.get()


from scal3 import core, ui
from scal3.event_lib.group import EventGroup
from scal3.format_time import compileTmFormat
from scal3.json_utils import dataToPrettyJson
from scal3.locale_man import tr as _
from scal3.s_object import SObjBinaryModel
from scal3.time_utils import getJhmsFromEpoch
from scal3.ui_gtk import Dialog, gtk, pack, pango
from scal3.ui_gtk import gtk_ud as ud
from scal3.ui_gtk.cal_obj_base import CalObjWidget
from scal3.ui_gtk.event.utils import checkEventsReadOnly
from scal3.ui_gtk.mywidgets.text_widgets import ReadOnlyTextView
from scal3.ui_gtk.utils import dialog_add_button, labelImageButton

if TYPE_CHECKING:
	from scal3.event_lib.pytypes import EventType

__all__ = ["EventHistoryDialog"]

historyTimeBinFmt = compileTmFormat("%Y/%m/%d    %H:%M:%S")

modifySymbol = "ⓜ"
addSymbol = "⊕"
removeSymbol = "⊖"


def _unnestStep(dst: dict[str, Any], src: dict[str, Any], path: str) -> None:
	if path:
		path += "."
	for key, value in src.items():
		_unnestStep(dst, value, path + key)


def unnest(src: Any) -> dict[str, Any]:
	if not isinstance(src, dict):
		return src  # type: ignore[no-any-return]
	dst: dict[str, Any] = {}
	_unnestStep(dst, src, "")
	return dst


class EventHistoryDialog(CalObjWidget):
	textViewTypes = [
		"Change Table",
		"Full Table",
		"After change (Text)",
		"After change (JSON)",
		"After change (Plain JSON)",
		"Before change (Text)",
		"Before change (JSON)",
		"Before change (Plain JSON)",
		"Change (JSON Diff)",
	]

	def __init__(
		self,
		event: EventType,
		transient_for: gtk.Window | None = None,
	) -> None:
		checkEventsReadOnly()
		self.dialog = Dialog(transient_for=transient_for)
		self.w: gtk.Widget = self.dialog
		self.dialog.set_title(_("History") + ": " + event.summary)
		self._event = event
		self.objectCache: dict[str, dict[str, Any]] = {}  # hash(str) -> data(dict)

		dialog_add_button(
			self.dialog,
			res=gtk.ResponseType.OK,
			imageName="window-close.svg",
			label=_("_Close"),
		)

		self.dialog.connect("response", self.onResponse)

		treev = gtk.TreeView()
		treev.set_headers_clickable(True)
		treeModel = gtk.ListStore(
			str,  # hashBefore (hidden)
			str,  # hashAfter (hidden)
			str,  # formatted date & time
			str,  # change msg (names or the number of changed params)
		)
		treev.set_model(treeModel)
		treev.connect("cursor-changed", self.treeviewCursorChanged)
		# treev.connect("button-press-event", self.treeviewCursorChanged)
		# FIXME: what is the signal for deselecting / unselecting a row?
		self.treeModel = treeModel
		self.treev = treev

		treevSwin = gtk.ScrolledWindow()
		treevSwin.add(treev)
		treevSwin.set_policy(
			gtk.PolicyType.AUTOMATIC,
			gtk.PolicyType.AUTOMATIC,
		)

		hpan = gtk.HPaned()
		hpan.add1(treevSwin)
		leftVbox = gtk.Box(orientation=gtk.Orientation.VERTICAL)
		hpan.add2(leftVbox)
		hpan.set_position(600)
		pack(self.dialog.vbox, hpan, expand=True, fill=True)

		actionBox = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=5)
		pack(leftVbox, actionBox, padding=30)

		# revertButton = labelImageButton(
		# 	label=_("Revert this vhange"),
		# 	imageName="edit-undo.svg",
		# )
		# revertButton.connect("clicked", self.onRevertClick)
		# pack(actionBox, revertButton, padding=1)
		# self.revertButton = revertButton

		checkoutAfterButton = labelImageButton(
			label=_("Select revision after this change"),
			imageName="edit-undo.svg",
		)
		checkoutAfterButton.connect("clicked", self.onCheckoutAfterClick)
		pack(actionBox, checkoutAfterButton, padding=1)
		self.checkoutAfterButton = checkoutAfterButton

		checkoutBeforeButton = labelImageButton(
			label=_("Select revision before this change"),
			imageName="edit-undo.svg",
		)
		checkoutBeforeButton.connect("clicked", self.onCheckoutBeforeClick)
		pack(actionBox, checkoutBeforeButton, padding=1)
		self.checkoutBeforeButton = checkoutBeforeButton

		self.setButtonsSensitive(False)

		combo = gtk.ComboBoxText()
		for text in self.textViewTypes:
			combo.append_text(_(text))
		combo.set_active(1)
		combo.connect("changed", self.viewTypeComboChanged)
		self.viewTypeCombo = combo

		textTypeHbox = gtk.Box(orientation=gtk.Orientation.HORIZONTAL)
		pack(textTypeHbox, gtk.Label(label=_("View type") + ": "))
		pack(textTypeHbox, self.viewTypeCombo)
		pack(leftVbox, textTypeHbox)

		self.textview = ReadOnlyTextView()
		self.textview.set_wrap_mode(gtk.WrapMode.NONE)
		self.textview.set_justification(gtk.Justification.LEFT)
		self.textbuff = self.textview.get_buffer()

		cmpTreev = gtk.TreeView()
		cmpTreev.set_headers_clickable(True)
		cmpTrees = gtk.ListStore(
			str,  # change symbol (modifySymbol, addSymbol, removeSymbol, "")
			str,  # key
			str,  # old value
			str,  # new value
		)
		cmpTreev.set_model(cmpTrees)
		# cmpTreev.connect("cursor-changed", self.cmpTreeviewCursorChanged)
		self.cmpTrees = cmpTrees
		self.cmpTreev = cmpTreev

		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title="", cell_renderer=cell, text=0)
		col.set_resizable(False)
		cmpTreev.append_column(col)

		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Key"), cell_renderer=cell, text=1)
		col.set_resizable(False)
		cmpTreev.append_column(col)

		wrap_width = 500
		# despite the setColumnWidth handler, this inital wrap_width is needed
		# 500px works with a typical display size (width >= 1200 px)
		# FIXME: but how to calculate the optimal inital wrap_width??

		cell = gtk.CellRendererText(
			wrap_mode=pango.WrapMode.WORD_CHAR,
			wrap_width=wrap_width,
		)
		col = gtk.TreeViewColumn(title=_("Old Value"), cell_renderer=cell, text=2)
		col.set_resizable(True)
		col.connect_after("notify::width", self.setColumnWidth, cell)
		cmpTreev.append_column(col)

		cell = gtk.CellRendererText(
			wrap_mode=pango.WrapMode.WORD_CHAR,
			wrap_width=wrap_width,
		)
		col = gtk.TreeViewColumn(title=_("New Value"), cell_renderer=cell, text=3)
		col.set_resizable(True)
		col.connect_after("notify::width", self.setColumnWidth, cell)
		cmpTreev.append_column(col)

		leftSwin = gtk.ScrolledWindow()
		leftSwin.set_policy(
			gtk.PolicyType.AUTOMATIC,
			gtk.PolicyType.AUTOMATIC,
		)
		pack(leftVbox, leftSwin, expand=True, fill=True)
		self.leftSwin = leftSwin

		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Time"), cell_renderer=cell, text=2)
		treev.append_column(col)

		cell = gtk.CellRendererText()
		col = gtk.TreeViewColumn(title=_("Change Summary"), cell_renderer=cell, text=3)
		treev.append_column(col)
		col.set_property("expand", True)

		self.load()
		self.dialog.vbox.show_all()
		self.dialog.resize(ud.workAreaW, int(ud.workAreaH * 0.9))

	def onResponse(self, _w: Any, _e: Any) -> None:
		self.hide()
		ud.windowList.broadcastConfigChange()

	@staticmethod
	def setColumnWidth(
		col: gtk.TreeViewColumn,
		_widthParam: Any,
		cell: gtk.CellRenderer,
	) -> None:
		width = col.get_width()
		cell.set_property("wrap_width", width)

	def treeviewCursorChanged(self, _treev: Any, _gevent: Any = None) -> None:
		self.updateViewType()

	def viewTypeComboChanged(self, _combo: Any) -> None:
		self.updateViewType()

	def setButtonsSensitive(self, sensitive: bool) -> None:
		# self.revertButton.set_sensitive(sensitive)
		self.checkoutAfterButton.set_sensitive(sensitive)
		self.checkoutBeforeButton.set_sensitive(sensitive)

	def updateViewType(self) -> None:
		pathObj = self.treev.get_cursor()[0]
		if not pathObj:
			self.setButtonsSensitive(False)
			return
		path = pathObj.get_indices()
		assert len(path) == 1
		self.setButtonsSensitive(True)
		index = path[0]
		row = self.treeModel[index]
		hashBefore = row[0]
		hashAfter = row[1]

		viewTypeIndex = self.viewTypeCombo.get_active()
		if viewTypeIndex == -1:
			return
		viewType = self.textViewTypes[viewTypeIndex]

		if viewType in {"Change Table", "Full Table"}:
			self.updateTableViewType(viewType, hashBefore, hashAfter)
		else:
			self.updateTextViewType(viewType, hashBefore, hashAfter)

	def updateTableViewType(
		self,
		viewType: str,
		hashBefore: str,
		hashAfter: str,
	) -> None:
		treeModel = self.cmpTrees
		treeModel.clear()

		if viewType == "Change Table":
			if hashBefore:
				diff = self.extractChangeDiff(hashBefore, hashAfter)
				for key in sorted(diff):
					(valueBefore, valueAfter) = diff[key]
					treeModel.append(
						[modifySymbol, key, str(valueBefore), str(valueAfter)],
					)
		elif viewType == "Full Table":
			for row in self.extractFullTable(hashBefore, hashAfter):
				treeModel.append(row)
		else:
			raise ValueError(f"unexpected {viewType=}")

		self.setScrolledWinChild(self.cmpTreev)

	def updateTextViewType(
		self,
		viewType: str,
		hashBefore: str,
		hashAfter: str,
	) -> None:
		event = self._event
		text = ""
		if viewType == "After change (Text)":
			if hashAfter:
				text = event.getRevision(hashAfter).getInfo()
		elif viewType == "Before change (Text)":
			if hashBefore:
				text = event.getRevision(hashBefore).getInfo()
		elif viewType == "After change (JSON)":
			if hashAfter:
				text = dataToPrettyJson(event.getRevision(hashAfter).getDict())
		elif viewType == "After change (Plain JSON)":
			if hashAfter:
				text = dataToPrettyJson(self.getObjectData(hashAfter))
		elif viewType == "Before change (JSON)":
			if hashBefore:
				text = dataToPrettyJson(event.getRevision(hashBefore).getDict())
		elif viewType == "Before change (Plain JSON)":
			if hashBefore:
				text = dataToPrettyJson(self.getObjectData(hashBefore))
		elif viewType == "Change (JSON Diff)":
			if hashBefore and hashAfter:
				diff = self.extractChangeDiff(hashBefore, hashAfter)
				text = dataToPrettyJson(diff)
		else:
			raise ValueError(f"unexpected {viewType=}")

		self.textbuff.set_text(text)
		self.setScrolledWinChild(self.textview)

	def setScrolledWinChild(self, new_child: gtk.Widget) -> None:
		old_child = self.leftSwin.get_child()
		if old_child != new_child:
			if old_child is not None:
				log.info("removing old child")
				self.leftSwin.remove(old_child)
			log.info("adding new child")
			self.leftSwin.add(new_child)
			new_child.show()

	def switchToRevision(self, revHash: str) -> None:
		assert isinstance(self._event.parent, EventGroup), f"{self._event.parent=}"
		assert self._event.id is not None
		newEvent = self._event.getRevision(revHash)
		self._event.parent.removeFromCache(self._event.id)
		# newEvent.id is set
		newEvent.parent = self._event.parent
		newEvent.save()
		self._event = newEvent
		self.load()
		ui.eventUpdateQueue.put("e", newEvent, self)

	def onCheckoutAfterClick(self, _button: Any) -> None:
		pathObj = self.treev.get_cursor()[0]
		if not pathObj:
			return
		path = pathObj.get_indices()
		assert len(path) == 1
		index = path[0]
		row = self.treeModel[index]
		hashAfter = row[1]
		self.switchToRevision(hashAfter)

	def onCheckoutBeforeClick(self, _button: Any) -> None:
		pathObj = self.treev.get_cursor()[0]
		if not pathObj:
			return
		path = pathObj.get_indices()
		assert len(path) == 1
		index = path[0]
		row = self.treeModel[index]
		hashBefore = row[0]
		self.switchToRevision(hashBefore)

	# def onRevertClick(self, button):
	# 	path = self.treev.get_cursor()[0]
	# 	if not path:
	# 		return
	# 	assert len(path) == 1
	# 	index = path[0]
	# 	row = self.treeModel[index]
	# 	hashBefore = row[0]
	# 	hashAfter = row[1]
	# 	# TODO

	@staticmethod
	def formatEpoch(epoch: int) -> str:
		jd, hms = getJhmsFromEpoch(epoch)
		cell = ui.cells.getCell(jd)
		return cell.format(historyTimeBinFmt, tm=hms.tuple())

	@staticmethod
	def normalizeObjectData(data: dict[str, Any]) -> dict[str, Any]:
		if "rules" in data:
			rulesDict = dict(data["rules"])
			data["rules"] = rulesDict
		return unnest(data)

	# returns normalized data ("rules.RULE_NAME" keys)
	def getObjectData(self, hashStr: str) -> dict[str, Any]:
		if not hashStr:
			return {}
		if hashStr in self.objectCache:
			return self.objectCache[hashStr]
		data = SObjBinaryModel.loadBinaryDict(hashStr, core.fs)
		data = self.normalizeObjectData(data)
		if len(self.objectCache) > 100:
			self.objectCache.popitem()
		self.objectCache[hashStr] = data
		return data

	def extractChangeDiff(
		self,
		hashBefore: str,
		hashAfter: str,
	) -> dict[str, tuple[Any, Any]]:
		"""returns: dict: param -> (valueBefore, valueAfter)."""
		dataBefore = self.getObjectData(hashBefore)
		dataAfter = self.getObjectData(hashAfter)
		diff = {}
		for key, valueBefore in dataBefore.items():
			valueAfter = dataAfter.get(key, None)
			if valueAfter == valueBefore:
				continue
			diff[key] = (valueBefore, valueAfter)
		for key, valueAfter in dataAfter.items():
			if key in diff:
				continue
			valueBefore = dataBefore.get(key, None)
			if valueAfter == valueBefore:
				continue
			diff[key] = (valueBefore, valueAfter)

		return diff

	def extractFullTable(
		self,
		hashBefore: str,
		hashAfter: str,
	) -> list[tuple[str, str, str, str]]:
		dataBefore = self.getObjectData(hashBefore)
		dataAfter = self.getObjectData(hashAfter)
		dataFull = []  # (symbol, key, valueBefore, valueAfter)
		keys = sorted(set(dataBefore).union(dataAfter))
		for key in keys:
			valueBefore = dataBefore.get(key, "")
			valueAfter = dataAfter.get(key, "")
			symbol = ""
			if valueBefore == valueAfter:
				pass
			elif key not in dataBefore:
				symbol = addSymbol
			elif key not in dataAfter:
				symbol = removeSymbol
			else:
				symbol = modifySymbol
			dataFull.append(
				(
					symbol,
					key,
					str(valueBefore),
					str(valueAfter),
				),
			)
		return dataFull

	@staticmethod
	def extractChangeSummary(diff: dict[str, Any]) -> str:
		"""diff: dict: param -> (valueBefore, valueAfter)."""
		if len(diff) < 3:
			return ", ".join(diff)

		return _("{count} parameters").format(count=_(len(diff)))

	def load(self) -> None:
		treeModel = self.treeModel
		treeModel.clear()
		hist = self._event.loadHistory()
		count = len(hist)
		for index, (epoch, hashAfter) in enumerate(hist):
			if index == count - 1:
				treeModel.append(
					[
						"",
						hashAfter,
						self.formatEpoch(epoch),
						_("(Added Event)"),
					],
				)
				continue

			hashBefore = hist[index + 1][1]
			diff = self.extractChangeDiff(hashBefore, hashAfter)
			changeSummary = self.extractChangeSummary(diff)

			treeModel.append(
				[
					hashBefore,
					hashAfter,
					self.formatEpoch(epoch),
					changeSummary,
				],
			)
