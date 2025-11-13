# Questo file indica a QGIS che questa directory è un plugin Python.
from .link_google_maps_plugin import LinkGoogleMapsPlugin

def classFactory(iface):
    return LinkGoogleMapsPlugin()
