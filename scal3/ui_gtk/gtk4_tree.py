"""GTK3 TreeView/ListStore compatibility on GTK4."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from gi.repository import Gdk, Gtk

from scal3.ui_gtk.gtk4_compat import connect_widget_event, pack

if TYPE_CHECKING:
	from collections.abc import Callable, Iterable

__all__ = [
	"CellRendererCombo",
	"CellRendererPixbuf",
	"CellRendererText",
	"CellRendererToggle",
	"ComboBox",
	"ComboBoxText",
	"ListStore",
	"TreeIter",
	"TreePath",
	"TreeStore",
	"TreeView",
	"TreeViewColumn",
	"TreeViewDropPosition",
	"install_tree_patches",
]


class TreeIter(tuple[int, ...]):
	__slots__ = ()

	def __new__(cls, *indices: int) -> TreeIter:
		return super().__new__(cls, indices)


class TreePath:
	def __init__(
		self, indices: list[int] | tuple[int, ...] | str | None = None
	) -> None:
		if indices is None:
			self._indices: list[int] = []
		elif isinstance(indices, str):
			self._indices = [int(x) for x in indices.split(":") if x]
		else:
			self._indices = list(indices)

	@staticmethod
	def new_from_indices(indices: list[int]) -> TreePath:
		return TreePath(indices)

	@staticmethod
	def new_from_string(path_str: str) -> TreePath:
		return TreePath(path_str)

	def get_indices(self) -> list[int]:
		return list(self._indices)

	def __len__(self) -> int:
		return len(self._indices)

	def __getitem__(self, index: int) -> int:
		return self._indices[index]

	def __str__(self) -> str:
		return ":".join(str(i) for i in self._indices)


class _BaseStore:
	def __init__(self, *column_types: type) -> None:
		self.column_types = column_types
		self._rows: list[list[Any]] = []
		self._sort_func: Callable[..., int] | None = None
		self._sort_column = 0
		self._listeners: list[Callable[[], None]] = []

	def _notify(self) -> None:
		for listener in self._listeners:
			listener()

	def connect_changed(self, callback: Callable[[], None]) -> None:
		self._listeners.append(callback)

	def __len__(self) -> int:
		return len(self._rows)

	def __getitem__(self, index: int | TreeIter) -> list[Any]:
		if isinstance(index, TreeIter):
			return self._rows[index[0]]
		return self._rows[index]

	def __delitem__(self, index: int) -> None:
		del self._rows[index]
		self._notify()

	def clear(self) -> None:
		self._rows.clear()
		self._notify()

	def append(self, row: Iterable[Any], parent: TreeIter | None = None) -> TreeIter:
		del parent
		self._rows.append(list(row))
		self._notify()
		return TreeIter(len(self._rows) - 1)

	def insert(self, index: int, row: Iterable[Any]) -> TreeIter:
		self._rows.insert(index, list(row))
		self._notify()
		return TreeIter(index)

	def prepend(self, row: Iterable[Any]) -> TreeIter:
		return self.insert(0, row)

	def swap(self, first: TreeIter | None, second: TreeIter | None) -> None:
		if first is None or second is None:
			return
		first_index, second_index = first[0], second[0]
		self._rows[first_index], self._rows[second_index] = (
			self._rows[second_index],
			self._rows[first_index],
		)
		self._notify()

	def remove(self, row_iter: TreeIter) -> None:
		del self._rows[row_iter[0]]
		self._notify()

	def get_value(self, row_iter: TreeIter, column: int) -> Any:
		return self._rows[row_iter[0]][column]

	def set_value(self, row_iter: TreeIter, column: int, value: Any) -> None:
		self._rows[row_iter[0]][column] = value
		self._notify()

	def get_path(self, row_iter: TreeIter) -> TreePath:  # noqa: PLR6301
		return TreePath([row_iter[0]])

	def get_iter(self, path: TreePath | list[int] | str) -> TreeIter | None:
		if isinstance(path, TreePath):
			indices = path.get_indices()
		elif isinstance(path, str):
			indices = TreePath(path).get_indices()
		else:
			indices = list(path)
		if not indices or indices[0] >= len(self._rows):
			return None
		return TreeIter(indices[0])

	def set_sort_func(
		self, column: int, func: Callable[..., int], _data: Any = None
	) -> None:
		self._sort_column = column
		self._sort_func = func

	def iter(self) -> Iterable[tuple[TreePath, TreeIter]]:
		for i in range(len(self._rows)):
			yield TreePath([i]), TreeIter(i)


class ListStore(_BaseStore):
	pass


class TreeStore(_BaseStore):
	def __init__(self, *column_types: type) -> None:
		super().__init__(*column_types)
		self._children: dict[int, list[list[Any]]] = {}

	def append(self, row: Iterable[Any], parent: TreeIter | None = None) -> TreeIter:
		row_list = list(row)
		if parent is None:
			self._rows.append(row_list)
			self._notify()
			return TreeIter(len(self._rows) - 1)
		parent_idx = parent[0]
		if parent_idx not in self._children:
			self._children[parent_idx] = []
		self._children[parent_idx].append(row_list)
		child_idx = len(self._children[parent_idx]) - 1
		self._notify()
		return TreeIter(parent_idx, child_idx)

	def remove(self, row_iter: TreeIter) -> None:
		if len(row_iter) == 1:
			idx = row_iter[0]
			del self._rows[idx]
			self._children.pop(idx, None)
		else:
			del self._children[row_iter[0]][row_iter[1]]
		self._notify()

	def get_value(self, row_iter: TreeIter, column: int) -> Any:
		if len(row_iter) == 1:
			return self._rows[row_iter[0]][column]
		return self._children[row_iter[0]][row_iter[1]][column]

	def set_value(self, row_iter: TreeIter, column: int, value: Any) -> None:
		if len(row_iter) == 1:
			self._rows[row_iter[0]][column] = value
		else:
			self._children[row_iter[0]][row_iter[1]][column] = value
		self._notify()

	def get_path(self, row_iter: TreeIter) -> TreePath:  # noqa: PLR6301
		return TreePath(list(row_iter))

	def get_iter(self, path: TreePath | list[int]) -> TreeIter | None:
		if isinstance(path, TreePath):
			indices = path.get_indices()
		else:
			indices = list(path)
		if not indices:
			return None
		if len(indices) == 1:
			if indices[0] >= len(self._rows):
				return None
			return TreeIter(indices[0])
		if indices[0] not in self._children:
			return None
		if indices[1] >= len(self._children[indices[0]]):
			return None
		return TreeIter(indices[0], indices[1])

	def __getitem__(self, index: int | TreeIter) -> list[Any]:
		if isinstance(index, TreeIter):
			if len(index) == 1:
				return self._rows[index[0]]
			return self._children[index[0]][index[1]]
		return self._rows[index]

	def iter(self) -> Iterable[tuple[TreePath, TreeIter]]:
		for i in range(len(self._rows)):
			yield TreePath([i]), TreeIter(i)
			if i in self._children:
				for j in range(len(self._children[i])):
					yield TreePath([i, j]), TreeIter(i, j)


class _CellRendererBase:
	renderer_type = "text"

	def __init__(self, **props: Any) -> None:
		self.props = props
		self._callbacks: dict[
			str, list[tuple[Callable[..., Any], tuple[Any, ...]]]
		] = {}

	def set_property(self, name: str, value: Any) -> None:
		name = name.replace("-", "_")
		self.props[name] = value
		setattr(self, name, value)

	def connect(
		self,
		signal: str,
		callback: Callable[..., Any],
		*user_data: Any,
	) -> int:
		callbacks = self._callbacks.setdefault(signal, [])
		callbacks.append((callback, user_data))
		return len(callbacks)

	def emit(self, signal: str, *args: Any) -> None:
		for callback, user_data in self._callbacks.get(signal, []):
			callback(self, *args, *user_data)


class CellRendererText(_CellRendererBase):
	renderer_type = "text"


class CellRendererPixbuf(_CellRendererBase):
	renderer_type = "pixbuf"


class CellRendererToggle(_CellRendererBase):
	renderer_type = "toggle"


class CellRendererCombo(_CellRendererBase):
	renderer_type = "combo"

	def __init__(self, **props: Any) -> None:
		super().__init__(**props)
		self.model: ListStore | None = None


class TreeViewColumn:
	def __init__(
		self,
		title: str = "",
		cell_renderer: _CellRendererBase | None = None,
		**attributes: Any,
	) -> None:
		self.title = title
		self.cell_renderer = cell_renderer
		self.attributes = attributes
		self.expand = False
		self.resizable = False
		self.sort_column_id = -1
		self.min_width = 0
		self.max_width = -1
		self.visible = True
		self._treeview: TreeView | None = None

	def set_expand(self, expand: bool) -> None:
		self.expand = expand

	def set_resizable(self, resizable: bool) -> None:
		self.resizable = resizable

	def set_sort_column_id(self, sort_id: int) -> None:
		self.sort_column_id = sort_id

	def set_min_width(self, width: int) -> None:
		self.min_width = width

	def set_max_width(self, width: int) -> None:
		self.max_width = width

	def set_visible(self, visible: bool) -> None:
		self.visible = visible

	def set_property(self, name: str, value: Any) -> None:
		name = name.replace("-", "_")
		setter = getattr(self, f"set_{name}", None)
		if setter is not None:
			setter(value)
		else:
			setattr(self, name, value)

	def add_attribute(
		self,
		cell: _CellRendererBase,
		attribute: str,
		column: int,
	) -> None:
		if self.cell_renderer is None:
			self.cell_renderer = cell
		self.attributes[attribute] = column

	def get_title(self) -> str:
		return self.title


class TreeViewDropPosition:
	BEFORE = 0
	INTO_OR_BEFORE = 1
	INTO_OR_AFTER = 2
	AFTER = 3


class TreeSelection:
	def __init__(self, treeview: TreeView) -> None:
		self._treeview = treeview
		self._mode = Gtk.SelectionMode.SINGLE
		self._selected: TreeIter | None = None
		self._callbacks: list[Callable[[], None]] = []

	def connect(self, signal: str, callback: Callable[..., None]) -> None:
		if signal == "changed":
			self._callbacks.append(callback)

	def _notify_changed(self) -> None:
		for cb in self._callbacks:
			cb(self)

	def set_mode(self, mode: Gtk.SelectionMode) -> None:
		self._mode = mode

	def get_selected(self) -> tuple[Any, TreeIter | None]:
		return self._treeview.get_model(), self._selected

	def select_iter(self, row_iter: TreeIter | None) -> None:
		self._selected = row_iter
		self._notify_changed()

	def select_path(self, path: TreePath) -> None:
		model = self._treeview.get_model()
		if model is None:
			return
		row_iter = model.get_iter(path)
		if row_iter is None:
			return
		self._treeview._cursor_path = path  # noqa: SLF001
		self.select_iter(row_iter)

	def unselect_all(self) -> None:
		if self._selected is None:
			return
		self._selected = None
		self._treeview._listbox.unselect_all()  # noqa: SLF001
		self._notify_changed()

	def count_selected_rows(self) -> int:
		return int(self._selected is not None)

	def get_selected_rows(self) -> list[TreePath]:
		if self._selected is None or self._treeview.get_model() is None:
			return []
		return [self._treeview.get_model().get_path(self._selected)]


class TreeView(Gtk.ScrolledWindow):
	def __init__(self, model: _BaseStore | None = None) -> None:
		super().__init__()
		self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
		self._model = model
		self._columns: list[TreeViewColumn] = []
		self._listbox = Gtk.ListBox()
		self._listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
		self.set_child(self._listbox)
		self._selection = TreeSelection(self)
		self._cursor_path: TreePath | None = None
		self._search_column = 0
		self._headers_visible = True
		self._headers_clickable = False
		self._row_activated_callbacks: list[Callable[..., None]] = []
		self._drag_callbacks: dict[str, list[Callable[..., Any]]] = {}
		if model is not None:
			self.set_model(model)
		self._listbox.connect("row-selected", self._on_row_selected)

	def set_model(self, model: _BaseStore | None) -> None:
		self._model = model
		if model is not None:
			model.connect_changed(self._rebuild_rows)
		self._rebuild_rows()

	def get_model(self) -> _BaseStore | None:
		return self._model

	def append_column(self, column: TreeViewColumn) -> None:
		column._treeview = self  # noqa: SLF001
		self._columns.append(column)
		self._rebuild_rows()

	def get_column(self, index: int) -> TreeViewColumn:
		return self._columns[index]

	def get_columns(self) -> list[TreeViewColumn]:
		return self._columns

	def set_headers_visible(self, visible: bool) -> None:
		self._headers_visible = visible

	def set_headers_clickable(self, clickable: bool) -> None:
		self._headers_clickable = clickable

	def set_search_column(self, column: int) -> None:
		self._search_column = column

	def get_selection(self) -> TreeSelection:
		return self._selection

	def get_cursor(self) -> tuple[TreePath | None, TreeViewColumn | None]:
		if self._cursor_path is None:
			return None, None
		col = self._columns[0] if self._columns else None
		return self._cursor_path, col

	def set_cursor(self, path: TreePath | TreeIter | int) -> None:
		if isinstance(path, TreeIter):
			path = self._model.get_path(path) if self._model else None
		elif isinstance(path, int):
			path = TreePath([path])
		self._cursor_path = path

	def scroll_to_cell(
		self,
		path: TreePath,
		column: TreeViewColumn | None = None,
		use_align: bool = False,
		row_align: float = 0.0,
		col_align: float = 0.0,
	) -> None:
		del column, use_align, row_align, col_align
		indices = path.get_indices()
		row = self._listbox.get_row_at_index(indices[0]) if indices else None
		if row is not None:
			self._listbox.select_row(row)

	def row_expanded(self, path: TreePath) -> bool:  # noqa: PLR6301
		del path
		return True

	def expand_row(self, path: TreePath, _open_all: bool) -> None:  # noqa: PLR6301
		del path

	def get_path_at_pos(
		self, x: int, y: int
	) -> tuple[TreePath, TreeViewColumn, int, int] | None:
		del x, y
		if self._cursor_path is None:
			return None
		col = self._columns[0] if self._columns else None
		return self._cursor_path, col, 0, 0

	def get_cell_area(  # noqa: PLR6301
		self, path: TreePath, column: TreeViewColumn
	) -> Gdk.Rectangle:
		del path, column
		return Gdk.Rectangle(0, 0, 0, 0)

	def enable_model_drag_source(self, *_args: Any, **_kwargs: Any) -> None:
		# GtkTreeView's model DnD API was removed in GTK4. Keep setup callable;
		# calendar ordering remains available through the adjacent toolbar.
		pass

	def enable_model_drag_dest(self, *_args: Any, **_kwargs: Any) -> None:
		pass

	def translate_coordinates(
		self,
		dest_widget: Gtk.Widget,
		src_x: int,
		src_y: int,
	) -> tuple[bool, int, int] | None:
		result = self.compute_point(dest_widget, src_x, src_y)
		if result is None:
			return None
		return True, int(result[0]), int(result[1])

	def grab_focus(self) -> None:
		self._listbox.grab_focus()

	def connect(
		self,
		signal: str,
		callback: Callable[..., Any],
		*user_data: Any,
	) -> int:
		def callback_with_data(*args: Any) -> Any:
			return callback(*args, *user_data)

		if signal == "row-activated":
			self._row_activated_callbacks.append(callback_with_data)
			return len(self._row_activated_callbacks)
		if signal in {"button-press-event", "key-press-event"}:
			connect_widget_event(self, signal, callback_with_data)
			return 1
		if signal.replace("_", "-") in {"drag-data-get", "drag-data-received"}:
			callbacks = self._drag_callbacks.setdefault(signal.replace("_", "-"), [])
			callbacks.append(callback_with_data)
			return len(callbacks)
		return super().connect(signal, callback, *user_data)

	def _on_row_selected(
		self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow | None
	) -> None:
		if row is None or self._model is None:
			return
		idx = row.get_index()
		row_iter = TreeIter(idx)
		self._selection.select_iter(row_iter)
		self._cursor_path = TreePath([idx])

	def _rebuild_rows(self) -> None:
		child = self._listbox.get_first_child()
		while child is not None:
			next_child = child.get_next_sibling()
			self._listbox.remove(child)
			child = next_child
		if self._model is None:
			return
		for _path, row_iter in self._model.iter():
			row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
			for col in self._columns:
				cell = self._make_cell_widget(col, row_iter)
				if cell is not None:
					pack(row_box, cell, expand=col.expand, fill=True)
			list_row = Gtk.ListBoxRow()
			list_row.set_child(row_box)
			self._listbox.append(list_row)

	def _make_cell_widget(
		self, col: TreeViewColumn, row_iter: TreeIter
	) -> Gtk.Widget | None:
		if self._model is None or col.cell_renderer is None:
			return None
		renderer = col.cell_renderer
		text_col = col.attributes.get("text", 0)
		active_col = col.attributes.get("active", 0)
		pixbuf_col = col.attributes.get("pixbuf", 0)
		if renderer.renderer_type == "toggle":
			check = Gtk.CheckButton()
			check.set_active(bool(self._model.get_value(row_iter, active_col)))
			path = ":".join(str(index) for index in row_iter)

			def on_toggled(_check: Gtk.CheckButton) -> None:
				renderer.emit("toggled", path)

			check.connect("toggled", on_toggled)
			return check
		if renderer.renderer_type == "pixbuf":
			pixbuf = self._model.get_value(row_iter, pixbuf_col)
			if pixbuf is not None:
				return Gtk.Image.new_from_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
			return Gtk.Image()
		text = self._model.get_value(row_iter, text_col)
		label = Gtk.Label(label=str(text) if text is not None else "")
		label.set_xalign(0)
		return label


class ComboBox(Gtk.DropDown):
	def __init__(self) -> None:
		super().__init__()
		self._list_store: ListStore | None = None
		self._text_renderer: CellRendererText | None = None
		self._string_list = Gtk.StringList.new([])
		Gtk.DropDown.set_model(self, self._string_list)

	def set_model(self, model: ListStore) -> None:
		self._list_store = model
		model.connect_changed(self._sync_native_model)
		self._sync_native_model()

	def _sync_native_model(self) -> None:
		model = self._list_store
		if model is None:
			return
		active = self.get_active()
		strings: list[str] = []
		for i in range(len(model)):
			row = model[i]
			text_col = 1 if len(row) > 1 else 0
			val = row[text_col]
			strings.append("" if val is None else str(val))
		self._string_list.splice(0, self._string_list.get_n_items(), strings)
		if 0 <= active < len(model):
			self.set_active(active)

	def set_active(self, index: int) -> None:
		selected = Gtk.INVALID_LIST_POSITION if index < 0 else index
		self.set_selected(selected)

	def get_active(self) -> int:
		selected = self.get_selected()
		if selected == Gtk.INVALID_LIST_POSITION:
			return -1
		return selected

	def get_model(self) -> ListStore | None:
		return self._list_store

	def pack_start(self, cell: _CellRendererBase, expand: bool = False) -> None:
		del expand
		if isinstance(cell, CellRendererText):
			self._text_renderer = cell

	def add_attribute(  # noqa: PLR6301
		self, cell: _CellRendererBase, attribute: str, column: int
	) -> None:
		del cell, attribute, column

	def set_row_separator_func(  # noqa: PLR6301
		self, func: Callable[..., bool], data: Any
	) -> None:
		del func, data

	def connect(
		self,
		signal: str,
		callback: Callable[..., Any],
		*user_data: Any,
	) -> int:
		if signal == "changed":

			def on_selected(_combo: ComboBox, _pspec: object) -> Any:
				return callback(self, *user_data)

			return super().connect("notify::selected", on_selected)
		return super().connect(signal, callback, *user_data)


class ComboBoxText(Gtk.ComboBoxText):
	pass


def install_tree_patches() -> None:
	Gtk.ListStore = ListStore  # type: ignore[attr-defined]
	Gtk.TreeStore = TreeStore  # type: ignore[attr-defined]
	Gtk.TreeView = TreeView  # type: ignore[attr-defined]
	Gtk.TreeViewColumn = TreeViewColumn  # type: ignore[attr-defined]
	Gtk.TreeViewDropPosition = TreeViewDropPosition  # type: ignore[attr-defined]
	Gtk.TreePath = TreePath  # type: ignore[attr-defined]
	Gtk.TreeIter = TreeIter  # type: ignore[attr-defined]
	Gtk.CellRendererText = CellRendererText  # type: ignore[attr-defined]
	Gtk.CellRendererPixbuf = CellRendererPixbuf  # type: ignore[attr-defined]
	Gtk.CellRendererToggle = CellRendererToggle  # type: ignore[attr-defined]
	Gtk.CellRendererCombo = CellRendererCombo  # type: ignore[attr-defined]
	Gtk.ComboBox = ComboBox  # type: ignore[attr-defined]
