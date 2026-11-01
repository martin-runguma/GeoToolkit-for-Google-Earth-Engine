# GeoToolkit – Data Sources and Attribution

## 1. Overview

GeoToolkit is an open-source QGIS plugin designed to facilitate access to geospatial datasets from Google Earth Engine and other geospatial data providers.

This document acknowledges the original providers of the datasets accessible through GeoToolkit and outlines relevant attribution and licensing considerations.

GeoToolkit is an independent software project. It is not affiliated with, endorsed by, or officially maintained by the organizations listed below unless explicitly stated otherwise.

**Important:** The GPL-3.0-or-later license governing GeoToolkit applies to the plugin's software code. It does not automatically apply to third-party datasets accessed or downloaded through the plugin. Each dataset remains subject to its own licensing terms and attribution requirements.

## 2. Satellite Imagery

### 2.1 Landsat

**Providers:** United States Geological Survey (USGS) and NASA.

**Dataset:** Landsat Collection 2 Level-2.

**Supported missions:** Landsat 4, 5, 7, 8 and 9, subject to availability.

**Products:**
- RGB composites
- False-colour composites
- Surface reflectance
- Land Surface Temperature (LST)
- Derived spectral indices

**Suggested attribution:**

Landsat data courtesy of the U.S. Geological Survey (USGS).

**Reference:**
https://www.usgs.gov/landsat-missions

### 2.2 Sentinel-2

**Providers:** European Union / Copernicus Programme and European Space Agency (ESA).

**Dataset:** Copernicus Sentinel-2 Surface Reflectance.

**Google Earth Engine collection:**
`COPERNICUS/S2_SR_HARMONIZED`

**Products:**
- RGB composites
- False-colour composites
- NDVI
- NDBI
- NDWI
- Other derived spectral indices

**Suggested attribution:**

Contains modified Copernicus Sentinel-2 data.

**Reference:**
https://dataspace.copernicus.eu/

## 3. Population Data

### 3.1 WorldPop Global 2

**Provider:** WorldPop, University of Southampton.

**Dataset:** WorldPop Global 2.

**Release:** R2025A v1.

**Resolution:** 100 metres.

**Google Earth Engine collection:**
`WorldPop/GP/100m/R2025A/v1/pop`

**Product:**
- Gridded population count.

**Suggested attribution:**

Source: WorldPop, University of Southampton. WorldPop Global 2, R2025A v1.

Users should cite the specific dataset and release according to the provider's recommended citation.

**Reference:**
https://www.worldpop.org/

## 4. Building Datasets

### 4.1 Google Open Buildings – Temporal

**Provider:** Google Research.

**Dataset:** Open Buildings 2.5D Temporal.

**Google Earth Engine collection:**
`GOOGLE/Research/open-buildings-temporal/v1`

**Products may include:**
- Building presence
- Building height
- Building-related count and fractional layers

**Suggested attribution:**

Google Research Open Buildings 2.5D Temporal dataset.

**Reference:**
https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_Research_open-buildings-temporal_v1

### 4.2 Google Open Buildings – V3

**Provider:** Google Research.

**Dataset:** Open Buildings V3.

**Google Earth Engine collection:**
`GOOGLE/Research/open-buildings/v3/polygons`

**Product:**
- Building footprint polygons.

**Suggested attribution:**

Google Research Open Buildings V3.

**Reference:**
https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_Research_open-buildings_v3_polygons

### 4.3 Microsoft Global ML Building Footprints

**Provider:** Microsoft.

**Dataset:** Global ML Building Footprints.

**Product:**
- Building footprint polygons.

**Suggested attribution:**

Microsoft Global ML Building Footprints.

**Reference:**
https://github.com/microsoft/GlobalMLBuildingFootprints

### 4.4 OpenBuildingMap

**Provider:** OpenBuildingMap / GFZ German Research Centre for Geosciences.

**Products:**
- Building footprints.
- Available building attributes.

**Suggested attribution:**

OpenBuildingMap. Cite the relevant dataset release and DOI according to the provider's documentation.

OpenBuildingMap may incorporate information from multiple upstream sources. Users should preserve applicable source-level attribution and comply with the relevant database licensing requirements.

**Reference:**
https://www.openbuildingmap.org/

### 4.5 GlobalBuildingAtlas

**Provider:** GlobalBuildingAtlas research project.

**Products may include:**
- Building footprint polygons.
- Building heights.
- Building attributes.

**Suggested attribution:**

GlobalBuildingAtlas. Cite the relevant dataset release and associated research publication.

**Reference:**
https://doi.org/10.5194/essd-17-6647-2025

## 5. Derived Products

GeoToolkit may generate derived geospatial products using the datasets listed above.

Examples include:

- Normalized Difference Vegetation Index (NDVI).
- Normalized Difference Built-up Index (NDBI).
- Normalized Difference Water Index (NDWI).
- Dry Built-up Soil Index (DBSI).
- Urban Index (UI).
- Land Surface Temperature (LST).

Attribution for derived products should acknowledge the original source imagery or datasets used in their calculation.

## 6. Third-Party Data and Licensing

GeoToolkit does not claim ownership of third-party datasets, satellite imagery, building footprints, population estimates, or other externally provided information.

Each dataset remains subject to its respective license, attribution requirements, and terms of use.

Users should consult the original provider's documentation before:
- Redistributing downloaded datasets.
- Publishing derived products.
- Using datasets commercially.
- Combining datasets with different licensing conditions.

The software license governing GeoToolkit does not grant additional rights over third-party data.

## 7. Acknowledgements

GeoToolkit acknowledges the contributions of the organizations, research institutions, developers, and open-data communities that make geospatial information accessible for research, planning, and development.

We particularly acknowledge USGS, NASA, ESA, Copernicus, WorldPop, Google Research, Microsoft, GFZ, and the GlobalBuildingAtlas research team.

## 8. Document Maintenance

This document will be updated as new data providers and datasets are integrated into GeoToolkit.

Dataset versions, licensing conditions, and attribution requirements should be reviewed before each public release.

For reproducibility, users are encouraged to retain dataset identifiers, source information, acquisition dates, and processing details when using downloaded data.