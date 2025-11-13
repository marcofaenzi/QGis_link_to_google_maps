from qgis.PyQt.QtCore import QObject, QCoreApplication, QSize
from qgis.PyQt.QtWidgets import QAction, QApplication, QToolButton, QMenu
from qgis.PyQt.QtGui import QIcon
from qgis.utils import iface
from qgis.gui import QgsMapTool
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from PyQt5.QtCore import QSize  
import os
from PyQt5.Qt import QDesktopServices, QUrl

PLUGIN_PATH = os.path.dirname(os.path.abspath(__file__))

ICON_CLIP = os.path.join(PLUGIN_PATH, 'icon_clipboard.png')
ICON_BROWSER = os.path.join(PLUGIN_PATH, 'icon_browser.png')
ICON_STREET = os.path.join(PLUGIN_PATH, 'icon_streetview.png')

def tr(msg):
    return QCoreApplication.translate('LinkGoogleMapsPlugin', msg)

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

    def initGui(self):
        self.btn = QToolButton()
        self.btn.setToolButtonStyle(2)
        self.menu = QMenu()
        self.menu.setBaseSize(QSize(48, 48))
        self.action_copy = self.menu.addAction(QIcon(ICON_CLIP), tr('Copia link Google Maps'))
        self.action_browser = self.menu.addAction(QIcon(ICON_BROWSER), tr('Apri su Google Maps nel browser'))
        self.action_street = self.menu.addAction(QIcon(ICON_STREET), tr('Apri Street View nel browser'))
        self.btn.setIcon(QIcon(ICON_CLIP))
        self.btn.setMenu(self.menu)
        self.btn.setPopupMode(QToolButton.MenuButtonPopup)
        self.btn.clicked.connect(self.trigger_current_action)
        self.action_copy.triggered.connect(lambda: self.set_main_action('copy'))
        self.action_browser.triggered.connect(lambda: self.set_main_action('browser'))
        self.action_street.triggered.connect(lambda: self.set_main_action('streetview'))
        self.btn.setToolTip(tr('Copia link Google Maps'))
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
            self.btn.setToolTip(tr('Copia link Google Maps'))
        elif mode == 'browser':
            self.btn.setIcon(QIcon(ICON_BROWSER))
            self.btn.setToolTip(tr('Apri su Google Maps nel browser'))
        elif mode == 'streetview':
            self.btn.setIcon(QIcon(ICON_STREET))
            self.btn.setToolTip(tr('Apri Street View nel browser'))
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
            iface.messageBar().pushSuccess('Link Google Maps copiato!', gmaps_link)
        elif self.current_action == 'browser':
            gmaps_link = f'https://maps.google.com/?q={lat},{lng}'
            QDesktopServices.openUrl(QUrl(gmaps_link))
            iface.messageBar().pushSuccess('Google Maps aperto nel browser', gmaps_link)
        elif self.current_action == 'streetview':
            street_link = f'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lng}'
            QDesktopServices.openUrl(QUrl(street_link))
            iface.messageBar().pushSuccess('Street View aperto nel browser', street_link)
