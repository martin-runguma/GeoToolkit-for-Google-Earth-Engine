
# GEE Data Toolkit

A QGIS plugin designed to simplify access to satellite imagery, remote sensing products, building datasets, and population data through Google Earth Engine and other geospatial data providers.

## Overview

GEE Data Toolkit brings multiple geospatial datasets into a unified QGIS interface, allowing users to select datasets, configure processing options, define an area of interest, and download results directly to their local computer or Google Drive where supported.

The toolkit aims to reduce the complexity of accessing and preparing geospatial data for GIS, urban planning, remote sensing, and spatial analysis workflows.

## Key Features

- Integrated dataset selection and management.
- Google Earth Engine authentication and project configuration.
- Area of Interest (AOI) based data extraction.
- Local computer downloads where supported.
- Google Drive exports where supported.
- Configurable satellite imagery and spectral index parameters.
- Raster and vector dataset support.
- Automatic loading of downloaded datasets into QGIS.
- Dataset previews and descriptive information.
- Provider-specific download handling.

## Supported Data Categories

### Satellite Imagery
- Landsat RGB
- Landsat False Color
- Sentinel-2 RGB

### Spectral Indices
- Normalized Difference Vegetation Index (NDVI)
- Normalized Difference Built-up Index (NDBI)
- Dry Built-up Soil Index (DBSI)
- Urban Index (UI)
- Normalized Difference Water Index (NDWI)

### Thermal Products
- Landsat Land Surface Temperature (LST)

### Building Datasets
- Microsoft Building Footprints
- OpenBuildingMap (GFZ)
- Global Building Atlas

### Population Data
- WorldPop Global2 Population Count

*Dataset availability, geographic coverage, download methods, and licensing conditions vary by provider.*

## Technology Stack

- QGIS
- Python
- PyQGIS
- Google Earth Engine Python API
- Requests
- Qt / PyQt
- Google Earth Engine

## Requirements

- QGIS with a compatible Python environment.
- A Google Earth Engine account.
- An authorized Google Earth Engine Cloud Project.
- Internet connectivity.
- Required Python dependencies.

## Development Status

The toolkit is under active development. Dataset integrations, download performance, compatibility, and error handling are being progressively improved and tested.

## Project Structure

```text
gee-data-toolkit/
│
├── assets/
│   └── previews/
│
├── core/
│   ├── compat.py
│   ├── earth_engine_downloads.py
│   └── registry.py
│
├── ui/
│   └── main_dialog.py
│
├── plugin.py
│
└── README.md
```

## Intended Applications

- Urban and regional planning.
- Remote sensing and satellite image analysis.
- Building footprint mapping.
- Urban growth monitoring.
- Land use and land cover analysis.
- Population mapping.
- Surface Urban Heat Island analysis.
- Spatial data preparation and visualization.

## Contributions

Suggestions, bug reports, and contributions are welcome.

Please use the GitHub Issues section to report problems or propose improvements.

## Author

Developed by Martin Runguma.

## Acknowledgements

This toolkit builds upon Google Earth Engine, QGIS, and the work of the organizations and research institutions providing the underlying geospatial datasets.

Please consult the original data providers for attribution and licensing requirements.
