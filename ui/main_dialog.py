"""Five-step GeoToolkit for Google Earth Engine interface for QGIS."""
from __future__ import annotations

import os
import re
import csv
import time
import uuid
from datetime import datetime, timezone
from qgis.PyQt.QtCore import QObject, Qt, QDate, QLocale, QSettings, QThread, QTimer, pyqtSignal
from qgis.PyQt.QtGui import QColor, QFont, QIcon, QPixmap
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFrame,
    QInputDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qgis.core import (Qgis, QgsMessageLog, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsDistanceArea,
                       QgsGeometry, QgsProject, QgsUnitTypes, QgsVectorLayer)
from ..core.compat import POLYGON_GEOM
from ..core.earth_engine_downloads import EarthEngineDownloadWorker


STEPS = (
    "Area of Interest",
    "Dataset Selection",
    "Dataset Options",
    "Output and Run",
    "Results",
)

US_STATES = (
    ("AL", "Alabama"), ("AK", "Alaska"), ("AZ", "Arizona"), ("AR", "Arkansas"),
    ("CA", "California"), ("CO", "Colorado"), ("CT", "Connecticut"), ("DE", "Delaware"),
    ("DC", "District of Columbia"), ("FL", "Florida"), ("GA", "Georgia"), ("HI", "Hawaii"),
    ("ID", "Idaho"), ("IL", "Illinois"), ("IN", "Indiana"), ("IA", "Iowa"),
    ("KS", "Kansas"), ("KY", "Kentucky"), ("LA", "Louisiana"), ("ME", "Maine"),
    ("MD", "Maryland"), ("MA", "Massachusetts"), ("MI", "Michigan"), ("MN", "Minnesota"),
    ("MS", "Mississippi"), ("MO", "Missouri"), ("MT", "Montana"), ("NE", "Nebraska"),
    ("NV", "Nevada"), ("NH", "New Hampshire"), ("NJ", "New Jersey"), ("NM", "New Mexico"),
    ("NY", "New York"), ("NC", "North Carolina"), ("ND", "North Dakota"), ("OH", "Ohio"),
    ("OK", "Oklahoma"), ("OR", "Oregon"), ("PA", "Pennsylvania"), ("RI", "Rhode Island"),
    ("SC", "South Carolina"), ("SD", "South Dakota"), ("TN", "Tennessee"), ("TX", "Texas"),
    ("UT", "Utah"), ("VT", "Vermont"), ("VA", "Virginia"), ("WA", "Washington"),
    ("WV", "West Virginia"), ("WI", "Wisconsin"), ("WY", "Wyoming"),
)

CATALOG = [
    {
        "group": "Imagery", "title": "Landsat RGB",
        "provider": "USGS / NASA", "collection": "Landsat Collection 2 Level 2 (Landsat 4–9)",
        "temporal": "1982–present; mission coverage varies", "resolution": "30 m",
        "bands": "L4–7 RGB: SR_B3, SR_B2, SR_B1; L8–9 RGB: SR_B4, SR_B3, SR_B2",
        "formula": "Cloud-masked median RGB surface reflectance over the selected dates.",
        "license": "USGS public domain", "preview": "landsat_rgb.png",
        "coverage": "Global; scene availability varies by region and year.",
        "credit": "Landsat 4–9 data: USGS / NASA.",
        "description": "True-colour Landsat composite made from the median of available clear observations across Landsat 4–9 in the selected date range. Sensor-specific band mapping is used so the red, green, and blue channels stay consistent.",
    },
    {
        "group": "Imagery", "title": "Landsat False Color",
        "provider": "USGS / NASA", "collection": "Landsat 8/9 Collection 2 Level 2",
        "temporal": "Selected date range", "resolution": "30 m",
        "bands": "Red display: SR_B5; Green: SR_B4; Blue: SR_B3",
        "formula": "composite.select(['SR_B5', 'SR_B4', 'SR_B3'])",
        "license": "USGS public domain", "preview": "landsat_false_color.png",
        "coverage": "Global; scene availability varies by region and year.",
        "credit": "Landsat 8/9 data: USGS / NASA.",
        "description": "Near-infrared false-colour composite using the Landsat 8/9 band selection supplied for this toolkit.",
    },
    {
        "group": "Imagery", "title": "Sentinel 2 RGB",
        "provider": "Copernicus / ESA", "collection": "COPERNICUS/S2_SR_HARMONIZED",
        "temporal": "2017–present", "resolution": "10 m",
        "bands": "RGB: B4 (red), B3 (green), B2 (blue)",
        "formula": "Cloud-masked median of B4/B3/B2 surface reflectance.",
        "license": "Copernicus open data", "preview": "sentinel2_rgb.png",
        "coverage": "Global; scene availability varies by region and year.",
        "credit": "Copernicus Sentinel-2 data: European Union / ESA.",
        "description": "True-colour Sentinel-2 surface-reflectance composite. The median is calculated from cloud-masked observations in the selected date range.",
    },
    {
        "group": "Indices", "title": "NDVI — Vegetation Index",
        "provider": "Calculated from Landsat or Sentinel-2 imagery", "collection": "Landsat Collection 2 Level 2 / COPERNICUS/S2_SR_HARMONIZED",
        "temporal": "Selected date range", "resolution": "30 m",
        "bands": "Landsat: SR_B5/SR_B4; Sentinel-2: B8/B4", "formula": "NDVI = (NIR - Red) / (NIR + Red)",
        "license": "Source dependent", "preview": "ndvi.png",
        "coverage": "Coverage follows the selected Landsat or Sentinel-2 imagery source.",
        "credit": "Derived from Landsat Collection 2 (USGS / NASA) or Copernicus Sentinel-2 data (EU / ESA), depending on the selected source.",
        "description": "Normalized Difference Vegetation Index. Highlights relative vegetation greenness using near-infrared and red reflectance. Select Landsat, Sentinel-2, or both in Dataset Options.",
    },
    {
        "group": "Indices", "title": "NDBI — Built-up Index",
        "provider": "Calculated from Landsat or Sentinel-2 imagery", "collection": "Landsat Collection 2 Level 2 / COPERNICUS/S2_SR_HARMONIZED",
        "temporal": "Selected date range", "resolution": "30 m",
        "bands": "Landsat: SR_B6/SR_B5; Sentinel-2: B11/B8", "formula": "NDBI = (SWIR1 - NIR) / (SWIR1 + NIR)",
        "license": "Source dependent", "preview": "ndbi.png",
        "coverage": "Coverage follows the selected Landsat or Sentinel-2 imagery source.",
        "credit": "Derived from Landsat Collection 2 (USGS / NASA) or Copernicus Sentinel-2 data (EU / ESA), depending on the selected source.",
        "description": "Normalized Difference Built-up Index, derived from shortwave-infrared and near-infrared reflectance. Select Landsat, Sentinel-2, or both in Dataset Options.",
    },
    {
        "group": "Indices", "title": "DBSI — Dry Built-up Soil Index",
        "provider": "Calculated from Landsat or Sentinel-2 imagery", "collection": "Landsat Collection 2 Level 2 / COPERNICUS/S2_SR_HARMONIZED",
        "temporal": "Selected date range", "resolution": "30 m",
        "bands": "Landsat: SR_B6/SR_B3 and NDVI SR_B5/SR_B4; Sentinel-2: B11/B3 and NDVI B8/B4",
        "formula": "DBSI = (SWIR1 - Green) / (SWIR1 + Green) - NDVI",
        "license": "Source dependent", "preview": "dbsi.png",
        "coverage": "Coverage follows the selected Landsat or Sentinel-2 imagery source.",
        "credit": "Derived from Landsat Collection 2 (USGS / NASA) or Copernicus Sentinel-2 data (EU / ESA), depending on the selected source.",
        "description": "Dry Built-up Soil Index combining SWIR1/green contrast with NDVI, following the supplied formula. Select Landsat, Sentinel-2, or both in Dataset Options.",
    },
    {
        "group": "Indices", "title": "UI — Urban Index",
        "provider": "Calculated from Landsat or Sentinel-2 imagery", "collection": "Landsat Collection 2 Level 2 / COPERNICUS/S2_SR_HARMONIZED",
        "temporal": "Selected date range", "resolution": "30 m",
        "bands": "Landsat: SR_B7/SR_B5; Sentinel-2: B12/B8",
        "formula": "UI = (SWIR2 - NIR) / (SWIR2 + NIR)",
        "license": "Source dependent", "preview": "ui.png",
        "coverage": "Coverage follows the selected Landsat or Sentinel-2 imagery source.",
        "credit": "Derived from Landsat Collection 2 (USGS / NASA) or Copernicus Sentinel-2 data (EU / ESA), depending on the selected source.",
        "description": "Urban Index using shortwave-infrared 2 and near-infrared surface reflectance bands. Select Landsat, Sentinel-2, or both in Dataset Options.",
    },
    {
        "group": "Indices", "title": "NDWI — Water Index",
        "provider": "Calculated from Landsat or Sentinel-2 imagery", "collection": "Landsat Collection 2 Level 2 / COPERNICUS/S2_SR_HARMONIZED",
        "temporal": "Selected date range", "resolution": "30 m",
        "bands": "Landsat: SR_B3/SR_B5; Sentinel-2: B3/B8", "formula": "NDWI = (Green - NIR) / (Green + NIR)",
        "license": "Source dependent", "preview": "ndwi.png",
        "coverage": "Coverage follows the selected Landsat or Sentinel-2 imagery source.",
        "credit": "Derived from Landsat Collection 2 (USGS / NASA) or Copernicus Sentinel-2 data (EU / ESA), depending on the selected source.",
        "description": "McFeeters Normalized Difference Water Index for highlighting open-water features using green and near-infrared reflectance. Select Landsat, Sentinel-2, or both in Dataset Options.",
    },
    {
        "group": "Indices", "title": "LST — Land Surface Temperature",
        "provider": "USGS / NASA", "collection": "Landsat Collection 2 Level 2",
        "temporal": "1982–present; mission coverage varies", "resolution": "30 m",
        "bands": "ST_B10 (Landsat 8/9); ST_B6 (Landsat 4/5/7)",
        "formula": "Temperature (°C) = scaled ST band (K) - 273.15",
        "license": "USGS public domain", "preview": "lst.png",
        "coverage": "Global; valid surface-temperature coverage varies by scene.",
        "credit": "Landsat Collection 2 surface temperature: USGS / NASA.",
        "description": "Landsat-only surface-temperature product; Sentinel-2 has no thermal band for this LST calculation. Some scenes have no valid temperature band or have known data gaps; cloud and quality masks are applied before compositing.",
    },
    {
        "group": "Other Rasters", "title": "Population (WorldPop Global2 — Count)",
        "provider": "WorldPop", "collection": "WorldPop/GP/100m/R2025A/v1/pop",
        "temporal": "Annual population estimates", "resolution": "100 m",
        "bands": "Population count", "formula": "Single-band population-count raster.",
        "license": "CC BY 4.0; attribution required", "preview": "population_count.png",
        "coverage": "Global; annual products and projection years vary by release.",
        "credit": "WorldPop, University of Southampton. CC BY 4.0; cite www.worldpop.org.",
        "description": "WorldPop Global2 estimated residential population count. This is the count product (people per 100 m grid cell), not age or sex classes. Coverage and years follow the selected release.",
    },
    {
        "group": "Other Rasters", "title": "Building Height (Open Buildings 2.5D Temporal)",
        "provider": "Google Research — Open Buildings", "collection": "GOOGLE/Research/open-buildings-temporal/v1",  # pragma: allowlist secret -- public EE collection ID
        "temporal": "Annual estimates, 2016–2023", "resolution": "4 m effective; 0.5 m raster pixels",
        "bands": "building_height, building_presence, building_fractional_count",
        "formula": "Select building_height for height in metres.",
        "license": "CC BY 4.0 and ODbL 1.0", "preview": "building_height.png",
        "coverage": "Regional: Africa, South/Southeast Asia, Latin America, and the Caribbean.",
        "credit": "Google Research Open Buildings. CC BY 4.0 and ODbL 1.0.",
        "description": "Annual building-presence, fractional-count, and height rasters. Coverage is regional (including Africa, South/Southeast Asia, Latin America, and the Caribbean), not global.",
    },
    {
        "group": "Vector", "title": "Open Buildings Polygon V3",
        "provider": "Google Research — Open Buildings", "collection": "GOOGLE/Research/open-buildings/v3/polygons",
        "temporal": "2023 inference", "resolution": "Building footprints from 50 cm imagery",
        "bands": "Polygon geometry, confidence, Plus Code, area",
        "formula": "Vector building-footprint features.", "license": "CC BY 4.0",
        "preview": "open_buildings_v3.png",
        "coverage": "Regional: Africa, Latin America, the Caribbean, South Asia, and Southeast Asia.",
        "credit": "Google Research Open Buildings V3. CC BY 4.0.",
        "description": "Open Buildings V3 is the polygon-footprint product. It is distinct from the Open Buildings Temporal V1 height raster and covers Africa, Latin America, the Caribbean, South Asia, and Southeast Asia.",
    },
    {
        "group": "Vector", "title": "Microsoft Buildings",
        "provider": "Microsoft Global ML Building Footprints / ORNL USA Structures",
        "collection": "MSBuildings/<country>; ORNL/USA-STRUCTURES/USA_ST_<state code>",
        "temporal": "Release dependent", "resolution": "Footprint polygons; varies by release",
        "bands": "Building polygon geometry and provider attributes",
        "formula": "Vector building-footprint features.", "license": "CDLA Permissive 2.0",
        "preview": "microsoft_buildings.png",
        "coverage": "Coverage varies by region and release.",
        "credit": "Microsoft Global ML Building Footprints. CDLA Permissive 2.0.",
        "description": "Choose a country to load its Microsoft Buildings collection. For the United States, choose a state to use the corresponding ORNL USA Structures asset. Results are clipped to the selected area and exported as a Google Drive table task.",
    },
    {
        "group": "Vector", "title": "OpenBuildingMap (by GFZ)",
        "provider": "GFZ German Research Centre for Geosciences", "collection": "OpenBuildingMap building features",
        "temporal": "Continuously updated source data", "resolution": "Varies by mapping coverage",
        "bands": "Building geometry and available OSM tags",
        "formula": "Vector building-footprint features.", "license": "Open Data Commons ODbL 1.0",
        "preview": "openbuildingmap_gfz.png",
        "coverage": "Global; completeness varies with source coverage.",
        "credit": "Oostwegel et al. (2025), GFZ Data Services, DOI 10.5880/GFZ.LKUT.2025.002. ODbL 1.0.",
        "description": "Building features from OpenBuildingMap by GFZ. Download tiles are identified by level-6 Quadkeys (six digits, each 0–3); enter one or more tile IDs in Dataset Options. Completeness and attributes vary by location.",
    },
    {
        "group": "Vector", "title": "Global Building Atlas Polygons",
        "provider": "GlobalBuildingAtlas", "collection": "Global Building Atlas polygon data",
        "temporal": "Dataset release dependent", "resolution": "Building footprints; release dependent",
        "bands": "Polygon geometry and available building attributes",
        "formula": "Vector building-footprint features.", "license": "CC BY-NC 4.0; source polygons include ODbL data",
        "preview": "global_building_atlas.png",
        "coverage": "Global building polygon coverage.",
        "credit": "Zhu et al. (2025), GlobalBuildingAtlas, DOI 10.5194/essd-17-6647-2025. CC BY-NC 4.0; source data may have additional terms.",
        "description": "Building polygons and associated attributes from the Global Building Atlas. Enter one or more 5-degree grid tile IDs (for example e030_n25_e035_n20) in Dataset Options. Confirm the selected release's terms before export.",
    },
]

