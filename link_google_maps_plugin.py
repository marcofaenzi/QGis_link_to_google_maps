from qgis.PyQt.QtCore import QObject, QCoreApplication, QSize, QTranslator, QLocale, QSettings
from qgis.PyQt.QtWidgets import QAction, QApplication, QToolButton, QMenu
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface
from qgis.gui import QgsMapTool
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform
import os
from PyQt5.Qt import QDesktopServices, QUrl

PLUGIN_PATH = os.path.dirname(os.path.abspath(__file__))

ICON_CLIP = os.path.join(PLUGIN_PATH, 'icon_clipboard.png')
ICON_BROWSER = os.path.join(PLUGIN_PATH, 'icon_browser.png')
ICON_STREET = os.path.join(PLUGIN_PATH, 'icon_streetview.png')

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
        self.btn.setToolButtonStyle(2)
        self.menu = QMenu()
        self.menu.setBaseSize(QSize(48, 48))
        self.action_copy = self.menu.addAction(QIcon(ICON_CLIP), tr('Copy Google Maps link'))
        self.action_browser = self.menu.addAction(QIcon(ICON_BROWSER), tr('Open on Google Maps in browser'))
        self.action_street = self.menu.addAction(QIcon(ICON_STREET), tr('Open Street View in browser'))
        self.btn.setIcon(QIcon(ICON_CLIP))
        self.btn.setMenu(self.menu)
        self.btn.setPopupMode(QToolButton.MenuButtonPopup)
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
