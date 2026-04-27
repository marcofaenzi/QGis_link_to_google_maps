from qgis.PyQt.QtCore import QObject, QCoreApplication, QSize, QTranslator, QLocale, QSettings, QUrl, Qt
from qgis.PyQt.QtWidgets import QAction, QApplication, QToolButton, QMenu, QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QComboBox
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.utils import iface
from qgis.gui import QgsMapTool, QgsVertexMarker
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform
import os
try:
    from qgis.PyQt.QtGui import QDesktopServices  # PyQt6 / QGIS 4
except ImportError:
    from qgis.PyQt.QtCore import QDesktopServices  # PyQt5 / QGIS 3
import json
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

PLUGIN_PATH = os.path.dirname(os.path.abspath(__file__))

ICON_CLIP = os.path.join(PLUGIN_PATH, 'icon_clipboard.png')
ICON_BROWSER = os.path.join(PLUGIN_PATH, 'icon_browser.png')
ICON_STREET = os.path.join(PLUGIN_PATH, 'icon_streetview.png')
ICON_SEARCH = os.path.join(PLUGIN_PATH, 'map_search.png')

def tr(msg):
    return QCoreApplication.translate('@default', msg)

class SingleClickMapTool(QgsMapTool):
    def __init__(self, canvas, callback):
        super().__init__(canvas)
        self.canvas = canvas
        self.callback = callback
    def canvasReleaseEvent(self, event):
        point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos().x(), event.pos().y())
        self.callback(point)
        iface.mapCanvas().unsetMapTool(self)