BLUE = "#0789cf"
INK = "#183a5a"
MUTED = "#69839b"
LINE = "#cfe1ef"
PALE = "#f2f8fc"


def _qt_member(group_name: str, member: str, legacy_name: str):
    """Resolve scoped Qt6 enums and their Qt5 aliases."""
    group = getattr(Qt, group_name, None)
    if group is not None and hasattr(group, member):
        return getattr(group, member)
    return getattr(Qt, legacy_name)


_CHECKED = _qt_member("CheckState", "Checked", "Checked")
_UNCHECKED = _qt_member("CheckState", "Unchecked", "Unchecked")
_USER_CHECKABLE = _qt_member("ItemFlag", "ItemIsUserCheckable", "ItemIsUserCheckable")
_USER_TRISTATE = _qt_member("ItemFlag", "ItemIsAutoTristate", "ItemIsTristate")
_USER_ROLE = _qt_member("ItemDataRole", "UserRole", "UserRole")
_ALIGN_CENTER = _qt_member("AlignmentFlag", "AlignCenter", "AlignCenter")
_ALIGN_TOP = _qt_member("AlignmentFlag", "AlignTop", "AlignTop")
_ALIGN_LEFT = _qt_member("AlignmentFlag", "AlignLeft", "AlignLeft")
_ALIGN_RIGHT = _qt_member("AlignmentFlag", "AlignRight", "AlignRight")
_KEEP_ASPECT = _qt_member("AspectRatioMode", "KeepAspectRatio", "KeepAspectRatio")
_SMOOTH = _qt_member("TransformationMode", "SmoothTransformation", "SmoothTransformation")
_FRAME_NO_FRAME = getattr(getattr(QFrame, "Shape", QFrame), "NoFrame")


_ACTIVE_EE_THREADS = []


def _release_ee_thread(active):
    try:
        _ACTIVE_EE_THREADS.remove(active)
    except ValueError:
        pass


class EarthEngineConnectionWorker(QObject):
    completed = pyqtSignal(bool, str)

    def __init__(self, project_id: str, authenticate: bool):
        super().__init__()
        self.project_id = project_id
        self.authenticate = authenticate

    def run(self):
        try:
            import ee
            if self.authenticate:
                ee.Authenticate(auth_mode="localhost", quiet=True)
            ee.Initialize(project=self.project_id)
            ee.Number(1).getInfo()
        except ImportError:
            self.completed.emit(
                False,
                "The Earth Engine Python API (earthengine-api) is not installed in QGIS's Python environment. "
                "Install it in the QGIS Python 3.12 environment, then restart QGIS. In OSGeo4W Shell, run: "
                "python -m pip install earthengine-api",
            )
        except Exception as exc:
            self.completed.emit(False, str(exc))
        else:
            self.completed.emit(True, "Earth Engine connection verified.")


def _card(title: str, subtitle: str = "") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(10, 6, 10, 6)
    layout.setSpacing(5)
    heading = QLabel(title)
    heading.setObjectName("cardHeading")
    layout.addWidget(heading)
    if subtitle:
        description = QLabel(subtitle)
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(description)
    return frame, layout


def _field_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("fieldLabel")
    return label


def _combo(items, current=0) -> QComboBox:
    widget = QComboBox()
    widget.addItems(items)
    if items:
        widget.setCurrentIndex(current)
    return widget


