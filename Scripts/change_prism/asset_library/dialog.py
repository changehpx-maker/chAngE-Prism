from __future__ import unicode_literals

from collections import deque
import datetime
import os
import subprocess
import sys
import threading

from qtpy.QtCore import (
    QAbstractListModel,
    QEvent,
    QModelIndex,
    QRect,
    QSize,
    Qt,
    QThread,
    QTimer,
    QUrl,
    Signal,
)
from qtpy.QtGui import (
    QDesktopServices,
    QIcon,
    QImage,
    QImageReader,
    QPixmap,
)
from qtpy.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from change_prism.asset_library import service
from change_prism.config import (
    get_asset_library_thumbnail_size,
    get_asset_library_sources,
    save_asset_library_thumbnail_size,
    save_asset_library_sources,
)
from change_prism.houdini_asset_bridge import HoudiniAssetBridge


SOURCE_ID_ROLE = Qt.UserRole
PATH_ROLE = Qt.UserRole + 1
SOURCE_ROOT_ROLE = Qt.UserRole + 2
ASSET_ROLE = Qt.UserRole
THUMBNAIL_PIXMAP_ROLE = Qt.UserRole + 10
THUMBNAIL_SIZE = QSize(256, 144)
THUMBNAIL_SIZE_PRESETS = (
    ("Small", "small", QSize(160, 80)),
    ("Medium", "medium", QSize(256, 128)),
    ("Large", "large", QSize(384, 192)),
)
THUMBNAIL_SIZE_BY_KEY = {
    key: QSize(size)
    for _label, key, size in THUMBNAIL_SIZE_PRESETS
}
DETAIL_PREVIEW_SIZE = QSize(384, 192)
MAX_THUMBNAIL_WORKERS = 4
MAX_HDR_THUMBNAIL_WORKERS = 2
HDR_EXTENSIONS = (".exr", ".hdr")
_ACTIVE_THREADS = set()


def _track_thread(thread):
    _ACTIVE_THREADS.add(thread)
    thread.finished.connect(
        lambda current=thread: _release_thread(current)
    )


def _release_thread(thread):
    _ACTIVE_THREADS.discard(thread)
    thread.deleteLater()


class _ScanThread(QThread):
    resultReady = Signal(object, int)
    failed = Signal(str, int)

    def __init__(self, sources, generation):
        super(_ScanThread, self).__init__(None)
        self.sources = sources
        self.generation = generation
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self):
        try:
            result = service.scan_sources(
                self.sources,
                cancel_event=self.cancel_event,
            )
        except Exception as exc:
            self.failed.emit(str(exc), self.generation)
            return
        self.resultReady.emit(result, self.generation)