class LinkGoogleMapsPlugin(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.btn = None
        self.menu = None
        self.action_copy = None
        self.action_browser = None
        self.action_street = None
        self.map_tool = None
        self.current_action = 'copy'  # 'copy', 'browser', 'streetview'
        self.translator = None
        self._load_translator()
        # Search action
        self.search_action = None
        # Search marker
        self.search_marker = None
        # Keys
        self._settings_zoom_key = 'plugins/LinkToGoogleMaps/zoomScale'
        self._settings_history_key = 'plugins/LinkToGoogleMaps/searchHistory'
        self._history_max_items = 10

    def _load_translator(self):
        # Rispetta la lingua di QGIS (non quella di sistema): usa overrideFlag e userLocale.
        # Default: inglese (nessun translator).
        lang = 'en'
        try:
            settings = QSettings()
            override_flag = settings.value('locale/overrideFlag', False, type=bool)
            if override_flag:
                user_locale = settings.value('locale/userLocale', '', type=str) or ''
                if user_locale:
                    lang = user_locale[0:2].lower()
            else:
                lang = QLocale().name()[0:2].lower()
        except Exception:
            lang = 'en'

        if lang != 'en':
            qm_path = os.path.join(PLUGIN_PATH, 'i18n', f'LinkToGoogleMaps_{lang}.qm')
            if os.path.exists(qm_path):
                self.translator = QTranslator()
                if self.translator.load(qm_path):
                    QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        self.btn = QToolButton()
        # Qt6 uses enum Qt.ToolButtonStyle; Qt5 used int. Value 2 = TextBesideIcon
        try:
            style = Qt.ToolButtonStyle.ToolButtonTextBesideIcon  # PyQt6 / QGIS 4
        except AttributeError:
            style = Qt.ToolButtonTextBesideIcon  # PyQt5 / QGIS 3
        self.btn.setToolButtonStyle(style)
        self.menu = QMenu()
        self.menu.setBaseSize(QSize(48, 48))
        self.action_copy = self.menu.addAction(QIcon(ICON_CLIP), tr('Copy Google Maps link'))
        self.action_browser = self.menu.addAction(QIcon(ICON_BROWSER), tr('Open on Google Maps in browser'))
        self.action_street = self.menu.addAction(QIcon(ICON_STREET), tr('Open Street View in browser'))
        self.menu.addSeparator()
        self.search_action = self.menu.addAction(QIcon(ICON_SEARCH), tr('Search address'))
        self.search_action.triggered.connect(self._open_search_dialog)
        self.btn.setIcon(QIcon(ICON_CLIP))
        self.btn.setMenu(self.menu)
        # Qt6: enum under QToolButton.ToolButtonPopupMode; Qt5: QToolButton.MenuButtonPopup
        try:
            popup_mode = QToolButton.ToolButtonPopupMode.MenuButtonPopup  # PyQt6 / QGIS 4
        except AttributeError:
            popup_mode = QToolButton.MenuButtonPopup  # PyQt5 / QGIS 3
        self.btn.setPopupMode(popup_mode)
        self.btn.clicked.connect(self.trigger_current_action)
        self.action_copy.triggered.connect(lambda: self.set_main_action('copy'))
        self.action_browser.triggered.connect(lambda: self.set_main_action('browser'))
        self.action_street.triggered.connect(lambda: self.set_main_action('streetview'))
        self.btn.setToolTip(tr('Copy Google Maps link'))
        iface.addToolBarWidget(self.btn)

    def unload(self):
        if self.btn is not None:
            self.btn.setParent(None)
            self.btn.deleteLater()
            self.btn = None
        self.search_action = None
        if self.search_marker is not None:
            try:
                self.search_marker.setVisible(False)
                iface.mapCanvas().scene().removeItem(self.search_marker)
            except Exception:
                pass
            self.search_marker = None
        if self.map_tool:
            iface.mapCanvas().unsetMapTool(self.map_tool)

    def set_main_action(self, mode):
        self.current_action = mode
        if mode == 'copy':
            self.btn.setIcon(QIcon(ICON_CLIP))
            self.btn.setToolTip(tr('Copy Google Maps link'))
        elif mode == 'browser':
            self.btn.setIcon(QIcon(ICON_BROWSER))
            self.btn.setToolTip(tr('Open on Google Maps in browser'))
        elif mode == 'streetview':
            self.btn.setIcon(QIcon(ICON_STREET))
            self.btn.setToolTip(tr('Open Street View in browser'))
        self.trigger_current_action()

    def trigger_current_action(self):
        self.map_tool = SingleClickMapTool(iface.mapCanvas(), self.handle_map_click)
        iface.mapCanvas().setMapTool(self.map_tool)

    def handle_map_click(self, qgs_point):
        crs_src = QgsProject.instance().crs()
        crs_dest = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        pt_wgs84 = xform.transform(qgs_point)
        lat = pt_wgs84.y()
        lng = pt_wgs84.x()
        if self.current_action == 'copy':
            gmaps_link = f'https://maps.google.com/?q={lat},{lng}'
            QApplication.clipboard().setText(gmaps_link)
            iface.messageBar().pushSuccess(tr('Google Maps link copied!'), gmaps_link)
        elif self.current_action == 'browser':
            gmaps_link = f'https://maps.google.com/?q={lat},{lng}'
            QDesktopServices.openUrl(QUrl(gmaps_link))
            iface.messageBar().pushSuccess(tr('Opened Google Maps in browser'), gmaps_link)
        elif self.current_action == 'streetview':
            street_link = f'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lng}'
            QDesktopServices.openUrl(QUrl(street_link))
            iface.messageBar().pushSuccess(tr('Opened Street View in browser'), street_link)

    def _open_search_dialog(self):
        dlg = QDialog(iface.mainWindow())
        dlg.setWindowTitle(tr('Search address'))
        try:
            dlg.setMinimumWidth(520)
        except Exception:
            pass
        layout = QVBoxLayout(dlg)
        label = QLabel(tr('Enter address to locate'))
        # Editable combo as address box with history dropdown
        combo = QComboBox()
        combo.setEditable(True)
        try:
            insert_policy = QComboBox.InsertPolicy.NoInsert  # PyQt6 / QGIS 4
        except AttributeError:
            insert_policy = QComboBox.NoInsert  # PyQt5 / QGIS 3
        combo.setInsertPolicy(insert_policy)
        # Placeholder on the embedded line edit
        if combo.lineEdit() is not None:
            combo.lineEdit().setPlaceholderText(tr('Search address...'))
        # Load history
        for item in self._load_search_history():
            combo.addItem(item)
        # Ensure input starts empty even if history exists
        try:
            combo.setCurrentIndex(-1)
        except Exception:
            pass
        if combo.lineEdit() is not None:
            combo.lineEdit().clear()
        zoom_label = QLabel(tr('Zoom level'))
        zoom_combo = QComboBox()
        zoom_combo.addItem(tr('Regional (1:100,000)'), 100000)
        zoom_combo.addItem(tr('City (1:10,000)'), 10000)
        zoom_combo.addItem(tr('Street (1:1,000)'), 1000)
        # Default selection and persisted preference (default = Street 1:1,000)
        try:
            settings = QSettings()
            saved_scale = settings.value('plugins/LinkToGoogleMaps/zoomScale', 1000, type=int)
        except Exception:
            saved_scale = 1000
        # Select matching saved scale, otherwise default to Street
        selected_index = None
        for i in range(zoom_combo.count()):
            if zoom_combo.itemData(i) == saved_scale:
                selected_index = i
                break
        zoom_combo.setCurrentIndex(selected_index if selected_index is not None else 2)
        layout.addWidget(label)
        layout.addWidget(combo)
        layout.addWidget(zoom_label)
        layout.addWidget(zoom_combo)
        try:
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
            )  # PyQt6 / QGIS 4
        except AttributeError:
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)  # PyQt5 / QGIS 3
        layout.addWidget(buttons)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        if combo.lineEdit() is not None:
            combo.lineEdit().returnPressed.connect(dlg.accept)
        # PyQt6 uses exec(), PyQt5 uses exec_(); Qt6: QDialog.DialogCode.Accepted
        run_dialog = getattr(dlg, 'exec', None) or getattr(dlg, 'exec_')
        try:
            accepted_code = QDialog.DialogCode.Accepted  # PyQt6 / QGIS 4
        except AttributeError:
            accepted_code = QDialog.Accepted  # PyQt5 / QGIS 3
        if run_dialog() == accepted_code:
            current_text = combo.currentText() if combo.currentText() is not None else ''
            query = (current_text or '').strip()
            scale = zoom_combo.currentData() or 1000
            # Persist user choice
            try:
                settings = QSettings()
                settings.setValue(self._settings_zoom_key, int(scale))
            except Exception:
                pass
            self._perform_search(query, scale)

    def _perform_search(self, query: str, scale: int):
        if not query:
            iface.messageBar().pushWarning(tr('Address not found'), tr('Please enter an address'))
            return
        try:
            result = self._geocode_address(query)
        except Exception:
            iface.messageBar().pushWarning(tr('Network error while searching'), query)
            return
        if not result:
            iface.messageBar().pushInfo(tr('Address not found'), query)
            return
        lat, lng = result
        # Update search history (dedup, most recent first, max 10)
        try:
            self._add_to_search_history(query)
        except Exception:
            pass
        # Transform WGS84 -> project CRS
        crs_src = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        crs_dest = QgsProject.instance().crs()
        xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        pt = xform.transform(lng, lat)
        canvas = iface.mapCanvas()
        canvas.setCenter(pt)
        try:
            canvas.zoomScale(float(scale))
        except Exception:
            pass
        canvas.refresh()
        # Add/update a marker at the located point
        try:
            if self.search_marker is None:
                self.search_marker = QgsVertexMarker(canvas)
                self.search_marker.setIconType(QgsVertexMarker.ICON_CROSS)
                self.search_marker.setColor(QColor(220, 30, 30))
                self.search_marker.setPenWidth(3)
                self.search_marker.setIconSize(14)
            self.search_marker.setCenter(pt)
            self.search_marker.setVisible(True)
        except Exception:
            pass
        iface.messageBar().pushSuccess(tr('Centered on result'), f'{lat:.6f}, {lng:.6f}')

    def _load_search_history(self):
        settings = QSettings()
        raw = settings.value(self._settings_history_key, '[]', type=str)
        try:
            items = json.loads(raw)
            if isinstance(items, list):
                # Only keep strings
                return [str(x) for x in items if isinstance(x, str)]
        except Exception:
            pass
        return []

    def _save_search_history(self, items):
        try:
            settings = QSettings()
            settings.setValue(self._settings_history_key, json.dumps(items))
        except Exception:
            pass

    def _add_to_search_history(self, query: str):
        if not query:
            return
        items = self._load_search_history()
        items = [x for x in items if x.strip() and x.strip().lower() != query.strip().lower()]
        items.insert(0, query.strip())
        if len(items) > self._history_max_items:
            items = items[: self._history_max_items]
        self._save_search_history(items)

    def _geocode_address(self, address):
        # Use OSM Nominatim (no key). Respect usage: provide UA.
        params = {
            'q': address,
            'format': 'jsonv2',
            'limit': 1,
        }
        url = 'https://nominatim.openstreetmap.org/search?' + urlencode(params)
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.netloc != 'nominatim.openstreetmap.org':
            raise ValueError('Only HTTPS Nominatim endpoint is allowed')
        req = Request(url, headers={
            'User-Agent': f'LinkToGoogleMaps QGIS Plugin/1.0.2 ({QApplication.instance().applicationName()})'
        })
        with urlopen(req, timeout=10) as resp:  # nosec B310 - validated https scheme and fixed trusted host above
            payload = resp.read()
        data = json.loads(payload.decode('utf-8'))
        if isinstance(data, list) and data:
            top = data[0]
            lat = float(top.get('lat'))
            lon = float(top.get('lon'))
            return (lat, lon)
        return None
