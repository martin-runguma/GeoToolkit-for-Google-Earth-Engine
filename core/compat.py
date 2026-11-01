"""Small shims so the same code runs on QGIS 3.28+ and 4.x."""
from qgis.core import Qgis, QgsMapLayerProxyModel, QgsWkbTypes
from qgis.gui import QgsFileWidget

try:
    POLYGON_GEOM = Qgis.GeometryType.Polygon
except AttributeError:
    POLYGON_GEOM = QgsWkbTypes.GeometryType.PolygonGeometry

FILE_GET_FILE = QgsFileWidget.StorageMode.GetFile
FILE_GET_DIR = QgsFileWidget.StorageMode.GetDirectory

_LEVELS = {"info": "Info", "success": "Success", "warning": "Warning", "critical": "Critical"}


def message_level(name):
    attr = _LEVELS.get(name, "Info")
    try:
        return getattr(Qgis.MessageLevel, attr)
    except AttributeError:
        return getattr(Qgis, attr)


def polygon_layer_filter():
    try:
        return Qgis.LayerFilter.PolygonLayer
    except AttributeError:
        return QgsMapLayerProxyModel.Filter.PolygonLayer