class _ThumbnailThread(QThread):
    resultReady = Signal(object)

    def __init__(
        self,
        core,
        path,
        record_key,
        generation,
        target_size,
        manual=False,
    ):
        super(_ThumbnailThread, self).__init__(None)
        self.core = core
        self.path = path
        self.record_key = record_key
        self.generation = generation
        self.target_size = target_size
        self.manual = manual

    def run(self):
        result = {
            "path": self.path,
            "record_key": self.record_key,
            "generation": self.generation,
            "image": None,
            "width": None,
            "height": None,
            "error": "",
            "cache_error": "",
            "manual": self.manual,
        }
        try:
            cache_path = service.thumbnail_path(self.path)
            if service.thumbnail_is_fresh(self.path, cache_path):
                image = QImage(cache_path)
                if not image.isNull():
                    result["image"] = image
                    width, height = self._read_resolution()
                    result["width"] = width
                    result["height"] = height
                    self.resultReady.emit(result)
                    return

            image, width, height = self._decode_image()
            if image is None or image.isNull():
                raise RuntimeError("Unable to decode image preview.")
            result["image"] = image
            result["width"] = width
            result["height"] = height

            try:
                cache_directory = os.path.dirname(cache_path)
                if not os.path.isdir(cache_directory):
                    try:
                        os.makedirs(cache_directory)
                    except OSError:
                        if not os.path.isdir(cache_directory):
                            raise
                if not image.save(cache_path, "JPG", 85):
                    result["cache_error"] = (
                        "Unable to save thumbnail: %s" % cache_path
                    )
            except OSError as exc:
                result["cache_error"] = str(exc)
        except Exception as exc:
            result["error"] = str(exc)
        self.resultReady.emit(result)

    def _decode_image(self):
        extension = os.path.splitext(self.path)[1].lower()
        if extension in (".exr", ".hdr"):
            media = getattr(self.core, "media", None)
            reader = getattr(media, "getQImageFromExrPath", None)
            if reader is None:
                raise RuntimeError(
                    "Prism media preview is unavailable for %s."
                    % extension
                )
            image = reader(
                self.path,
                self.target_size.width(),
                self.target_size.height(),
                allowThumb=False,
            )
            width, height = self._read_resolution()
            return image, width, height

        reader = QImageReader(self.path)
        reader.setAutoTransform(True)
        original_size = reader.size()
        if original_size.isValid():
            reader.setScaledSize(
                original_size.scaled(
                    self.target_size,
                    Qt.KeepAspectRatio,
                )
            )
        image = reader.read()
        width = original_size.width() if original_size.isValid() else None
        height = (
            original_size.height() if original_size.isValid() else None
        )
        if image.isNull():
            image = QImage(self.path)
        if (
            not image.isNull()
            and (
                image.width() > self.target_size.width()
                or image.height() > self.target_size.height()
            )
        ):
            image = image.scaled(
                self.target_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        return image, width, height

    def _read_resolution(self):
        media = getattr(self.core, "media", None)
        reader = getattr(media, "getMediaResolution", None)
        if reader is not None:
            try:
                result = reader(self.path) or {}
                return result.get("width"), result.get("height")
            except Exception:
                pass
        image_reader = QImageReader(self.path)
        size = image_reader.size()
        if size.isValid():
            return size.width(), size.height()
        return None, None


class AssetListModel(QAbstractListModel):
    def __init__(self, placeholder_icon, parent=None):
        super(AssetListModel, self).__init__(parent)
        self.placeholder_icon = placeholder_icon
        self.icon_size = QSize(256, 144)
        self.device_pixel_ratio = 1.0
        self.records = []
        self.icons = {}
        self.pixmaps = {}
        self.thumbnail_images = {}
        self._rows_by_key = {}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.records)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.records):
            return None
        record = self.records[index.row()]
        if role == Qt.DisplayRole:
            text = record.get("filename", "")
            count = int(record.get("location_count", 1))
            if count > 1:
                text += "\n%d locations" % count
            return text
        if role == Qt.DecorationRole:
            return self.icons.get(
                record.get("record_key"),
                self.placeholder_icon,
            )
        if role == THUMBNAIL_PIXMAP_ROLE:
            return self.pixmaps.get(record.get("record_key"))
        if role == Qt.ToolTipRole:
            count = int(record.get("location_count", 1))
            if count > 1:
                return "%s\n%d locations" % (
                    record.get("filename", ""),
                    count,
                )
            return record.get("path", "")
        if role == ASSET_ROLE:
            return record
        return None

    def set_records(self, records):
        self.beginResetModel()
        self.records = list(records)
        self.icons = {}
        self.pixmaps = {}
        self.thumbnail_images = {}
        self._rows_by_key = {
            record.get("record_key"): row
            for row, record in enumerate(self.records)
        }
        self.endResetModel()

    def record(self, index):
        if not index.isValid() or not 0 <= index.row() < len(self.records):
            return None
        return self.records[index.row()]

    def set_icon_metrics(self, icon_size, device_pixel_ratio):
        icon_size = QSize(icon_size)
        try:
            ratio = float(device_pixel_ratio)
        except Exception:
            ratio = 1.0
        ratio = max(1.0, ratio)
        changed = (
            self.icon_size != icon_size
            or abs(self.device_pixel_ratio - ratio) > 0.001
        )
        self.icon_size = icon_size
        self.device_pixel_ratio = ratio
        if changed:
            self._rebuild_thumbnail_pixmaps()

    def set_thumbnail(self, record_key, image):
        self.thumbnail_images[record_key] = image
        self._set_thumbnail_pixmap(record_key, image)

    def _rebuild_thumbnail_pixmaps(self):
        for record_key, image in list(self.thumbnail_images.items()):
            self._set_thumbnail_pixmap(record_key, image)

    def _set_thumbnail_pixmap(self, record_key, image):
        physical_size = QSize(
            max(
                1,
                int(
                    round(
                        self.icon_size.width()
                        * self.device_pixel_ratio
                    )
                ),
            ),
            max(
                1,
                int(
                    round(
                        self.icon_size.height()
                        * self.device_pixel_ratio
                    )
                ),
            ),
        )
        display_image = image.scaled(
            physical_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        pixmap = QPixmap.fromImage(display_image)
        if pixmap.isNull():
            return
        set_device_pixel_ratio = getattr(
            pixmap,
            "setDevicePixelRatio",
            None,
        )
        if callable(set_device_pixel_ratio):
            set_device_pixel_ratio(self.device_pixel_ratio)
        self.icons[record_key] = QIcon(pixmap)
        self.pixmaps[record_key] = pixmap
        row = self._rows_by_key.get(record_key)
        if row is None:
            return
        index = self.index(row, 0)
        self.dataChanged.emit(
            index,
            index,
            [Qt.DecorationRole, THUMBNAIL_PIXMAP_ROLE],
        )


class HoudiniAssetItemDelegate(QStyledItemDelegate):
    """Draw full-size thumbnails without Houdini QIcon rescaling."""

    def __init__(self, icon_size, parent=None):
        super(HoudiniAssetItemDelegate, self).__init__(parent)
        self.icon_size = QSize(icon_size)

    def set_icon_size(self, icon_size):
        self.icon_size = QSize(icon_size)

    def paint(self, painter, option, index):
        item_option = QStyleOptionViewItem(option)
        self.initStyleOption(item_option, index)
        text = item_option.text
        item_option.icon = QIcon()
        item_option.text = ""
        widget = item_option.widget
        style = widget.style() if widget is not None else QApplication.style()
        style.drawControl(
            QStyle.CE_ItemViewItem,
            item_option,
            painter,
            widget,
        )

        pixmap = index.data(THUMBNAIL_PIXMAP_ROLE)
        if pixmap is not None and not pixmap.isNull():
            target = self._thumbnail_rect(option.rect, pixmap)
            painter.drawPixmap(target, pixmap)

        text_rect = QRect(
            option.rect.x() + 4,
            option.rect.y() + self.icon_size.height() + 8,
            max(1, option.rect.width() - 8),
            max(1, option.rect.height() - self.icon_size.height() - 10),
        )
        if option.state & QStyle.State_Selected:
            text_color = item_option.palette.highlightedText().color()
        else:
            text_color = item_option.palette.text().color()
        painter.save()
        painter.setFont(item_option.font)
        painter.setPen(text_color)
        painter.drawText(
            text_rect,
            Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap,
            text,
        )
        painter.restore()

    def _thumbnail_rect(self, item_rect, pixmap):
        pixel_ratio_reader = getattr(
            pixmap,
            "devicePixelRatio",
            None,
        )
        try:
            pixel_ratio = (
                float(pixel_ratio_reader())
                if callable(pixel_ratio_reader)
                else 1.0
            )
        except Exception:
            pixel_ratio = 1.0
        pixel_ratio = max(1.0, pixel_ratio)
        source_width = max(1.0, pixmap.width() / pixel_ratio)
        source_height = max(1.0, pixmap.height() / pixel_ratio)
        scale = min(
            self.icon_size.width() / source_width,
            self.icon_size.height() / source_height,
        )
        width = max(1, int(round(source_width * scale)))
        height = max(1, int(round(source_height * scale)))
        left = item_rect.x() + (item_rect.width() - width) // 2
        top = (
            item_rect.y()
            + 4
            + (self.icon_size.height() - height) // 2
        )
        return QRect(left, top, width, height)


class LazyAssetLibraryWidget(QWidget):
    """Create the full library UI only after the tab is opened."""

    def __init__(self, core, parent=None):
        super(LazyAssetLibraryWidget, self).__init__(parent)
        self.core = core
        self.refreshStatus = "invalid"
        self._browser = None
        self.setProperty("tabType", "AssetLibrary")
        self.setProperty("changePrismAssetLibrary", "change_prism")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._placeholder = QLabel(
            "Open Asset Library to scan configured sources.",
            self,
        )
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setEnabled(False)
        self._layout.addWidget(self._placeholder)

    def _ensure_browser(self):
        if self._browser is None:
            browser = AssetLibraryWidget(self.core, parent=self)
            self._layout.replaceWidget(self._placeholder, browser)
            self._placeholder.deleteLater()
            self._browser = browser
        return self._browser

    def entered(self, prevTab=None, navData=None):
        del prevTab, navData
        browser = self._ensure_browser()
        browser.entered()
        self.refreshStatus = "valid"

    def getSelectedContext(self):
        return None

    def refreshUI(self):
        if self._browser is None:
            self.refreshStatus = "invalid"
            return
        self._browser.refresh_sources()
        self.refreshStatus = "valid"

    def refresh_sources(self):
        if self._browser is None:
            self.refreshStatus = "invalid"
            return
        self._browser.refresh_sources()


class AssetLibraryWidget(QWidget):
    def __init__(self, core, parent=None):
        super(AssetLibraryWidget, self).__init__(parent)
        self.core = core
        self.refreshStatus = "invalid"
        self.sources = get_asset_library_sources(core)
        self.scan_result = self._empty_scan_result()
        self._scan_thread = None
        self._scan_generation = 0
        self._queued_refresh = False
        self._entered = False
        self._closing = False
        self._updating_tree = False
        self._view_generation = 0
        self._thumbnail_queue = deque()
        self._thumbnail_requested = set()
        self._thumbnail_threads = set()
        self._thumbnail_failures = 0
        self._thumbnail_batch = None
        self._resolution_cache = {}
        self._selected_record = None
        self._houdini_asset_bridge = None
        app_plugin = getattr(self.core, "appPlugin", None)
        self._is_houdini = (
            str(getattr(app_plugin, "pluginName", "")).lower()
            == "houdini"
        )
        self._asset_library_host_key = (
            "houdini" if self._is_houdini else "standalone"
        )
        self._thumbnail_size_key = get_asset_library_thumbnail_size(
            self.core,
            self._asset_library_host_key,
        )
        self._thumbnail_display_size = QSize(
            THUMBNAIL_SIZE_BY_KEY.get(
                self._thumbnail_size_key,
                THUMBNAIL_SIZE_BY_KEY["medium"],
            )
        )
        self._build_ui()
        self._populate_tree()

    @staticmethod
    def _empty_scan_result():
        return {
            "sources": [],
            "directories": [],
            "assets": [],
            "failures": [],
            "cancelled": False,
        }

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Horizontal, self)
        layout.addWidget(splitter)

        left = QWidget(splitter)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(10, 10, 6, 10)
        source_heading = QLabel("Sources", left)
        source_font = source_heading.font()
        source_font.setBold(True)
        source_heading.setFont(source_font)
        left_layout.addWidget(source_heading)

        source_buttons = QHBoxLayout()
        self.add_source_button = QPushButton("Add Source", left)
        self.add_source_button.clicked.connect(self.add_source)
        source_buttons.addWidget(self.add_source_button)
        self.remove_source_button = QPushButton("Remove", left)
        self.remove_source_button.clicked.connect(self.remove_source)
        source_buttons.addWidget(self.remove_source_button)
        left_layout.addLayout(source_buttons)

        self.source_tree = QTreeWidget(left)
        self.source_tree.setHeaderLabels(["Source / Folder", "Status"])
        self.source_tree.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )
        self.source_tree.itemChanged.connect(
            self._on_source_item_changed
        )
        self.source_tree.currentItemChanged.connect(
            self._on_tree_selection_changed
        )
        self.source_tree.itemSelectionChanged.connect(
            self._update_generate_button
        )
        left_layout.addWidget(self.source_tree, 1)
        splitter.addWidget(left)

        right = QWidget(splitter)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 10, 10, 10)
        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit(right)
        self.search_edit.setPlaceholderText(
            "Search all enabled sources..."
        )
        self.search_edit.setClearButtonEnabled(True)
        toolbar.addWidget(self.search_edit, 1)

        self.sort_combo = QComboBox(right)
        self.sort_combo.addItem("Name", "name")
        self.sort_combo.addItem("Modified", "modified")
        self.sort_combo.addItem("File Size", "size")
        self.sort_combo.currentIndexChanged.connect(
            self._refresh_asset_view
        )
        toolbar.addWidget(self.sort_combo)

        self.order_button = QPushButton("Ascending", right)
        self.order_button.setCheckable(True)
        self.order_button.toggled.connect(self._on_order_changed)
        toolbar.addWidget(self.order_button)

        self.thumbnail_size_label = QLabel("Size:", right)
        toolbar.addWidget(self.thumbnail_size_label)
        self.thumbnail_size_combo = QComboBox(right)
        for label, key, _size in THUMBNAIL_SIZE_PRESETS:
            self.thumbnail_size_combo.addItem(label, key)
        size_index = self.thumbnail_size_combo.findData(
            self._thumbnail_size_key
        )
        self.thumbnail_size_combo.setCurrentIndex(max(0, size_index))
        self.thumbnail_size_combo.setToolTip(
            "Change the thumbnail display size. Existing _thumbs caches "
            "are reused and are not regenerated."
        )
        self.thumbnail_size_combo.currentIndexChanged.connect(
            self._on_thumbnail_size_changed
        )
        toolbar.addWidget(self.thumbnail_size_combo)

        self.generate_thumbnails_button = QPushButton(
            "Generate Thumbnails",
            right,
        )
        self.generate_thumbnails_button.setToolTip(
            "Generate missing or outdated thumbnails for images directly "
            "inside all selected folders. Use Ctrl or Shift to select "
            "multiple folders."
        )
        self.generate_thumbnails_button.clicked.connect(
            self.generate_selected_thumbnails
        )
        self.generate_thumbnails_button.setEnabled(False)
        toolbar.addWidget(self.generate_thumbnails_button)

        self.refresh_button = QPushButton("Refresh", right)
        self.refresh_button.setIcon(
            self.style().standardIcon(QStyle.SP_BrowserReload)
        )
        self.refresh_button.clicked.connect(self.refresh_sources)
        toolbar.addWidget(self.refresh_button)
        right_layout.addLayout(toolbar)

        self.status_label = QLabel("Add a source to begin.", right)
        self.status_label.setEnabled(False)
        self.status_label.setWordWrap(True)
        right_layout.addWidget(self.status_label)

        placeholder = self.style().standardIcon(QStyle.SP_FileIcon)
        self.asset_model = AssetListModel(placeholder, self)
        self.asset_view = QListView(right)
        self.asset_view.setModel(self.asset_model)
        self.asset_view.setViewMode(QListView.IconMode)
        self.asset_view.setResizeMode(QListView.Adjust)
        self.asset_view.setMovement(QListView.Static)
        self.asset_view.setSelectionMode(
            QAbstractItemView.SingleSelection
        )
        if self._is_houdini:
            self.asset_view.setItemDelegate(
                HoudiniAssetItemDelegate(
                    self._thumbnail_display_size,
                    self.asset_view,
                )
            )
        self._apply_thumbnail_size()
        self.asset_view.setVerticalScrollMode(
            QAbstractItemView.ScrollPerPixel
        )
        self.asset_view.setUniformItemSizes(True)
        self.asset_view.setWordWrap(True)
        self.asset_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.asset_view.customContextMenuRequested.connect(
            self._show_asset_context_menu
        )
        self.asset_view.doubleClicked.connect(
            lambda _index: self.open_selected()
        )
        self.asset_view.selectionModel().currentChanged.connect(
            self._on_asset_selection_changed
        )
        self.asset_view.verticalScrollBar().valueChanged.connect(
            self._schedule_visible_thumbnails
        )
        self.asset_view.viewport().installEventFilter(self)
        right_layout.addWidget(self.asset_view, 1)

        details = QGroupBox("Details", right)
        detail_outer_layout = QHBoxLayout(details)
        self.detail_preview = QLabel(details)
        self.detail_preview.setFixedSize(DETAIL_PREVIEW_SIZE)
        self.detail_preview.setAlignment(Qt.AlignCenter)
        self.detail_preview.setFrameShape(QFrame.StyledPanel)
        self.detail_preview.setFrameShadow(QFrame.Sunken)
        detail_outer_layout.addWidget(
            self.detail_preview,
            0,
            Qt.AlignTop,
        )
        detail_layout = QFormLayout()
        detail_outer_layout.addLayout(detail_layout, 1)
        self.detail_name = QLabel("-", details)
        detail_layout.addRow("Name:", self.detail_name)
        self.detail_resolution = QLabel("-", details)
        detail_layout.addRow("Resolution:", self.detail_resolution)
        self.detail_size = QLabel("-", details)
        detail_layout.addRow("File Size:", self.detail_size)
        self.detail_modified = QLabel("-", details)
        detail_layout.addRow("Modified:", self.detail_modified)
        self.detail_categories = QLabel("-", details)
        self.detail_categories.setWordWrap(True)
        detail_layout.addRow("Locations:", self.detail_categories)
        self.location_combo = QComboBox(details)
        self.location_combo.currentIndexChanged.connect(
            self._on_location_changed
        )
        detail_layout.addRow("Active Location:", self.location_combo)
        self.detail_path = QLineEdit(details)
        self.detail_path.setReadOnly(True)
        detail_layout.addRow("Path:", self.detail_path)

        action_row = QWidget(details)
        action_layout = QHBoxLayout(action_row)
        action_layout.setContentsMargins(0, 0, 0, 0)
        self.open_button = QPushButton("Open", action_row)
        self.open_button.clicked.connect(self.open_selected)
        action_layout.addWidget(self.open_button)
        self.reveal_button = QPushButton("Reveal in Explorer", action_row)
        self.reveal_button.clicked.connect(self.reveal_selected)
        action_layout.addWidget(self.reveal_button)
        self.copy_button = QPushButton("Copy Path", action_row)
        self.copy_button.clicked.connect(self.copy_selected_path)
        action_layout.addWidget(self.copy_button)
        action_layout.addStretch()
        detail_layout.addRow("", action_row)
        right_layout.addWidget(details)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 900])

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(150)
        self._search_timer.timeout.connect(self._refresh_asset_view)
        self.search_edit.textChanged.connect(
            lambda _text: self._search_timer.start()
        )
        self._thumbnail_timer = QTimer(self)
        self._thumbnail_timer.setSingleShot(True)
        self._thumbnail_timer.setInterval(25)
        self._thumbnail_timer.timeout.connect(
            self._queue_visible_thumbnails
        )
        self._clear_details()

    def entered(self):
        if not self._entered:
            self._entered = True
            self.refresh_sources()
        else:
            self._schedule_visible_thumbnails()
        self.refreshStatus = "valid"

    def refresh_sources(self):
        if self._closing:
            return
        self.sources = get_asset_library_sources(self.core)
        if self._scan_thread is not None and self._scan_thread.isRunning():
            self._queued_refresh = True
            self._scan_thread.cancel()
            self.status_label.setText("Stopping the previous scan...")
            return
        self._start_scan()

    def _start_scan(self):
        self._queued_refresh = False
        self._scan_generation += 1
        generation = self._scan_generation
        if not self.sources:
            self.scan_result = self._empty_scan_result()
            self._populate_tree()
            self._refresh_asset_view()
            self.status_label.setText(
                "No sources configured. Click Add Source to begin."
            )
            return

        enabled_count = sum(
            1 for item in self.sources if item.get("enabled", True)
        )
        self.status_label.setText(
            "Scanning %d enabled source(s)..." % enabled_count
        )
        thread = _ScanThread(list(self.sources), generation)
        _track_thread(thread)
        thread.resultReady.connect(self._on_scan_result)
        thread.failed.connect(self._on_scan_failed)
        thread.finished.connect(
            lambda current=thread: self._on_scan_finished(current)
        )
        self._scan_thread = thread
        thread.start()

    def _on_scan_result(self, result, generation):
        if self._closing or generation != self._scan_generation:
            return
        if result.get("cancelled"):
            return
        self.scan_result = result
        self._thumbnail_failures = 0
        self.status_label.setToolTip("")
        self._populate_tree()
        self._refresh_asset_view()
        failures = result.get("failures", [])
        if failures:
            self.status_label.setToolTip(
                "\n".join(
                    "%s: %s"
                    % (item.get("path", ""), item.get("error", ""))
                    for item in failures
                )
            )
        self.refreshStatus = "valid"

    def _on_scan_failed(self, message, generation):
        if self._closing or generation != self._scan_generation:
            return
        self.status_label.setText("Asset Library scan failed: %s" % message)

    def _on_scan_finished(self, thread):
        if self._scan_thread is thread:
            self._scan_thread = None
        if self._closing:
            return
        if self._queued_refresh:
            self._start_scan()

    def _populate_tree(self):
        selected = self._selected_tree_key()
        self._updating_tree = True
        self.source_tree.clear()
        source_results = {
            item["id"]: item
            for item in self.scan_result.get("sources", [])
        }
        directories = self.scan_result.get("directories", [])
        directory_map = {}

        for spec in self.sources:
            root = spec["path"]
            source_id = service.source_key(root)
            source_result = source_results.get(source_id)
            root_item = QTreeWidgetItem(self.source_tree)
            root_item.setText(0, service.source_name(root))
            root_item.setToolTip(0, root)
            root_item.setData(0, SOURCE_ID_ROLE, source_id)
            root_item.setData(0, PATH_ROLE, root)
            root_item.setData(0, SOURCE_ROOT_ROLE, True)
            root_item.setFlags(
                root_item.flags() | Qt.ItemIsUserCheckable
            )
            root_item.setCheckState(
                0,
                Qt.Checked if spec.get("enabled", True) else Qt.Unchecked,
            )
            root_item.setIcon(
                0,
                self.style().standardIcon(QStyle.SP_DirIcon),
            )
            if not spec.get("enabled", True):
                status = "Disabled"
            elif source_result is None:
                status = (
                    "Not scanned"
                    if os.path.isdir(root)
                    else "Offline"
                )
            elif not source_result.get("available"):
                status = "Offline"
            else:
                status = "%d files" % source_result.get(
                    "file_count", 0
                )
            root_item.setText(1, status)
            directory_map[
                (source_id, os.path.normcase(os.path.normpath(root)))
            ] = root_item

        sorted_directories = sorted(
            directories,
            key=lambda item: (
                item.get("source_id", ""),
                item.get("relative_path", "").count(os.sep),
                item.get("relative_path", "").casefold(),
            ),
        )
        asset_counts = {}
        for asset in self.scan_result.get("assets", []):
            count_key = (
                asset.get("source_id"),
                os.path.normcase(asset.get("directory", "")),
            )
            asset_counts[count_key] = asset_counts.get(count_key, 0) + 1

        for directory in sorted_directories:
            source_id = directory["source_id"]
            path = directory["path"]
            key = (source_id, os.path.normcase(os.path.normpath(path)))
            if key in directory_map:
                continue
            parent_path = os.path.dirname(path)
            parent = directory_map.get(
                (
                    source_id,
                    os.path.normcase(os.path.normpath(parent_path)),
                )
            )
            if parent is None:
                continue
            item = QTreeWidgetItem(parent)
            item.setText(0, directory["name"])
            item.setToolTip(0, path)
            item.setData(0, SOURCE_ID_ROLE, source_id)
            item.setData(0, PATH_ROLE, path)
            item.setData(0, SOURCE_ROOT_ROLE, False)
            item.setIcon(
                0,
                self.style().standardIcon(QStyle.SP_DirIcon),
            )
            direct_count = asset_counts.get(
                (source_id, os.path.normcase(os.path.normpath(path))),
                0,
            )
            if direct_count:
                item.setText(1, str(direct_count))
            directory_map[key] = item

        target = directory_map.get(selected)
        if target is None and self.source_tree.topLevelItemCount():
            target = self.source_tree.topLevelItem(0)
        if target is not None:
            self.source_tree.setCurrentItem(target)
        self.source_tree.expandToDepth(0)
        self.source_tree.resizeColumnToContents(0)
        self._updating_tree = False
        self._update_generate_button()

    def _selected_tree_key(self):
        item = self.source_tree.currentItem()
        if item is None:
            return None
        return (
            item.data(0, SOURCE_ID_ROLE),
            os.path.normcase(
                os.path.normpath(item.data(0, PATH_ROLE) or "")
            ),
        )

    def _on_source_item_changed(self, item, column):
        if (
            self._updating_tree
            or column != 0
            or not item.data(0, SOURCE_ROOT_ROLE)
        ):
            return
        source_id = item.data(0, SOURCE_ID_ROLE)
        enabled = item.checkState(0) == Qt.Checked
        updated = []
        for spec in self.sources:
            current = dict(spec)
            if service.source_key(current["path"]) == source_id:
                current["enabled"] = enabled
            updated.append(current)
        save_asset_library_sources(self.core, updated)
        self.sources = updated
        self.refresh_sources()

    def _on_tree_selection_changed(self, _current, _previous):
        self._update_generate_button()
        if not self._updating_tree and not self.search_edit.text().strip():
            self._refresh_asset_view()

    def add_source(self):
        start = self.sources[-1]["path"] if self.sources else ""
        path = QFileDialog.getExistingDirectory(
            self,
            "Add Asset Library Source",
            start,
        )
        if not path:
            return
        path = service.normalize_source_path(path)
        key = service.source_key(path)
        if any(service.source_key(item["path"]) == key for item in self.sources):
            self._show_warning("This source is already registered.")
            return
        sources = list(self.sources)
        sources.append({"path": path, "enabled": True})
        save_asset_library_sources(self.core, sources)
        self.sources = sources
        self.refresh_sources()

    def remove_source(self):
        item = self.source_tree.currentItem()
        if item is None:
            return
        source_id = item.data(0, SOURCE_ID_ROLE)
        spec = next(
            (
                source
                for source in self.sources
                if service.source_key(source["path"]) == source_id
            ),
            None,
        )
        if spec is None:
            return
        answer = QMessageBox.question(
            self,
            "Remove Asset Source",
            (
                "Remove this source from Asset Library?\n\n%s\n\n"
                "Source files and existing _thumbs folders will not be deleted."
            )
            % spec["path"],
            QMessageBox.Yes | QMessageBox.Cancel,
            QMessageBox.Cancel,
        )
        if answer != QMessageBox.Yes:
            return
        sources = [
            source
            for source in self.sources
            if service.source_key(source["path"]) != source_id
        ]
        save_asset_library_sources(self.core, sources)
        self.sources = sources
        self.refresh_sources()

    def _on_order_changed(self, descending):
        self.order_button.setText(
            "Descending" if descending else "Ascending"
        )
        self._refresh_asset_view()

    def _on_thumbnail_size_changed(self, *_args):
        size_key = self.thumbnail_size_combo.currentData() or "medium"
        if size_key not in THUMBNAIL_SIZE_BY_KEY:
            size_key = "medium"
        self._thumbnail_size_key = size_key
        self._thumbnail_display_size = QSize(
            THUMBNAIL_SIZE_BY_KEY[size_key]
        )
        self._apply_thumbnail_size()
        save_asset_library_thumbnail_size(
            self.core,
            self._asset_library_host_key,
            size_key,
        )

    def _apply_thumbnail_size(self):
        size = self._thumbnail_display_size
        self.asset_view.setIconSize(size)
        if self._is_houdini:
            grid_size = QSize(
                size.width() + 8,
                size.height() + 62,
            )
            spacing = 2
            delegate = self.asset_view.itemDelegate()
            if isinstance(delegate, HoudiniAssetItemDelegate):
                delegate.set_icon_size(size)
        else:
            grid_size = QSize(
                size.width() + 20,
                size.height() + 66,
            )
            spacing = 6
        self.asset_view.setGridSize(grid_size)
        self.asset_view.setSpacing(spacing)
        self._update_thumbnail_icon_metrics()
        self.asset_view.doItemsLayout()
        if hasattr(self, "_thumbnail_timer"):
            self._schedule_visible_thumbnails()

    def _selected_directory_assets(self):
        directories = [
            (
                item.data(0, SOURCE_ID_ROLE),
                item.data(0, PATH_ROLE),
            )
            for item in self.source_tree.selectedItems()
        ]
        return service.assets_in_directories(
            self.scan_result.get("assets", []),
            directories,
        )

    def _update_generate_button(self):
        enabled = (
            not self._closing
            and self._thumbnail_batch is None
            and bool(self._selected_directory_assets())
        )
        self.generate_thumbnails_button.setEnabled(enabled)

    def generate_selected_thumbnails(self):
        if self._closing or self._thumbnail_batch is not None:
            return
        assets = self._selected_directory_assets()
        if not assets:
            self.status_label.setText(
                "No supported images directly in the selected folder(s)."
            )
            self._update_generate_button()
            return

        pending = []
        skipped = 0
        for asset in assets:
            path = asset.get("path", "")
            if path and service.thumbnail_is_fresh(path):
                skipped += 1
            elif path:
                pending.append(asset)

        if not pending:
            self.status_label.setText(
                "All %d thumbnail(s) are up to date — skipped."
                % skipped
            )
            self._schedule_visible_thumbnails()
            self._update_generate_button()
            return

        self._thumbnail_batch = {
            "total": len(pending),
            "completed": 0,
            "failed": 0,
            "skipped": skipped,
        }
        self._update_generate_button()
        for asset in pending:
            self._thumbnail_queue.append(
                {
                    "path": asset.get("path", ""),
                    "record_key": (
                        asset.get("source_id", ""),
                        os.path.normcase(asset.get("path", "")),
                    ),
                    "generation": self._view_generation,
                    "manual": True,
                }
            )
        self._update_thumbnail_batch_status()
        self._start_next_thumbnail()

    def _update_thumbnail_batch_status(self):
        batch = self._thumbnail_batch
        if batch is None:
            return
        text = "Generating thumbnails: %d/%d" % (
            batch["completed"],
            batch["total"],
        )
        if batch["skipped"]:
            text += " — %d up to date" % batch["skipped"]
        if batch["failed"]:
            text += " — %d failed" % batch["failed"]
        self.status_label.setText(text)

    def _finish_thumbnail_batch(self):
        batch = self._thumbnail_batch
        if batch is None:
            return
        generated = batch["total"] - batch["failed"]
        text = "Thumbnail generation complete: %d generated" % generated
        if batch["skipped"]:
            text += ", %d skipped" % batch["skipped"]
        if batch["failed"]:
            text += ", %d failed" % batch["failed"]
        self.status_label.setText(text + ".")
        self._thumbnail_batch = None
        self._update_generate_button()
        self._schedule_visible_thumbnails()

    def _refresh_asset_view(self):
        if self._closing:
            return
        query = self.search_edit.text().strip()
        assets = self.scan_result.get("assets", [])
        if query:
            records = service.aggregate_assets(
                service.search_assets(assets, query)
            )
            empty_message = "No images match the global search."
        else:
            item = self.source_tree.currentItem()
            if item is None:
                records = []
            else:
                records = service.display_records(
                    service.assets_in_directory(
                        assets,
                        item.data(0, SOURCE_ID_ROLE),
                        item.data(0, PATH_ROLE),
                    )
                )
            empty_message = (
                "No supported images directly in this folder. "
                "Select a subfolder or search all sources."
            )
        records = service.sort_assets(
            records,
            self.sort_combo.currentData() or "name",
            self.order_button.isChecked(),
        )
        self._view_generation += 1
        self._thumbnail_queue = deque(
            job
            for job in self._thumbnail_queue
            if job.get("manual")
        )
        self._thumbnail_requested.clear()
        self.asset_model.set_records(records)
        self._clear_details()
        if records:
            failure_count = len(self.scan_result.get("failures", []))
            text = "%d image(s)" % len(records)
            if query:
                text += " in global search"
            if failure_count:
                text += " — %d scan warning(s)" % failure_count
            self.status_label.setText(text)
        elif not self.sources:
            self.status_label.setText(
                "No sources configured. Click Add Source to begin."
            )
        else:
            self.status_label.setText(empty_message)
        QTimer.singleShot(0, self._schedule_visible_thumbnails)

    def eventFilter(self, watched, event):
        if (
            watched is self.asset_view.viewport()
            and event.type() in (QEvent.Resize, QEvent.Show)
        ):
            self._update_thumbnail_icon_metrics()
            self._schedule_visible_thumbnails()
        return super(AssetLibraryWidget, self).eventFilter(
            watched,
            event,
        )

    def _update_thumbnail_icon_metrics(self):
        ratio_reader = getattr(
            self.asset_view,
            "devicePixelRatioF",
            None,
        )
        if not callable(ratio_reader):
            ratio_reader = getattr(
                self.asset_view,
                "devicePixelRatio",
                None,
            )
        try:
            ratio = ratio_reader() if callable(ratio_reader) else 1.0
        except Exception:
            ratio = 1.0
        self.asset_model.set_icon_metrics(
            self._thumbnail_display_size,
            ratio,
        )

    def _schedule_visible_thumbnails(self, *_args):
        if not self._thumbnail_timer.isActive():
            self._thumbnail_timer.start()

    def _queue_visible_thumbnails(self):
        row_count = self.asset_model.rowCount()
        if not row_count:
            return
        viewport = self.asset_view.viewport().rect()
        grid = self.asset_view.gridSize()
        columns = max(
            1,
            viewport.width() // max(1, grid.width()),
        )
        scroll = self.asset_view.verticalScrollBar().value()
        first_grid_row = max(
            0,
            scroll // max(1, grid.height()) - 1,
        )
        last_grid_row = (
            (scroll + viewport.height() * 2)
            // max(1, grid.height())
            + 1
        )
        first_row = min(row_count, first_grid_row * columns)
        last_row = min(
            row_count,
            (last_grid_row + 1) * columns,
        )
        rows = range(first_row, last_row)

        for row in rows:
            record = self.asset_model.records[row]
            locations = record.get("locations") or [record]
            path = locations[0].get("path", "")
            if not path or not service.thumbnail_is_fresh(path):
                continue
            token = (
                self._view_generation,
                record.get("record_key"),
                service.source_key(path),
            )
            if token in self._thumbnail_requested:
                continue
            self._thumbnail_requested.add(token)
            self._thumbnail_queue.append(
                {
                    "path": path,
                    "record_key": record.get("record_key"),
                    "generation": self._view_generation,
                    "manual": False,
                }
            )
        self._start_next_thumbnail()

    def _start_next_thumbnail(self):
        if self._closing:
            return
        while (
            self._thumbnail_queue
            and len(self._thumbnail_threads) < MAX_THUMBNAIL_WORKERS
        ):
            active_hdr = sum(
                1
                for thread in self._thumbnail_threads
                if thread.is_hdr
            )
            job_index = None
            for index, candidate in enumerate(self._thumbnail_queue):
                extension = os.path.splitext(
                    candidate.get("path", "")
                )[1].lower()
                if (
                    extension in HDR_EXTENSIONS
                    and active_hdr >= MAX_HDR_THUMBNAIL_WORKERS
                ):
                    continue
                job_index = index
                break
            if job_index is None:
                return

            job = self._thumbnail_queue[job_index]
            del self._thumbnail_queue[job_index]
            thread = _ThumbnailThread(
                self.core,
                job["path"],
                job["record_key"],
                job["generation"],
                THUMBNAIL_SIZE,
                manual=job.get("manual", False),
            )
            thread.is_hdr = (
                os.path.splitext(job["path"])[1].lower()
                in HDR_EXTENSIONS
            )
            _track_thread(thread)
            thread.resultReady.connect(self._on_thumbnail_result)
            thread.finished.connect(
                lambda current=thread: self._on_thumbnail_finished(
                    current
                )
            )
            self._thumbnail_threads.add(thread)
            thread.start()

    def _on_thumbnail_result(self, result):
        if result.get("manual") and self._thumbnail_batch is not None:
            self._thumbnail_batch["completed"] += 1
            if result.get("error") or result.get("cache_error"):
                self._thumbnail_batch["failed"] += 1
            self._update_thumbnail_batch_status()
        if result.get("width") and result.get("height"):
            self._resolution_cache[
                service.source_key(result.get("path"))
            ] = (result["width"], result["height"])
        if (
            self._closing
            or result.get("generation") != self._view_generation
        ):
            return
        image = result.get("image")
        if image is not None and not image.isNull():
            self.asset_model.set_thumbnail(
                result.get("record_key"),
                image,
            )
        if result.get("error"):
            self._thumbnail_failures += 1
            self._append_status_tooltip(
                "%s: %s"
                % (result.get("path", ""), result.get("error", ""))
            )
        if result.get("cache_error"):
            self._append_status_tooltip(
                "%s: %s"
                % (
                    result.get("path", ""),
                    result.get("cache_error", ""),
                )
            )
        self._update_selected_resolution()
        if (
            service.source_key(result.get("path", ""))
            == service.source_key(self._selected_path())
        ):
            self._update_detail_preview()

    def _on_thumbnail_finished(self, thread):
        self._thumbnail_threads.discard(thread)
        if (
            thread.manual
            and self._thumbnail_batch is not None
            and self._thumbnail_batch["completed"]
            >= self._thumbnail_batch["total"]
        ):
            self._finish_thumbnail_batch()
        if not self._closing:
            self._start_next_thumbnail()

    def _on_asset_selection_changed(self, current, _previous):
        record = self.asset_model.record(current)
        self._selected_record = record
        if record is None:
            self._clear_details()
            return
        self.detail_name.setText(record.get("filename", "-"))
        self.detail_size.setText(_format_bytes(record.get("size", 0)))
        self.detail_modified.setText(
            _format_timestamp(record.get("mtime_ns", 0))
        )
        locations = record.get("locations") or [record]
        relative_paths = [
            os.path.join(
                location.get("relative_directory", ""),
                location.get("filename", ""),
            )
            for location in locations
        ]
        self.detail_categories.setText(
            ", ".join(relative_paths) if relative_paths else "-"
        )
        self.location_combo.blockSignals(True)
        self.location_combo.clear()
        for location, relative_path in zip(locations, relative_paths):
            self.location_combo.addItem(
                relative_path or location.get("filename", ""),
                location.get("path", ""),
            )
        self.location_combo.blockSignals(False)
        if self.location_combo.count():
            self.location_combo.setCurrentIndex(0)
        self._on_location_changed()

    def _on_location_changed(self, *_args):
        path = self._selected_path()
        self.detail_path.setText(path)
        enabled = bool(path and os.path.isfile(path))
        self.open_button.setEnabled(enabled)
        self.reveal_button.setEnabled(enabled)
        self.copy_button.setEnabled(bool(path))
        self._update_selected_resolution()
        self._update_detail_preview()

    def _selected_path(self):
        return self.location_combo.currentData() or ""

    def _update_selected_resolution(self):
        resolution = self._resolution_cache.get(
            service.source_key(self._selected_path())
        )
        if resolution and resolution[0] and resolution[1]:
            self.detail_resolution.setText(
                "%d x %d" % (resolution[0], resolution[1])
            )
        else:
            self.detail_resolution.setText("-")

    def _update_detail_preview(self):
        path = self._selected_path()
        cache_path = service.thumbnail_path(path) if path else ""
        if not path or not service.thumbnail_is_fresh(path, cache_path):
            self._set_detail_preview_placeholder()
            return
        image = QImage(cache_path)
        if image.isNull():
            self._set_detail_preview_placeholder()
            return
        ratio_reader = getattr(
            self.detail_preview,
            "devicePixelRatioF",
            None,
        )
        if not callable(ratio_reader):
            ratio_reader = getattr(
                self.detail_preview,
                "devicePixelRatio",
                None,
            )
        try:
            ratio = float(
                ratio_reader() if callable(ratio_reader) else 1.0
            )
        except (TypeError, ValueError):
            ratio = 1.0
        ratio = max(1.0, ratio)
        target_size = QSize(
            max(1, int(round(self.detail_preview.width() * ratio))),
            max(1, int(round(self.detail_preview.height() * ratio))),
        )
        display_image = image.scaled(
            target_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        pixmap = QPixmap.fromImage(display_image)
        if pixmap.isNull():
            self._set_detail_preview_placeholder()
            return
        set_device_pixel_ratio = getattr(
            pixmap,
            "setDevicePixelRatio",
            None,
        )
        if callable(set_device_pixel_ratio):
            set_device_pixel_ratio(ratio)
        self.detail_preview.setText("")
        self.detail_preview.setPixmap(pixmap)

    def _set_detail_preview_placeholder(self):
        self.detail_preview.clear()
        self.detail_preview.setText("No cached preview")

    def _clear_details(self):
        self._selected_record = None
        self.detail_name.setText("-")
        self.detail_resolution.setText("-")
        self.detail_size.setText("-")
        self.detail_modified.setText("-")
        self.detail_categories.setText("-")
        self.location_combo.blockSignals(True)
        self.location_combo.clear()
        self.location_combo.blockSignals(False)
        self.detail_path.clear()
        self.open_button.setEnabled(False)
        self.reveal_button.setEnabled(False)
        self.copy_button.setEnabled(False)
        self._set_detail_preview_placeholder()

    def _show_asset_context_menu(self, position):
        index = self.asset_view.indexAt(position)
        if not index.isValid():
            return
        self.asset_view.setCurrentIndex(index)
        menu = QMenu(self)
        menu.addAction("Open", self.open_selected)
        menu.addAction("Reveal in Explorer", self.reveal_selected)
        menu.addAction("Copy Path", self.copy_selected_path)
        self._add_houdini_asset_action(menu, self._selected_path())
        menu.exec_(self.asset_view.viewport().mapToGlobal(position))

    def _add_houdini_asset_action(self, menu, path):
        bridge = self._get_houdini_asset_bridge()
        descriptor = bridge.describe_action(path)
        if descriptor is None:
            return None
        target = descriptor.get("target")
        menu.addSeparator()
        return menu.addAction(
            descriptor["label"],
            lambda checked=False, selected_path=path, selected_target=target: (
                self._create_houdini_environment_light(
                    selected_path,
                    selected_target,
                )
            ),
        )

    def _get_houdini_asset_bridge(self):
        if self._houdini_asset_bridge is None:
            self._houdini_asset_bridge = HoudiniAssetBridge(self.core)
        return self._houdini_asset_bridge

    def _create_houdini_environment_light(self, path, target):
        bridge = self._get_houdini_asset_bridge()
        if target is None:
            self._show_warning(
                "The current Houdini context cannot contain an "
                "environment light. Open /obj or enter a LOP network "
                "such as /stage, then try again."
            )
            return

        target_path = target.get("network_path")
        result = bridge.create_environment_light(path, target_path)
        if not result.get("success"):
            self._show_warning(result.get("message", "Creation failed."))

    def open_selected(self):
        path = self._selected_path()
        if path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def reveal_selected(self):
        path = self._selected_path()
        if not path:
            return
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer.exe", "/select,", path])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", path])
            else:
                QDesktopServices.openUrl(
                    QUrl.fromLocalFile(os.path.dirname(path))
                )
        except OSError as exc:
            self._show_warning(str(exc))

    def copy_selected_path(self):
        path = self._selected_path()
        if path:
            QApplication.clipboard().setText(path)

    def _show_warning(self, message):
        popup = getattr(self.core, "popup", None)
        if popup is not None:
            popup(message, severity="warning")
        else:
            QMessageBox.warning(self, "Asset Library", message)

    def _append_status_tooltip(self, message):
        current = self.status_label.toolTip()
        self.status_label.setToolTip(
            (current + "\n" + message).strip()
        )

    def closeEvent(self, event):
        self._closing = True
        self._thumbnail_queue.clear()
        if self._scan_thread is not None:
            self._scan_thread.cancel()
        super(AssetLibraryWidget, self).closeEvent(event)


def _format_bytes(size):
    value = float(size or 0)
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            if unit == "B":
                return "%d %s" % (int(value), unit)
            return "%.1f %s" % (value, unit)
        value /= 1024.0
    return "0 B"


def _format_timestamp(mtime_ns):
    if not mtime_ns:
        return "-"
    try:
        value = float(mtime_ns) / 1000000000.0
        return datetime.datetime.fromtimestamp(value).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except (OverflowError, OSError, ValueError):
        return "-"