class MainDialog(QDialog):
    """A polished, navigable five-stage downloader wizard."""

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.current_step = 0
        self.dataset_checks: dict[str, QCheckBox] = {}
        self.dataset_items: dict[str, QTreeWidgetItem] = {}
        self._connected_selection_layers = set()
        self._ee_thread = None
        self._ee_worker = None
        self._ee_pending_project = ""
        self._ee_notify_on_result = False
        self._download_thread = None
        self._download_worker = None
        self._download_rows = {}
        self._job_started_at = {}
        self._job_elapsed_seconds = {}
        self._job_history_ids = {}
        self._job_history_records = {}
        self._history_row_by_id = {}
        self._history_suppressed_ids = set()
        self.setWindowTitle("GeoToolkit for Google Earth Engine")
        self.icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icon.png")
        self.setWindowIcon(QIcon(self.icon_path))
        # Keep the wizard close to the compact, wide layout in the reference.
        self.setMinimumSize(700, 380)
        self.resize(770, 400)
        self._build()
        self.history_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "download_history.csv")
        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.setInterval(5000)
        self.elapsed_timer.timeout.connect(self._refresh_elapsed_times)
        self._refresh_history_table()
        self._style()
        project = QgsProject.instance()
        project.layersAdded.connect(self._refresh_layers)
        project.layersRemoved.connect(self._refresh_layers)
        self._refresh_layers()
        self._update_step_ui()
        saved_project = QSettings().value("GeoToolkit/GEE/cloudProjectId", "", type=str).strip()
        if saved_project:
            self._start_ee_connection(saved_project, authenticate=False, notify_on_result=False)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header mirrors the deep-blue title strip in the reference image.
        header = QWidget()
        header.setObjectName("titleBar")
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(20, 5, 20, 5)
        header_row.setSpacing(10)
        self.connection_badge = QLabel("●  Not connected")
        self.connection_badge.setObjectName("connectionBadge")
        self.connection_badge.setAlignment(_ALIGN_CENTER)
        self.connection_badge.setMinimumWidth(150)
        self.connection_badge.setFixedHeight(34)
        self.connection_button = QPushButton("Authenticate and Initialize")
        self.connection_button.setToolTip("Sign in to Google and initialize Earth Engine with a Cloud Project.")
        self.connection_button.setObjectName("connectionButton")
        self.connection_button.setMinimumWidth(210)
        self.connection_button.setFixedHeight(34)
        self.connection_button.clicked.connect(self._connect_earth_engine)
        header_row.addWidget(self.connection_badge)
        header_row.addStretch(1)
        header_row.addWidget(self.connection_button)
        root.addWidget(header)

        content = QHBoxLayout()
        content.setSpacing(0)
        root.addLayout(content, 1)

        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(7, 10, 7, 8)
        sidebar_layout.setSpacing(3)
        self.step_buttons = []
        self.step_markers = []
        for index, name in enumerate(STEPS):
            step_row = QWidget()
            step_row.setObjectName("stepRow")
            step_layout = QHBoxLayout(step_row)
            step_layout.setContentsMargins(20, 10, 20, 10)
            step_layout.setSpacing(10)
            marker = QLabel(str(index + 1))
            marker.setObjectName("stepMarker")
            marker.setAlignment(_ALIGN_CENTER)
            step_layout.addWidget(marker)
            button = QPushButton(name)
            button.setObjectName("stepButton")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index: self._go_to(i))
            step_layout.addWidget(button, 1)
            sidebar_layout.addWidget(step_row)
            self.step_buttons.append(button)
            self.step_markers.append(marker)
        sidebar_layout.addStretch(1)
        content.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("pages")
        self.stack.addWidget(self._build_aoi_page())
        self.stack.addWidget(self._build_datasets_page())
        self.stack.addWidget(self._build_options_page())
        self.stack.addWidget(self._build_output_page())
        self.stack.addWidget(self._build_results_page())
        content.addWidget(self.stack, 1)

        footer = QWidget()
        footer.setObjectName("footer")
        footer_row = QGridLayout(footer)
        footer_row.setContentsMargins(20, 10, 20, 10)
        footer_row.setHorizontalSpacing(20)
        footer_row.setVerticalSpacing(5)
        footer_row.setColumnStretch(0, 1)
        footer_row.setColumnStretch(2, 1)
        self.help_button = QPushButton("Help")
        self.help_button.setObjectName("secondaryButton")
        self.help_button.setFixedHeight(25)
        self.help_button.clicked.connect(self._show_help)
        footer_row.addWidget(self.help_button, 0, 0, _ALIGN_LEFT)
        self.step_caption = QLabel("Step 1 of 5")
        self.step_caption.setObjectName("muted")
        footer_row.addWidget(self.step_caption, 0, 1, _ALIGN_CENTER)
        navigation = QWidget()
        navigation_row = QHBoxLayout(navigation)
        navigation_row.setContentsMargins(0, 0, 0, 0)
        navigation_row.setSpacing(20)
        self.back_button = QPushButton("←  Back")
        self.back_button.setObjectName("secondaryButton")
        self.back_button.clicked.connect(lambda: self._go_to(self.current_step - 1))
        navigation_row.addWidget(self.back_button)
        self.next_button = QPushButton("Next  →")
        self.next_button.setObjectName("primaryButton")
        self.next_button.setFixedHeight(25)
        self.next_button.clicked.connect(lambda: self._go_to(self.current_step + 1))
        navigation_row.addWidget(self.next_button)
        footer_row.addWidget(navigation, 0, 2, _ALIGN_RIGHT)
        root.addWidget(footer)

    def _build_aoi_page(self):
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(9, 16, 9, 8)
        row.setSpacing(8)

        source, form = _card("Source")
        form.addWidget(_field_label("Layer type"))
        self.layer_type = _combo(["Polygon layer", "Current map extent"])
        self.layer_type.currentIndexChanged.connect(self._layer_type_changed)
        form.addWidget(self.layer_type)
        form.addWidget(_field_label("Select layer"))
        self.layer_combo = _combo([])
        self.layer_combo.setMinimumWidth(0)
        self.layer_combo.currentIndexChanged.connect(self._update_aoi_summary)
        layer_picker = QHBoxLayout()
        layer_picker.setContentsMargins(20, 5, 20, 5)
        layer_picker.setSpacing(20)
        layer_picker.addWidget(self.layer_combo, 1)
        self.browse_layer_button = QPushButton("Browse…")
        self.browse_layer_button.setObjectName("secondaryButton")
        self.browse_layer_button.setToolTip("Import a polygon layer from a file into this QGIS project")
        self.browse_layer_button.clicked.connect(self._browse_aoi_layer)
        layer_picker.addWidget(self.browse_layer_button)
        form.addLayout(layer_picker)
        self.selected_only = QCheckBox("Use selected features only")
        self.selected_only.setChecked(False)
        self.selected_only.toggled.connect(self._update_aoi_summary)
        form.addWidget(self.selected_only)
        hint = QLabel("Only the selected features from the layer will be used for the download request.")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        form.addWidget(hint)

        processing, processing_layout = _card("Processing")
        processing_layout.addWidget(_field_label("Area calculation method"))
        self.exact_geometry = QRadioButton("Use exact geometry")
        self.bounding_box = QRadioButton("Use bounding box (faster)")
        self.bounding_box.setChecked(True)
        self.exact_geometry.toggled.connect(self._update_aoi_summary)
        self.bounding_box.toggled.connect(self._update_aoi_summary)
        processing_layout.addWidget(self.exact_geometry)
        processing_layout.addWidget(self.bounding_box)
        left = QVBoxLayout()
        left.addWidget(source)
        left.addWidget(processing)
        left.addStretch(1)
        left_widget = QWidget()
        left_widget.setLayout(left)
        row.addWidget(left_widget, 6)

        summary, summary_layout = _card("Summary")
        self.summary_values = {}
        for key in ("Source", "Features", "Area", "CRS"):
            line = QHBoxLayout()
            name = QLabel(key)
            name.setObjectName("summaryKey")
            value = QLabel("—")
            value.setObjectName("summaryValue")
            line.addWidget(name)
            line.addStretch(1)
            line.addWidget(value)
            summary_layout.addLayout(line)
            self.summary_values[key] = value
        info = QLabel("ℹ  The selected features define the area of interest for all selected datasets.")
        info.setObjectName("infoBanner")
        info.setWordWrap(True)
        summary_layout.addSpacing(10)
        summary_layout.addWidget(info)
        summary_layout.addStretch(1)
        summary.setFixedHeight(270)
        row.addWidget(summary, 5, _ALIGN_TOP)
        return page

    def _build_datasets_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        search_row = QHBoxLayout()
        self.dataset_search = QLineEdit()
        self.dataset_search.setPlaceholderText("⌕   Search datasets...")
        self.dataset_search.textChanged.connect(self._filter_datasets)
        search_row.addWidget(self.dataset_search, 1)
        self.free_only = QCheckBox("Show only free datasets")
        search_row.addWidget(self.free_only)
        layout.addLayout(search_row)

        body = QHBoxLayout()
        body.setSpacing(10)
        self.dataset_tree = QTreeWidget()
        self.dataset_tree.setHeaderHidden(True)
        self.dataset_tree.setMinimumWidth(220)
        groups = {}
        group_counts = {group: sum(1 for dataset in CATALOG if dataset["group"] == group)
                        for group in ("Imagery", "Indices", "Other Rasters", "Vector")}
        for dataset in CATALOG:
            group = dataset["group"]
            if group not in groups:
                category = QTreeWidgetItem([f"{group}  ({group_counts[group]})"])
                category.setFlags(category.flags() | _USER_CHECKABLE | _USER_TRISTATE)
                category.setCheckState(0, _UNCHECKED)
                self.dataset_tree.addTopLevelItem(category)
                groups[group] = category
            item = QTreeWidgetItem([dataset["title"]])
            item.setFlags(item.flags() | _USER_CHECKABLE)
            item.setCheckState(0, _UNCHECKED)
            item.setData(0, _USER_ROLE, dataset)
            groups[group].addChild(item)
            self.dataset_items[dataset["title"]] = item
        self.dataset_tree.expandAll()
        self.dataset_tree.itemChanged.connect(self._dataset_tree_changed)
        body.addWidget(self.dataset_tree, 1)

        detail = QFrame()
        detail.setObjectName("card")
        detail_layout = QVBoxLayout(detail)
        detail_layout.setContentsMargins(10, 8, 10, 8)
        detail_layout.setSpacing(5)
        detail_header = QHBoxLayout()
        detail_header.setSpacing(8)
        self.detail_preview = QLabel()
        self.detail_preview.setObjectName("datasetPreview")
        self.detail_preview.setAlignment(_ALIGN_CENTER)
        self.detail_preview.setFixedSize(48, 44)
        detail_header.addWidget(self.detail_preview, 0, _ALIGN_TOP)
        title_block = QVBoxLayout()
        self.detail_title = QLabel("Choose a dataset")
        self.detail_title.setObjectName("detailTitle")
        self.detail_provider = QLabel("Provider details")
        self.detail_provider.setObjectName("muted")
        self.detail_provider.setWordWrap(True)
        title_block.addWidget(self.detail_title)
        title_block.addWidget(self.detail_provider)
        title_block.addStretch(1)
        detail_header.addLayout(title_block, 1)
        detail_layout.addLayout(detail_header)
        detail_layout.addWidget(QFrame())
        self.detail_rows = {}
        for key in ("Description", "Temporal coverage", "Spatial resolution", "Bands", "License", "Credit / attribution", "Collection / source", "Composite / formula"):
            line = QHBoxLayout()
            left = QLabel(key)
            left.setObjectName("summaryKey")
            left.setFixedWidth(100)
            right = QLabel("—")
            right.setObjectName("summaryValue")
            right.setWordWrap(True)
            line.addWidget(left)
            line.addWidget(right, 1)
            detail_layout.addLayout(line)
            self.detail_rows[key] = right
        coverage, cov_layout = _card("ⓘ  Coverage")
        coverage_row = QHBoxLayout()
        self.detail_coverage = QLabel("Global — check provider availability for your area.")
        self.detail_coverage.setObjectName("muted")
        self.detail_coverage.setWordWrap(True)
        coverage_row.addWidget(self.detail_coverage, 1)
        coverage_map = QLabel()
        coverage_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "previews", "coverage_world.png")
        coverage_pixmap = QPixmap(coverage_path)
        if not coverage_pixmap.isNull():
            coverage_map.setPixmap(coverage_pixmap.scaled(92, 46, _KEEP_ASPECT, _SMOOTH))
        coverage_map.setAlignment(_ALIGN_CENTER)
        coverage_map.setObjectName("coverageMap")
        coverage_row.addWidget(coverage_map, 0, _ALIGN_RIGHT)
        cov_layout.addLayout(coverage_row)
        detail_layout.addWidget(coverage)
        detail_layout.addStretch(1)
        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setFrameShape(_FRAME_NO_FRAME)
        detail_scroll.setWidget(detail)
        body.addWidget(detail_scroll, 1)
        layout.addLayout(body, 1)
        self.selection_tags = QLabel("Selected datasets:  none")
        self.selection_tags.setObjectName("muted")
        layout.addWidget(self.selection_tags)
        self.dataset_tree.currentItemChanged.connect(self._show_dataset_details)
        self.free_only.toggled.connect(self._filter_datasets)
        return page

    def _build_options_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        self.options_summary = QLabel("Options will be based on the datasets selected in Step 2.")
        self.options_summary.setObjectName("muted")
        self.options_summary.setWordWrap(True)
        layout.addWidget(self.options_summary)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(_FRAME_NO_FRAME)
        self.options_content = QWidget()
        self.options_layout = QVBoxLayout(self.options_content)
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        self.options_layout.setSpacing(6)
        scroll.setWidget(self.options_content)
        layout.addWidget(scroll, 1)
        self.option_controls = {}
        return page

    def _add_option_field(self, layout, label, widget):
        row = QHBoxLayout()
        title = QLabel(label)
        title.setObjectName("summaryKey")
        title.setMinimumWidth(115)
        row.addWidget(title)
        row.addWidget(widget, 1)
        layout.addLayout(row)

    def _refresh_dataset_options(self):
        if not hasattr(self, "options_layout"):
            return
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.option_controls.clear()
        datasets = self._selected_datasets()
        if not datasets:
            self.options_summary.setText("No datasets are selected. Return to Dataset Selection and choose one or more datasets.")
            empty, empty_layout = _card("No dataset options yet")
            empty_layout.addWidget(QLabel("Selected datasets and their matching controls will appear here."))
            self.options_layout.addWidget(empty)
            self.options_layout.addStretch(1)
            return

        self.options_summary.setText(f"Options below match the {len(datasets)} dataset(s) selected in Step 2.")
        selected_card, selected_layout = _card(f"Selected datasets ({len(datasets)})")
        for data in datasets:
            title = QLabel(data["title"])
            title.setObjectName("detailTitle")
            selected_layout.addWidget(title)
            selected_layout.addWidget(QLabel(f"{data['group']}  ·  {data['provider']}"))
            metadata = data.get("formula") or data.get("bands") or data.get("description", "")
            detail = QLabel(metadata)
            detail.setObjectName("muted")
            detail.setWordWrap(True)
            selected_layout.addWidget(detail)
        self.options_layout.addWidget(selected_card)

        optical = [data for data in datasets if data["group"] in ("Imagery", "Indices")]
        if optical:
            card, card_layout = _card("Optical imagery and index processing")
            dates = QHBoxLayout()
            self.image_start = QDateEdit()
            self.image_start.setCalendarPopup(True)
            self.image_start.setDate(QDate(2020, 1, 1))
            self.image_end = QDateEdit()
            self.image_end.setCalendarPopup(True)
            self.image_end.setDate(QDate(2020, 12, 31))
            dates.addWidget(self.image_start)
            dates.addWidget(QLabel("to"))
            dates.addWidget(self.image_end)
            date_holder = QWidget()
            date_holder.setLayout(dates)
            self._add_option_field(card_layout, "Date range", date_holder)
            self.cloud_cover = QSpinBox()
            self.cloud_cover.setRange(0, 100)
            self.cloud_cover.setValue(20)
            self.cloud_cover.setSuffix(" %")
            self._add_option_field(card_layout, "Maximum cloud cover", self.cloud_cover)
            self.cloud_mask = QCheckBox("Mask clouds and cirrus using quality bands")
            self.cloud_mask.setChecked(True)
            card_layout.addWidget(self.cloud_mask)
            composite = QLabel("Median composite for selected observations")
            composite.setObjectName("muted")
            self._add_option_field(card_layout, "Composite", composite)
            self.option_controls["optical"] = {
                "datasets": [data["title"] for data in optical],
                "start": self.image_start, "end": self.image_end,
                "cloud_cover": self.cloud_cover, "cloud_mask": self.cloud_mask,
            }
            self.options_layout.addWidget(card)

        index_datasets = [data for data in datasets if data["group"] == "Indices"]
        if index_datasets:
            card, card_layout = _card("Index source sensors")
            landsat_indices = QCheckBox("Landsat Collection 2")
            landsat_indices.setChecked(True)
            sentinel_indices = QCheckBox("Sentinel-2 SR Harmonized")
            sentinel_indices.setChecked(False)
            card_layout.addWidget(landsat_indices)
            card_layout.addWidget(sentinel_indices)
            note = QLabel("Choose either or both sources for NDVI, NDBI, DBSI, UI, and NDWI. LST is Landsat-only and will not be generated from Sentinel-2.")
            note.setObjectName("muted")
            note.setWordWrap(True)
            card_layout.addWidget(note)
            self.option_controls["index_sources"] = {
                "datasets": [data["title"] for data in index_datasets],
                "landsat": landsat_indices, "sentinel2": sentinel_indices,
            }
            self.options_layout.addWidget(card)

        for data in datasets:
            if data["title"].startswith("Population (WorldPop"):
                card, card_layout = _card("WorldPop population count")
                year = _combo([str(y) for y in range(2015, 2031)])
                year.setCurrentText("2024")
                self._add_option_field(card_layout, "Population year", year)
                band = QLabel("Population count (people per cell)")
                band.setObjectName("muted")
                self._add_option_field(card_layout, "Output band", band)
                self.option_controls[data["title"]] = {"year": year}
                self.options_layout.addWidget(card)
            elif data["title"].startswith("Building Height (Open Buildings 2.5D"):
                card, card_layout = _card("Open Buildings 2.5D Temporal")
                year = _combo([str(y) for y in range(2016, 2024)])
                year.setCurrentText("2023")
                self._add_option_field(card_layout, "Building year", year)
                band = _combo(["building_height", "building_presence", "building_fractional_count"])
                self._add_option_field(card_layout, "Output band", band)
                self.option_controls[data["title"]] = {"year": year, "band": band}
                self.options_layout.addWidget(card)

        vectors = [data for data in datasets if data["group"] == "Vector"]
        if vectors:
            card, card_layout = _card(f"Vector export options ({len(vectors)} source(s))")
            card_layout.addWidget(QLabel("Selected vector sources: " + ", ".join(data["title"] for data in vectors)))
            self.include_attributes = QCheckBox("Include available source attributes")
            self.include_attributes.setChecked(True)
            self.simplify_geometry = QCheckBox("Simplify polygon geometry")
            card_layout.addWidget(self.include_attributes)
            card_layout.addWidget(self.simplify_geometry)
            self.option_controls["vector"] = {
                "datasets": [data["title"] for data in vectors],
                "include_attributes": self.include_attributes,
                "simplify_geometry": self.simplify_geometry,
            }
            self.options_layout.addWidget(card)

        for data in vectors:
            if not data["title"].startswith("Microsoft Buildings"):
                continue
            card, card_layout = _card("Microsoft Buildings location")
            country = QComboBox()
            country.addItem("Select a country…", "")
            for country_name in self._microsoft_country_names():
                country.addItem(country_name, country_name)
            self._add_option_field(card_layout, "Country", country)

            state = QComboBox()
            state.addItem("Select a U.S. state…", "")
            for state_code, state_name in US_STATES:
                state.addItem(f"{state_code} — {state_name}", state_code)
            state_row = QWidget()
            state_row_layout = QHBoxLayout(state_row)
            state_row_layout.setContentsMargins(0, 0, 0, 0)
            state_row_layout.addWidget(_field_label("U.S. state"))
            state_row_layout.addWidget(state, 1)
            state_row.setVisible(False)
            card_layout.addWidget(state_row)
            country.currentIndexChanged.connect(
                lambda _index, country_combo=country, row=state_row:
                    row.setVisible(country_combo.currentData() == "United States")
            )
            note = QLabel(
                "Choose a country for its Microsoft Buildings collection. For United States, "
                "choose a state to use the matching ORNL USA Structures asset. The selected "
                "collection is filtered to the area of interest and exported as a Google Drive task."
            )
            note.setObjectName("muted")
            note.setWordWrap(True)
            card_layout.addWidget(note)
            self.option_controls[data["title"]] = {"country": country, "state": state}
            self.options_layout.addWidget(card)

        tile_sources = {
            "OpenBuildingMap (by GFZ)": (
                "OpenBuildingMap tile IDs (level-6 Quadkeys)",
                "Enter one or more six-digit Quadkeys, one per line (commas and semicolons also work). Each ID creates its own Google Drive export task. Find tiles at openbuildingmap.org/download/.",
                "300110\n300111",
            ),
            "Global Building Atlas Polygons": (
                "Global Building Atlas tile IDs (5° grid)",
                "Enter one or more 5-degree grid tile IDs, one per line (commas and semicolons also work). Each ID creates its own Google Drive export task. Nairobi example: e035_n00_e040_s05. Find tiles in the GBA tile finder.",
                "e035_n00_e040_s05\ne040_n00_e045_s05",
            ),
        }
        for data in vectors:
            config = tile_sources.get(data["title"])
            if not config:
                continue
            label, help_text, example = config
            card, card_layout = _card(data["title"] + " grid tiles")
            tile_ids = QPlainTextEdit()
            tile_ids.setPlaceholderText(example)
            tile_ids.setFixedHeight(62)
            self._add_option_field(card_layout, "Tile IDs", tile_ids)
            hint = QLabel(help_text)
            hint.setObjectName("muted")
            hint.setWordWrap(True)
            card_layout.addWidget(hint)
            self.option_controls[data["title"]] = {"tile_ids": tile_ids}
            self.options_layout.addWidget(card)

        self.options_layout.addStretch(1)

    @staticmethod
    def _microsoft_country_names():
        """Build an English country/territory list from Qt's bundled locale data."""
        language_enum = getattr(QLocale, "Language", QLocale)
        script_enum = getattr(QLocale, "Script", QLocale)
        territory_enum = getattr(QLocale, "Territory", getattr(QLocale, "Country", QLocale))
        any_language = getattr(language_enum, "AnyLanguage", getattr(QLocale, "AnyLanguage", None))
        any_script = getattr(script_enum, "AnyScript", getattr(QLocale, "AnyScript", None))
        any_territory = getattr(
            territory_enum, "AnyTerritory",
            getattr(territory_enum, "AnyCountry", getattr(QLocale, "AnyCountry", None)),
        )
        country_to_string = getattr(QLocale, "territoryToString", None) or getattr(QLocale, "countryToString")
        names = set()
        try:
            locales = QLocale.matchingLocales(any_language, any_script, any_territory)
        except Exception:
            locales = []
        for locale in locales:
            get_territory = getattr(locale, "territory", None) or getattr(locale, "country", None)
            if get_territory is None:
                continue
            territory = get_territory()
            try:
                if int(territory) == 0:
                    continue
            except (TypeError, ValueError):
                pass
            name = str(country_to_string(territory)).strip()
            if name and name.lower() not in {"any country", "any territory", "default"}:
                names.add(name)
        return sorted(names, key=str.casefold)

    def _build_output_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        warning = QLabel("⚠  Large areas and high resolution may result in long download times and high data usage. Ensure a stable internet connection and enough disk space.")
        warning.setObjectName("warningBanner")
        warning.setWordWrap(True)
        layout.addWidget(warning)

        top = QHBoxLayout()
        location, location_layout = _card("▰  Output Location")
        destination_row = QHBoxLayout()
        destination_row.addWidget(_field_label("Save to"))
        self.output_destination = _combo(["Local computer", "Google Drive"])
        self.output_destination.currentTextChanged.connect(self._output_destination_changed)
        destination_row.addWidget(self.output_destination, 1)
        location_layout.addLayout(destination_row)
        self.output_destination_stack = QStackedWidget()
        local_destination = QWidget()
        local_layout = QVBoxLayout(local_destination)
        local_layout.setContentsMargins(0, 0, 0, 0)
        self.local_folder_row = QWidget()
        local_folder_layout = QVBoxLayout(self.local_folder_row)
        local_folder_layout.setContentsMargins(0, 0, 0, 0)
        local_folder_layout.addWidget(_field_label("Local folder"))
        path_row = QHBoxLayout()
        path_row.setContentsMargins(0, 2, 0, 2)
        path_row.setSpacing(6)
        self.output_path = QLineEdit(r"D:\14_Data_Analytics\QGIS_Plugin\Earth_Downloader\Output")
        path_row.addWidget(self.output_path, 1)
        browse = QPushButton("📁")
        browse.setObjectName("secondaryButton")
        browse.clicked.connect(self._browse_output)
        path_row.addWidget(browse)
        local_folder_layout.addLayout(path_row)
        worker_row = QHBoxLayout()
        worker_row.addWidget(_field_label("Parallel download workers"))
        self.download_workers = QSpinBox()
        self.download_workers.setRange(1, 4)
        self.download_workers.setValue(2)
        self.download_workers.setToolTip(
            "Runs up to this many local dataset downloads at once. Higher values "
            "may use more memory or hit Earth Engine request limits; 1 is safest."
        )
        worker_row.addWidget(self.download_workers)
        worker_row.addStretch(1)
        local_layout.addLayout(worker_row)
        drive_destination = QWidget()
        drive_layout = QVBoxLayout(drive_destination)
        drive_layout.setContentsMargins(0, 0, 0, 0)
        drive_note = QLabel("Earth Engine exports are created in Google Drive; authenticate and initialize Earth Engine first.")
        drive_note.setObjectName("muted")
        drive_note.setWordWrap(True)
        drive_layout.addWidget(drive_note)
        self.output_destination_stack.addWidget(local_destination)
        self.output_destination_stack.addWidget(drive_destination)
        location_layout.addWidget(self.output_destination_stack)
        location_layout.addWidget(self.local_folder_row)
        self.drive_folder_row = QWidget()
        drive_folder_layout = QHBoxLayout(self.drive_folder_row)
        drive_folder_layout.setContentsMargins(0, 0, 0, 0)
        drive_folder_layout.addWidget(_field_label("Google Drive folder"))
        self.drive_folder = QLineEdit("GeoToolkit_Exports")
        self.drive_folder.setPlaceholderText("Folder name in your Google Drive")
        drive_folder_layout.addWidget(self.drive_folder, 1)
        location_layout.addWidget(self.drive_folder_row)
        self.vector_destination_note = QLabel()
        self.vector_destination_note.setObjectName("muted")
        self.vector_destination_note.setWordWrap(True)
        location_layout.addWidget(self.vector_destination_note)
        form = QGridLayout()
        form.setContentsMargins(4, 3, 4, 3)
        form.setHorizontalSpacing(5)
        form.setVerticalSpacing(3)
        form.addWidget(_field_label("Organize by"), 0, 0)
        form.addWidget(_combo(["Dataset", "Date", "Flat folder"]), 0, 1)
        form.addWidget(_field_label("File naming"), 0, 2)
        form.addWidget(_combo(["{dataset}_{date}.tif", "{dataset}_{aoi}_{date}.tif"]), 0, 3)
        self.subfolders = QCheckBox("Create subfolders for each dataset")
        self.subfolders.setChecked(True)
        form.addWidget(self.subfolders, 1, 0, 1, 4)
        location_layout.addLayout(form)
        top.addWidget(location, 3)

        output_format, format_layout = _card("⚙  Format and projection")
        self.output_controls = {}
        for label, options in (
            ("Output format", ["GeoTIFF (recommended)", "Cloud Optimized GeoTIFF"]),
            ("Compression", ["LZW", "DEFLATE", "None"]),
            ("CRS", ["EPSG:4326 (WGS 84)", "Use layer CRS", "EPSG:3857 (Web Mercator)"]),
            ("Resampling", ["Nearest neighbour", "Bilinear", "Cubic"]),
        ):
            line = QHBoxLayout()
            line.addWidget(QLabel(label))
            line.addStretch(1)
            control = _combo(options)
            self.output_controls[label] = control
            line.addWidget(control)
            format_layout.addLayout(line)
        crs_note = QLabel("Raster exports use the selected CRS. KML vectors use WGS 84, as required by the KML format.")
        crs_note.setObjectName("muted")
        crs_note.setWordWrap(True)
        format_layout.addWidget(crs_note)
        top.addWidget(output_format, 2)
        layout.addLayout(top)

        overview, overview_layout = _card("▦  Request Overview")
        self.request_table = QTableWidget(0, 4)
        self.request_table.setHorizontalHeaderLabels(["Dataset", "Resolution", "Estimated pixels", "Estimated size"])
        self.request_table.horizontalHeader().setStretchLastSection(True)
        self.request_table.setAlternatingRowColors(True)
        self.request_table.setMinimumHeight(185)
        overview_layout.addWidget(self.request_table)
        progress_row = QHBoxLayout()
        self.estimate_bar = QProgressBar()
        self.estimate_bar.setRange(0, 100)
        self.estimate_bar.setValue(0)
        self.estimate_bar.setTextVisible(False)
        progress_row.addWidget(self.estimate_bar, 1)
        self.total_size_label = QLabel("Estimated size: pending AOI and datasets")
        self.total_size_label.setObjectName("muted")
        progress_row.addWidget(self.total_size_label)
        overview_layout.addLayout(progress_row)
        layout.addWidget(overview, 1)

        run_row = QHBoxLayout()
        run_row.setContentsMargins(20, 10, 20, 10)
        run_row.setSpacing(20)
        run_row.addStretch(1)
        self.start_download = QPushButton("▶  Start Download")
        self.start_download.setObjectName("primaryButton")
        self.start_download.clicked.connect(self._start_download)
        run_row.addWidget(self.start_download)
        layout.addLayout(run_row)
        return page

    def _build_results_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(8, 8, 8, 8)
        tabs = QTabWidget()
        current_tab = QWidget()
        current_layout = QVBoxLayout(current_tab)
        current_layout.setContentsMargins(0, 0, 0, 0)
        banner = QLabel("●  Download jobs will appear here with their output paths and status.")
        banner.setObjectName("successBanner")
        current_layout.addWidget(banner)
        self.results_table = QTableWidget(0, 5)
        self.results_table.setHorizontalHeaderLabels(["Dataset", "Output", "File Path", "Status", "Time Taken"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setMinimumHeight(220)
        current_layout.addWidget(self.results_table, 1)
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        self.history_table = QTableWidget(0, 6)
        self.history_table.setHorizontalHeaderLabels(["Time (UTC)", "Dataset", "Output", "File Path / Details", "Status", "Time Taken"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setAlternatingRowColors(True)
        history_layout.addWidget(self.history_table, 1)
        clear_history = QPushButton("Clear history")
        clear_history.setObjectName("secondaryButton")
        clear_history.clicked.connect(self._clear_history)
        history_layout.addWidget(clear_history)
        tabs.addTab(current_tab, "Current results")
        tabs.addTab(history_tab, "View history")
        self.results_tabs = tabs
        layout.addWidget(tabs, 1)
        actions = QHBoxLayout()
        actions.setContentsMargins(20, 10, 20, 10)
        actions.setSpacing(20)
        actions.addStretch(1)
        self.add_to_project = QPushButton("＋  Add to project")
        self.add_to_project.setObjectName("successButton")
        self.add_to_project.setEnabled(False)
        self.add_to_project.clicked.connect(self._add_downloads_to_project)
        actions.addWidget(self.add_to_project)
        open_folder = QPushButton("▱  Open output folder")
        open_folder.setObjectName("secondaryButton")
        open_folder.clicked.connect(self._open_output_folder)
        actions.addWidget(open_folder)
        new_session = QPushButton("⟳  New session")
        new_session.setObjectName("secondaryButton")
        new_session.setToolTip(
            "Start a fresh download setup: clear current results and dataset checks, "
            "return to Area of Interest, and keep saved download history and authentication."
        )
        new_session.clicked.connect(self._new_session)
        actions.addWidget(new_session)
        layout.addLayout(actions)
        return page

    def _style(self):
        self.setStyleSheet(f"""
            QDialog {{ background: #f5f9fc; color: {INK}; font: 6.5pt 'Segoe UI'; }}
            QWidget#titleBar {{ background: #08649a; min-height: 44px; max-height: 44px; }}
            QLabel#brandMark {{ color: white; font-size: 10pt; font-weight: 700; }}
            QLabel#brandTitle {{ color: white; font-size: 8pt; font-weight: 700; }}
            QLabel#connectionBadge {{ color: white; background: #087fa8; border: 1px solid #3cb4cf; border-radius: 8px; padding: 0 12px; font-size: 8pt; font-weight: 700; }}
            QLabel#connectionBadge[connectionState="connected"] {{ background: #187644; border-color: #54c98a; }}
            QPushButton#connectionButton {{ min-height: 0px; max-height: 34px; padding: 0 12px; border-radius: 8px; color: white; background: #087fa8; border: 1px solid #3cb4cf; font-size: 8pt; font-weight: 700; }}
            QPushButton#connectionButton:hover {{ background: #0b94bc; }}
            QWidget#sidebar {{ background: #edf5fa; border-right: 1px solid {LINE}; }}
            QWidget#pages {{ background: #f7fafc; }}
            QWidget#footer {{ background: #eaf3f9; border-top: 1px solid {LINE}; }}
            QFrame#card {{ background: #ffffff; border: 1px solid {LINE}; border-radius: 6px; }}
            QLabel#cardHeading {{ color: {INK}; font-size: 9pt; font-weight: 700; }}
            QLabel#detailTitle {{ color: #153d60; font-size: 10pt; font-weight: 700; }}
            QLabel#datasetPreview {{ background: #f2f7fa; border: 1px solid {LINE}; border-radius: 5px; padding: 2px; }}
            QLabel#fieldLabel {{ color: #176da4; font-size: 7pt; font-weight: 600; }}
            QLabel#summaryKey {{ color: #325575; }}
            QLabel#summaryValue {{ color: #173a5b; font-weight: 600; }}
            QLabel#muted {{ color: {MUTED}; font-size: 7pt; }}
            QLabel#infoBanner {{ color: #0b65a2; background: #edf8ff; border: 1px solid #b9dff6; border-radius: 4px; padding: 5px; }}
            QLabel#warningBanner {{ color: #614600; background: #fff8e0; border: 1px solid #f3d36d; border-radius: 4px; padding: 4px; }}
            QLabel#successBanner {{ color: #167440; background: #ebf9f0; border: 1px solid #b9e8c8; border-radius: 4px; padding: 7px; }}
            QPushButton {{ min-height: 17px; padding: 1px 5px; border: 1px solid {LINE}; border-radius: 3px; background: white; color: {INK}; }}
            QPushButton:hover {{ border-color: {BLUE}; background: #f0f8fd; }}
            QPushButton#stepButton {{ text-align: left; border: 0; background: transparent; color: #536f89; padding: 4px 1px; }}
            QPushButton#stepButton:checked {{ background: transparent; color: #056eaa; font-weight: 700; }}
            QLabel#stepMarker {{ min-width: 18px; max-width: 18px; min-height: 18px; max-height: 18px; margin: 0; padding: 0; border: 0; background: transparent; color: #69839b; font-size: 7pt; font-weight: 700; }}
            QPushButton#primaryButton {{ background: {BLUE}; color: white; border: 1px solid {BLUE}; font-weight: 700; padding: 3px 11px; }}
            QPushButton#primaryButton:hover {{ background: #0677b4; }}
            QPushButton#secondaryButton {{ background: white; color: #126da5; }}
            QPushButton#successButton {{ background: #2ea955; color: white; border-color: #2ea955; font-weight: 700; }}
            QLineEdit, QComboBox, QDateEdit, QSpinBox {{ min-height: 17px; border: 1px solid #cbddea; border-radius: 3px; padding: 1px 3px; background: white; selection-background-color: {BLUE}; }}
            QTreeWidget, QTableWidget {{ background: white; border: 1px solid {LINE}; border-radius: 5px; alternate-background-color: #f3f8fc; gridline-color: #dfebf3; }}
            QTreeWidget::item {{ padding: 2px 1px; }}
            QTreeWidget::item:selected {{ background: #dff1fb; color: #124b74; }}
            QHeaderView::section {{ background: #edf5fa; color: #245474; border: 0; border-bottom: 1px solid {LINE}; padding: 3px; font-weight: 700; }}
            QProgressBar {{ border: 0; border-radius: 4px; background: #e4eef5; min-height: 9px; max-height: 9px; }}
            QProgressBar::chunk {{ background: #44b26b; border-radius: 4px; }}
            QCheckBox, QRadioButton {{ spacing: 6px; color: #294c6d; }}
        """)

    def _refresh_layers(self, *_):
        previous_id = self.layer_combo.currentData()
        self.layer_combo.blockSignals(True)
        self.layer_combo.clear()
        self.layer_combo.addItem("Select a polygon layer…", None)
        project = QgsProject.instance()
        for layer in project.mapLayers().values():
            if (isinstance(layer, QgsVectorLayer) and layer.isValid()
                    and layer.geometryType() == POLYGON_GEOM):
                self.layer_combo.addItem(layer.name(), layer.id())
                if layer.id() not in self._connected_selection_layers:
                    layer.selectionChanged.connect(self._update_aoi_summary)
                    self._connected_selection_layers.add(layer.id())
        index = self.layer_combo.findData(previous_id) if previous_id else -1
        # When opening on an existing QGIS project, default to its first valid
        # polygon layer so the user can use the AOI immediately.
        fallback_index = 1 if self.layer_combo.count() > 1 else 0
        self.layer_combo.setCurrentIndex(index if index >= 0 else fallback_index)
        self.layer_combo.blockSignals(False)
        self._update_aoi_summary()

    def _browse_aoi_layer(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import polygon layer", "",
            "Vector datasets (*.gpkg *.shp *.geojson *.json *.kml *.gml);;All files (*)",
        )
        if not path:
            return
        layer = QgsVectorLayer(path, os.path.splitext(os.path.basename(path))[0], "ogr")
        if not layer.isValid():
            QMessageBox.warning(self, "Unable to open layer", "QGIS could not open the selected file as a vector layer.")
            return
        if layer.geometryType() != POLYGON_GEOM:
            QMessageBox.warning(self, "Polygon layer required", "Choose a polygon vector layer for the area of interest.")
            return
        QgsProject.instance().addMapLayer(layer)
        index = self.layer_combo.findData(layer.id())
        if index >= 0:
            self.layer_combo.setCurrentIndex(index)

    def _selected_layer(self):
        layer_id = self.layer_combo.currentData()
        return QgsProject.instance().mapLayer(layer_id) if layer_id else None

    def _layer_type_changed(self, index):
        self.layer_combo.setEnabled(index == 0)
        self.browse_layer_button.setEnabled(index == 0)
        self.selected_only.setEnabled(index == 0)
        self._update_aoi_summary()

    @staticmethod
    def _area_km2(geometry, crs):
        if geometry is None or geometry.isNull() or geometry.isEmpty():
            return None
        project = QgsProject.instance()
        measure = QgsDistanceArea()
        measure.setSourceCrs(crs, project.transformContext())
        ellipsoid = project.ellipsoid()
        measure.setEllipsoid(ellipsoid if ellipsoid else "WGS84")
        square_metres = measure.measureArea(geometry)
        units_group = getattr(QgsUnitTypes, "AreaUnit", None)
        square_meters = getattr(units_group, "SquareMeters", None) if units_group else None
        if square_meters is None:
            square_meters = getattr(QgsUnitTypes, "AreaSquareMeters", None)
        if square_meters is None:
            square_meters = Qgis.AreaUnit.SquareMeters
        square_metres = measure.convertAreaMeasurement(square_metres, square_meters)
        return square_metres / 1_000_000

    def _update_aoi_summary(self, *_):
        if self.layer_type.currentIndex() == 1:
            canvas = self.iface.mapCanvas() if self.iface else None
            extent = canvas.extent() if canvas else None
            self.summary_values["Source"].setText("Current map extent")
            self.summary_values["Features"].setText("—")
            crs = canvas.mapSettings().destinationCrs() if canvas else None
            try:
                area = self._area_km2(QgsGeometry.fromRect(extent), crs) if extent and crs else None
                area_text = f"{area:,.2f} km²" if area is not None else "—"
            except Exception:
                area_text = "—"
            self.summary_values["Area"].setText(area_text)
            self.summary_values["CRS"].setText(crs.authid() if crs else "—")
            return
        layer = self._selected_layer()
        if not layer:
            self.summary_values["Source"].setText("Polygon layer")
            self.summary_values["Features"].setText("Select a polygon layer")
            self.summary_values["Area"].setText("—")
            self.summary_values["CRS"].setText("—")
            return
        use_selection = self.selected_only.isChecked()
        selected = layer.selectedFeatureCount() if use_selection else layer.featureCount()
        count_text = f"{selected:,} selected features" if use_selection else f"{selected:,} features"
        try:
            if use_selection and selected == 0:
                area_text = "—"
            else:
                request_features = layer.selectedFeatures() if use_selection else layer.getFeatures()
                geometries = [feature.geometry() for feature in request_features
                              if feature.hasGeometry() and not feature.geometry().isEmpty()]
                if not self.exact_geometry.isChecked() and geometries:
                    bounds = geometries[0].boundingBox()
                    for geometry in geometries[1:]:
                        bounds.combineExtentWith(geometry.boundingBox())
                    geometry = QgsGeometry.fromRect(bounds)
                elif len(geometries) > 1:
                    geometry = QgsGeometry.unaryUnion(geometries)
                else:
                    geometry = geometries[0] if geometries else None
                area = self._area_km2(geometry, layer.crs())
                area_text = f"{area:,.2f} km²" if area is not None else "—"
        except Exception:
            area_text = "—"
        self.summary_values["Source"].setText(layer.name())
        self.summary_values["Features"].setText(count_text)
        self.summary_values["Area"].setText(area_text)
        self.summary_values["CRS"].setText(layer.crs().authid())

    def _dataset_tree_changed(self, *_):
        self._update_selected_tags()
        self._update_request_table()
        self._update_vector_output_note()

    def _selected_datasets(self):
        selected = []
        for title, item in self.dataset_items.items():
            if item.checkState(0) == _CHECKED:
                selected.append(item.data(0, _USER_ROLE))
        return selected

    def _update_selected_tags(self):
        names = [item["title"] for item in self._selected_datasets()]
        if names:
            self.selection_tags.setText("Selected datasets:   " + "   ·   ".join(names))
        else:
            self.selection_tags.setText("Selected datasets:  none")

    def _show_dataset_details(self, item, _previous=None):
        if item is None:
            return
        data = item.data(0, _USER_ROLE)
        if not data:
            return
        self.detail_title.setText(data["title"])
        self.detail_provider.setText(data["provider"])
        values = {
            "Description": data.get("description", "—"),
            "Temporal coverage": data.get("temporal", "—"),
            "Spatial resolution": data.get("resolution", "—"),
            "Bands": data.get("bands", "—"),
            "License": data.get("license", "—"),
            "Credit / attribution": data.get("credit", "—"),
            "Collection / source": data.get("collection", "—"),
            "Composite / formula": data.get("formula", "—"),
        }
        for key, value in values.items():
            self.detail_rows[key].setText(value)
        self.detail_coverage.setText(data.get("coverage", "Global — check provider availability for your area."))

        preview_name = data.get("preview")
        if preview_name:
            preview_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "assets", "previews", preview_name,
            )
            preview = QPixmap(preview_path)
            if not preview.isNull():
                preview = preview.scaled(42, 38, _KEEP_ASPECT, _SMOOTH)
                self.detail_preview.setPixmap(preview)
                self.detail_preview.setToolTip("Reference thumbnail from the supplied dataset overview.")
                self.detail_preview.show()
            else:
                self.detail_preview.clear()
                self.detail_preview.show()
        else:
            self.detail_preview.clear()
            self.detail_preview.hide()

    def _filter_datasets(self, text=""):
        needle = text.strip().lower() if isinstance(text, str) else self.dataset_search.text().strip().lower()
        free_only = self.free_only.isChecked()
        for title, item in self.dataset_items.items():
            data = item.data(0, _USER_ROLE)
            searchable = (title + " " + data["group"] + " " + data["provider"]).lower()
            matches_search = not needle or needle in searchable
            license_text = data["license"].lower()
            known_open = any(term in license_text for term in ("public domain", "cc by", "odbl", "open data", "open license"))
            item.setHidden(not matches_search or (free_only and not known_open))
        for index in range(self.dataset_tree.topLevelItemCount()):
            parent = self.dataset_tree.topLevelItem(index)
            parent.setHidden(all(parent.child(i).isHidden() for i in range(parent.childCount())))

    def _update_request_table(self):
        if not hasattr(self, "request_table"):
            return
        datasets = self._selected_datasets()
        self.request_table.setRowCount(len(datasets))
        total = 0
        for row, dataset in enumerate(datasets):
            resolution = dataset["resolution"]
            pixels, size = "Set AOI to estimate", "—"
            self.request_table.setItem(row, 0, QTableWidgetItem(dataset["title"]))
            self.request_table.setItem(row, 1, QTableWidgetItem(resolution))
            self.request_table.setItem(row, 2, QTableWidgetItem(pixels))
            self.request_table.setItem(row, 3, QTableWidgetItem(size))
        self.total_size_label.setText("Estimated size: requires an AOI and Earth Engine metadata")

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_path.text())
        if folder:
            self.output_path.setText(folder)

    def _output_destination_changed(self, destination):
        self.output_destination_stack.setCurrentIndex(1 if destination == "Google Drive" else 0)
        self._update_vector_output_note()

    def _update_vector_output_note(self):
        """Explain where raster and vector outputs go for the current selection."""
        selected = [item["title"] for item in self._selected_datasets()]
        vector_exports = any(
            title.startswith((
                "Open Buildings Polygon V3",
                "Global Building Atlas Polygons",
                "OpenBuildingMap",
                "Microsoft Buildings",
            ))
            for title in selected
        )
        use_drive = self.output_destination.currentText() == "Google Drive" or vector_exports
        self.drive_folder_row.setVisible(use_drive)
        self.local_folder_row.setVisible(self.output_destination.currentText() == "Local computer")

        notes = []
        if vector_exports:
            notes.append(
                "Selected vector datasets are submitted as Earth Engine table export tasks to Google Drive "
                "(KML). This applies even when rasters are saved locally. Track progress in Results or the "
                "Earth Engine Tasks tab."
            )
        if any(title.startswith("OpenBuildingMap") for title in selected):
            notes.append(
                "OpenBuildingMap tile IDs are mapped to the sat-io Earth Engine assets and exported as tasks."
            )
        self.vector_destination_note.setText(" ".join(notes))
        self.vector_destination_note.setVisible(bool(notes))

    def _connect_earth_engine(self):
        settings = QSettings()
        saved_project = settings.value("GeoToolkit/GEE/cloudProjectId", "", type=str)
        project_id, accepted = QInputDialog.getText(
            self,
            "Connect to Google Earth Engine",
            "Google Cloud Project ID (registered for Earth Engine):",
            text=saved_project,
        )
        if not accepted:
            return
        project_id = project_id.strip()
        if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", project_id):
            QMessageBox.warning(
                self,
                "Invalid project ID",
                "Enter a valid Google Cloud Project ID (6–30 lowercase letters, numbers, or hyphens; "
                "it must start with a letter and end with a letter or number).",
            )
            return
        self._start_ee_connection(project_id, authenticate=True, notify_on_result=True)

    def _start_ee_connection(self, project_id: str, authenticate: bool, notify_on_result: bool):
        if self._ee_thread is not None and self._ee_thread.isRunning():
            return
        self._ee_pending_project = project_id
        self._ee_notify_on_result = notify_on_result
        self.connection_badge.setText("◌  Connecting…")
        self.connection_button.setEnabled(False)
        thread = QThread()
        worker = EarthEngineConnectionWorker(project_id, authenticate)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.completed.connect(self._on_ee_connection_complete)
        worker.completed.connect(thread.quit)
        worker.completed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        active = (thread, worker)
        _ACTIVE_EE_THREADS.append(active)
        thread.finished.connect(lambda active=active: _release_ee_thread(active))
        self._ee_thread = thread
        self._ee_worker = worker
        thread.start()

    def _on_ee_connection_complete(self, connected: bool, message: str):
        self.connection_button.setEnabled(True)
        self._ee_thread = None
        self._ee_worker = None
        if connected:
            QSettings().setValue("GeoToolkit/GEE/cloudProjectId", self._ee_pending_project)
            self.connection_badge.setText("●  Connected")
            self.connection_badge.setProperty("connectionState", "connected")
            self.connection_badge.style().unpolish(self.connection_badge)
            self.connection_badge.style().polish(self.connection_badge)
            self.connection_badge.setToolTip(f"Earth Engine initialized with project {self._ee_pending_project}")
        else:
            self.connection_badge.setText("●  Not connected")
            self.connection_badge.setProperty("connectionState", "disconnected")
            self.connection_badge.style().unpolish(self.connection_badge)
            self.connection_badge.style().polish(self.connection_badge)
            self.connection_badge.setToolTip("")
            if self._ee_notify_on_result:
                QMessageBox.warning(self, "Earth Engine connection failed", message)

    def _aoi_geojson(self):
        project = QgsProject.instance()
        target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        if self.layer_type.currentIndex() == 1:
            canvas = self.iface.mapCanvas() if self.iface else None
            if canvas is None:
                raise ValueError("The QGIS map canvas is unavailable.")
            geometry = QgsGeometry.fromRect(canvas.extent())
            source_crs = canvas.mapSettings().destinationCrs()
        else:
            layer = self._selected_layer()
            if layer is None:
                raise ValueError("Choose a polygon layer for the area of interest.")
            features = layer.selectedFeatures() if self.selected_only.isChecked() else layer.getFeatures()
            geometries = [f.geometry() for f in features if f.hasGeometry() and not f.geometry().isEmpty()]
            if not geometries:
                raise ValueError("The selected polygon layer has no usable features. Check the selected-features option.")
            if self.bounding_box.isChecked():
                bounds = geometries[0].boundingBox()
                for geom in geometries[1:]:
                    bounds.combineExtentWith(geom.boundingBox())
                geometry = QgsGeometry.fromRect(bounds)
            else:
                geometry = QgsGeometry.unaryUnion(geometries) if len(geometries) > 1 else geometries[0]
            source_crs = layer.crs()
        if source_crs != target_crs:
            geometry.transform(QgsCoordinateTransform(source_crs, target_crs, project))
        if geometry.isEmpty() or not geometry.isGeosValid():
            raise ValueError("The selected area is empty or invalid. Repair the polygon and try again.")
        return geometry.asJson(7)

    def _download_jobs(self):
        selected = self._selected_datasets()
        if not selected:
            raise ValueError("Select at least one dataset before starting the download.")
        if self.connection_badge.property("connectionState") != "connected":
            raise ValueError("Earth Engine is not connected. Use Authenticate and Initialize, then try again.")
        dates = self.option_controls.get("optical", {})
        start = dates.get("start").date().toString("yyyy-MM-dd") if dates else "2020-01-01"
        end_date = dates.get("end").date().addDays(1).toString("yyyy-MM-dd") if dates else "2021-01-01"
        cloud = dates.get("cloud_cover").value() if dates else 20
        cloud_mask = dates.get("cloud_mask").isChecked() if dates else True
        crs_choice = self.output_controls["CRS"].currentText()
        if crs_choice.startswith("EPSG:3857"):
            output_crs = "EPSG:3857"
        elif crs_choice == "Use layer CRS":
            if self.layer_type.currentIndex() == 1 and self.iface:
                output_crs = self.iface.mapCanvas().mapSettings().destinationCrs().authid()
            else:
                layer = self._selected_layer()
                output_crs = layer.crs().authid() if layer else "EPSG:4326"
        else:
            output_crs = "EPSG:4326"
        jobs = []
        for data in selected:
            title = data["title"]
            config = self.option_controls.get(title, {})
            base = {"start": start, "end": end_date, "cloud": cloud, "mask": cloud_mask, "crs": output_crs}
            if title.startswith("Population (WorldPop") or title.startswith("Building Height"):
                base["year"] = config["year"].currentText()
            if title.startswith("Building Height"):
                base["band"] = config["band"].currentText()
            if title.startswith("OpenBuildingMap"):
                ids = self._parse_tile_ids(config.get("tile_ids").toPlainText())
                if not ids:
                    raise ValueError("Enter at least one OpenBuildingMap Quadkey in Dataset Options.")
                for tile in ids:
                    if len(tile) != 6 or any(char not in "0123" for char in tile):
                        raise ValueError(f"Invalid OpenBuildingMap Quadkey: {tile}. Use six digits from 0 to 3.")
                    jobs.append({"title": title + " — " + tile, "name": self._safe_filename(title + "_" + tile), "options": base, "tile_ids": [tile]})
                continue
            if title.startswith("Microsoft Buildings"):
                country_control = config.get("country")
                state_control = config.get("state")
                country_name = country_control.currentData() if country_control else ""
                if not country_name:
                    raise ValueError("Choose a country for Microsoft Buildings in Dataset Options.")
                base["ms_country"] = country_name
                job_title = title + " — " + country_name
                if country_name == "United States":
                    state_code = state_control.currentData() if state_control else ""
                    if not state_code:
                        raise ValueError("Choose a U.S. state for the Microsoft Buildings download.")
                    state_name = state_control.currentText().split(" — ", 1)[-1]
                    base["ms_state_code"] = state_code
                    job_title = f"{title} — {state_code} {state_name}"
                jobs.append({"title": job_title, "name": self._safe_filename(job_title), "options": base})
                continue
            if "Global Building Atlas" in title:
                ids = self._parse_tile_ids(config.get("tile_ids").toPlainText())
                if not ids:
                    raise ValueError("Enter at least one Global Building Atlas grid tile ID in Dataset Options.")
                for tile in ids:
                    jobs.append({"title": title + " — " + tile, "name": self._safe_filename(title + "_" + tile), "options": base, "tile_ids": [tile]})
                continue
            if title.startswith("NDVI") or title.startswith("NDBI") or title.startswith("DBSI") or title.startswith("UI") or title.startswith("NDWI"):
                source_cfg = self.option_controls.get("index_sources", {})
                sensors = [name for name, control in (("Landsat", source_cfg.get("landsat")), ("Sentinel-2", source_cfg.get("sentinel2"))) if control and control.isChecked()]
                if not sensors:
                    raise ValueError("Choose Landsat Collection 2, Sentinel-2, or both under Dataset Options.")
                for sensor in sensors:
                    if sensor == "Sentinel-2" and title.startswith("LST"):
                        continue
                    jobs.append({"title": title, "sensor": sensor, "name": self._safe_filename(title + "_" + sensor), "options": base})
            else:
                jobs.append({"title": title, "name": self._safe_filename(title), "options": base})
        return jobs

    @staticmethod
    def _parse_tile_ids(text):
        """Parse multiline or comma/semicolon-separated tile IDs without duplicates."""
        return list(dict.fromkeys(
            tile.strip()
            for tile in re.split(r"[\s,;]+", text or "")
            if tile.strip()
        ))

    @staticmethod
    def _safe_filename(value):
        value = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
        return value[:100] or "EarthEngine_export"

    def _start_download(self):
        try:
            geometry = self._aoi_geojson()
            jobs = self._download_jobs()
            if self._download_thread is not None and self._download_thread.isRunning():
                return
            selected_titles = [item["title"] for item in self._selected_datasets()]
            has_vectors = any(
                title.startswith((
                    "Open Buildings Polygon V3",
                    "Global Building Atlas Polygons",
                    "OpenBuildingMap",
                    "Microsoft Buildings",
                ))
                for title in selected_titles
            )
            needs_local_folder = self.output_destination.currentText() == "Local computer"
            folder = os.path.abspath(os.path.expandvars(self.output_path.text().strip())) if needs_local_folder else ""
            if needs_local_folder:
                if not folder:
                    raise ValueError("Choose a local output folder.")
                os.makedirs(folder, exist_ok=True)
            needs_drive_folder = self.output_destination.currentText() == "Google Drive" or has_vectors
            if needs_drive_folder and not self.drive_folder.text().strip():
                raise ValueError("Enter a Google Drive folder name.")
            self.results_table.setRowCount(len(jobs))
            self._download_rows.clear()
            self._job_started_at.clear()
            self._job_elapsed_seconds.clear()
            self._job_history_ids.clear()
            self._job_history_records.clear()
            self._history_suppressed_ids.clear()
            for row, job in enumerate(jobs):
                self.results_table.setItem(row, 0, QTableWidgetItem(job["title"]))
                is_vector = any(token in job["title"] for token in ("Polygon V3", "Global Building Atlas", "OpenBuildingMap", "Microsoft Buildings"))
                output_label = "KML (WGS 84)" if is_vector else "GeoTIFF"
                self.results_table.setItem(row, 1, QTableWidgetItem(output_label))
                self.results_table.setItem(row, 2, QTableWidgetItem("Preparing…"))
                self.results_table.setItem(row, 3, QTableWidgetItem("Queued"))
                self.results_table.setItem(row, 4, QTableWidgetItem("00:00:00"))
                self._download_rows[row] = row
                job_id = uuid.uuid4().hex
                self._job_history_ids[row] = job_id
                record = {
                    "job_id": job_id,
                    "time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "dataset": job["title"],
                    "output": output_label,
                    "path_or_details": "Preparing…",
                    "status": "Queued",
                    "time_taken": "00:00:00",
                }
                self._job_history_records[row] = record
                self._write_history_record(record)
            self._refresh_history_table()
            saved_project = QSettings().value("GeoToolkit/GEE/cloudProjectId", "", type=str).strip()
            self.start_download.setEnabled(False)
            self.start_download.setText("Starting…")
            self._go_to(4)
            self._download_thread = QThread()
            self._download_worker = EarthEngineDownloadWorker(
                saved_project, jobs, geometry, self.output_destination.currentText(),
                folder, self.drive_folder.text().strip(), self.download_workers.value(),
            )
            self._download_worker.moveToThread(self._download_thread)
            self._download_thread.started.connect(self._download_worker.run)
            self._download_worker.progress.connect(self._on_download_progress)
            self._download_worker.finished.connect(self._download_thread.quit)
            self._download_worker.finished.connect(self._download_worker.deleteLater)
            self._download_thread.finished.connect(self._on_download_finished)
            self._download_thread.finished.connect(self._download_thread.deleteLater)
            self.elapsed_timer.start()
            self._download_thread.start()
        except Exception as exc:
            QMessageBox.warning(self, "Cannot start download", str(exc))

    def _on_download_progress(self, index, title, status, detail):
        if index < 0:
            self._append_history(title, status, detail)
            QMessageBox.warning(self, "Earth Engine download failed", detail)
            return
        row = index if index < self.results_table.rowCount() else None
        if row is None:
            return
        if "— " in title:
            for candidate in range(self.results_table.rowCount()):
                cell = self.results_table.item(candidate, 0)
                if cell and cell.text() == title:
                    row = candidate
                    break
        if row not in self._job_started_at:
            self._job_started_at[row] = time.monotonic()
            record = self._job_history_records.get(row)
            if record:
                record["time_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self.results_table.setItem(row, 2, QTableWidgetItem(detail))
        self.results_table.setItem(row, 3, QTableWidgetItem(status))
        suffix = os.path.splitext(detail)[1].lower()
        output_label = {".tif": "GeoTIFF", ".tiff": "GeoTIFF", ".kmz": "KMZ",
                        ".kml": "KML", ".gpkg": "GeoPackage", ".geojson": "GeoJSON"}.get(suffix)
        if output_label:
            self.results_table.setItem(row, 1, QTableWidgetItem(output_label))

        terminal = status.lower() in ("downloaded", "failed", "completed", "cancelled", "canceled")
        if terminal:
            started = self._job_started_at.get(row)
            elapsed = int(time.monotonic() - started) if started is not None else 0
            self._job_elapsed_seconds[row] = elapsed
            self.results_table.setItem(row, 4, QTableWidgetItem(self._format_duration(elapsed)))

        job_id = self._job_history_ids.get(row)
        record = self._job_history_records.get(row)
        if job_id and record and job_id not in self._history_suppressed_ids:
            record["path_or_details"] = detail
            record["status"] = status
            if output_label:
                record["output"] = output_label
            if terminal:
                record["time_taken"] = self._format_duration(elapsed)
            self._write_history_record(record)
        self._refresh_history_table()

    @staticmethod
    def _format_duration(seconds):
        seconds = max(0, int(seconds))
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _elapsed_for_row(self, row):
        if row in self._job_elapsed_seconds and self.results_table.item(row, 3):
            status = self.results_table.item(row, 3).text().lower()
            if status in ("downloaded", "failed", "completed", "cancelled", "canceled"):
                return self._job_elapsed_seconds[row]
        started = self._job_started_at.get(row)
        return int(time.monotonic() - started) if started is not None else 0

    def _refresh_elapsed_times(self):
        for row, started in self._job_started_at.items():
            elapsed = self._elapsed_for_row(row)
            formatted = self._format_duration(elapsed)
            cell = self.results_table.item(row, 4)
            if cell and cell.text() != formatted:
                cell.setText(formatted)
            job_id = self._job_history_ids.get(row)
            history_row = self._history_row_by_id.get(job_id)
            if history_row is not None and job_id not in self._history_suppressed_ids:
                history_cell = self.history_table.item(history_row, 5)
                if history_cell:
                    history_cell.setText(formatted)

    def _write_history_record(self, record):
        """Insert/update one run row, retaining compatibility with old CSV logs."""
        if record.get("job_id") in self._history_suppressed_ids:
            return
        fields = ["time_utc", "dataset", "output", "path_or_details", "status", "time_taken", "job_id"]
        rows = []
        try:
            if os.path.exists(self.history_path):
                with open(self.history_path, "r", newline="", encoding="utf-8-sig") as source:
                    rows = list(csv.DictReader(source))
            job_id = record.get("job_id", "")
            match = next((i for i, row in enumerate(rows) if job_id and row.get("job_id") == job_id), None)
            normalized = {field: record.get(field, "") for field in fields}
            if match is None:
                rows.append(normalized)
            else:
                rows[match].update(normalized)
            temp_path = self.history_path + ".partial"
            with open(temp_path, "w", newline="", encoding="utf-8-sig") as output:
                writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                for row in rows:
                    writer.writerow({field: row.get(field, "") or "" for field in fields})
            os.replace(temp_path, self.history_path)
        except (OSError, csv.Error) as exc:
            QgsMessageLog.logMessage(f"Could not write download history: {exc}", "GeoToolkit")

    def _append_history(self, title, status, detail):
        suffix = os.path.splitext(str(detail))[1].lower()
        output_label = {".tif": "GeoTIFF", ".tiff": "GeoTIFF", ".kmz": "KMZ",
                        ".kml": "KML", ".gpkg": "GeoPackage", ".geojson": "GeoJSON"}.get(suffix, "Earth Engine")
        self._write_history_record({
            "job_id": uuid.uuid4().hex,
            "time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "dataset": title,
            "output": output_label,
            "path_or_details": detail,
            "status": status,
            "time_taken": "",
        })
        self._refresh_history_table()

    def _refresh_history_table(self):
        if not hasattr(self, "history_table"):
            return
        self.history_table.setRowCount(0)
        if not getattr(self, "history_path", None) or not os.path.exists(self.history_path):
            return
        try:
            with open(self.history_path, "r", newline="", encoding="utf-8-sig") as source:
                rows = list(csv.DictReader(source))
        except (OSError, csv.Error):
            return
        self._history_row_by_id.clear()
        self.history_table.setRowCount(len(rows))
        for row_index, entry in enumerate(rows):
            values = (entry.get("time_utc", ""), entry.get("dataset", ""), entry.get("output", ""),
                      entry.get("path_or_details", ""), entry.get("status", ""), entry.get("time_taken", ""))
            for column, value in enumerate(values):
                self.history_table.setItem(row_index, column, QTableWidgetItem(value))
            if entry.get("job_id"):
                self._history_row_by_id[entry["job_id"]] = row_index
        self.history_table.scrollToBottom()

    def _clear_history(self):
        yes = QMessageBox.StandardButton.Yes
        no = QMessageBox.StandardButton.No
        answer = QMessageBox.question(self, "Clear download history", "Delete all saved download history?",
                                      yes | no, no)
        if answer == yes:
            self._history_suppressed_ids.update(self._job_history_ids.values())
            try:
                if os.path.exists(self.history_path):
                    os.remove(self.history_path)
            except OSError as exc:
                QMessageBox.warning(self, "Could not clear history", str(exc))
            self._refresh_history_table()

    def _on_download_finished(self):
        self.elapsed_timer.stop()
        for row in self._job_started_at:
            if row not in self._job_elapsed_seconds or not self.results_table.item(row, 3) or self.results_table.item(row, 3).text().lower() not in ("downloaded", "failed", "completed", "cancelled", "canceled"):
                started = self._job_started_at.get(row)
                elapsed = int(time.monotonic() - started) if started is not None else 0
                self._job_elapsed_seconds[row] = elapsed
                self.results_table.setItem(row, 3, QTableWidgetItem("Failed"))
                self.results_table.setItem(row, 2, QTableWidgetItem("Download worker ended before reporting a result."))
                self.results_table.setItem(row, 4, QTableWidgetItem(self._format_duration(elapsed)))
                record = self._job_history_records.get(row)
                if record:
                    record["status"] = "Failed"
                    record["path_or_details"] = "Download worker ended before reporting a result."
                    record["time_taken"] = self._format_duration(elapsed)
                    self._write_history_record(record)
        for row in range(self.results_table.rowCount()):
            if row not in self._job_started_at:
                self._job_elapsed_seconds[row] = 0
                self.results_table.setItem(row, 3, QTableWidgetItem("Failed"))
                self.results_table.setItem(row, 2, QTableWidgetItem("Download worker ended before starting this job."))
                self.results_table.setItem(row, 4, QTableWidgetItem("00:00:00"))
                record = self._job_history_records.get(row)
                if record:
                    record["status"] = "Failed"
                    record["path_or_details"] = "Download worker ended before starting this job."
                    record["time_taken"] = "00:00:00"
                    self._write_history_record(record)
        self._refresh_history_table()
        self._download_thread = None
        self._download_worker = None
        self.start_download.setEnabled(True)
        self.start_download.setText("▶  Start Download")
        self.add_to_project.setEnabled(any(
            self.results_table.item(row, 3) and self.results_table.item(row, 3).text() == "Downloaded"
            and self.results_table.item(row, 2) and self.results_table.item(row, 2).text().lower().endswith((".tif", ".tiff"))
            for row in range(self.results_table.rowCount())
        ))

    def _add_downloads_to_project(self):
        from qgis.core import QgsRasterLayer
        loaded = 0
        for row in range(self.results_table.rowCount()):
            status = self.results_table.item(row, 3)
            path_item = self.results_table.item(row, 2)
            name_item = self.results_table.item(row, 0)
            if not status or status.text() != "Downloaded" or not path_item or not name_item:
                continue
            path = path_item.text()
            if path.lower().endswith((".tif", ".tiff")):
                layer = QgsRasterLayer(path, name_item.text())
                if layer.isValid():
                    QgsProject.instance().addMapLayer(layer)
                    loaded += 1
        QMessageBox.information(self, "Add downloads to project", f"Added {loaded} valid raster layer(s) to the QGIS project.")

    def _open_output_folder(self):
        folder = self.output_path.text().strip()
        if folder and os.path.isdir(folder):
            from qgis.PyQt.QtGui import QDesktopServices
            from qgis.PyQt.QtCore import QUrl
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        else:
            QMessageBox.information(self, "Output folder", "The output folder does not exist yet.")

    def _show_help(self):
        QMessageBox.information(
            self,
            "GeoToolkit for Google Earth Engine Help",
            "Use the five steps to define an area of interest, choose datasets, set processing options, "
            "configure output, and review results.\n\n"
            "For a polygon layer, choose a loaded polygon layer or browse to import one. "
            "Enable ‘Use selected features only’ when you want to use only the layer’s selected features. "
            "Use Authenticate and Initialize in the header to sign in with Google and initialize a registered Cloud Project. "
            "Rasters can be saved locally or to Google Drive. Supported vector datasets are submitted as Earth Engine table tasks to Google Drive. Use View history to revisit previous runs; New session clears the current results and dataset checks while keeping history and authentication.",
        )

    def _new_session(self):
        if self._download_thread is not None and self._download_thread.isRunning():
            return
        if self._ee_thread is not None and self._ee_thread.isRunning():
            return
        for item in self.dataset_items.values():
            item.setCheckState(0, _UNCHECKED)
        self.results_table.setRowCount(0)
        self.add_to_project.setEnabled(False)
        self.start_download.setEnabled(True)
        self.start_download.setText("▶  Start Download")
        self._go_to(0)

    def _go_to(self, index):
        index = max(0, min(len(STEPS) - 1, index))
        self.current_step = index
        self.stack.setCurrentIndex(index)
        self._update_step_ui()
        if index == 2:
            self._refresh_dataset_options()
        if index == 3:
            self._update_request_table()

    def _update_step_ui(self):
        for index, button in enumerate(self.step_buttons):
            button.setChecked(index == self.current_step)
            marker = self.step_markers[index]
            marker.setText("✓" if index < self.current_step else str(index + 1))
            marker.setAlignment(_ALIGN_CENTER)
            marker.setContentsMargins(0, 0, 0, 0)
            marker.setMargin(0)
            if index == self.current_step:
                marker.setStyleSheet("border: 0; background: transparent; color: #0789cf; font-weight: 700;")
            elif index < self.current_step:
                marker.setStyleSheet("border: 0; background: transparent; color: #3986ad; font-weight: 700;")
            else:
                marker.setStyleSheet("border: 0; background: transparent; color: #69839b; font-weight: 700;")
        self.step_caption.setText(f"Step {self.current_step + 1} of {len(STEPS)}")
        self.back_button.setVisible(self.current_step > 0)
        self.next_button.setVisible(self.current_step < len(STEPS) - 1)
        self.next_button.setText("Next  →")
        if self.current_step == 3:
            self.next_button.setVisible(False)
        if self.current_step == 4:
            self.next_button.setVisible(False)

