# GeoToolkit for Google Earth Engine — User Guide

This guide walks through a complete download with the GeoToolkit for Google Earth Engine QGIS plugin. The plugin lets you define an area of interest (AOI), choose Earth Engine datasets, configure dataset-specific settings, and export results to your computer or Google Drive.

## 1. Before you start

### Requirements

- QGIS 3.28 or later (including QGIS 4).
- An internet connection.
- The plugin's required Python packages installed in the Python environment used by QGIS. The plugin checks for dependencies when it starts and reports any packages that are missing. Install missing packages into the QGIS Python environment shown in that message, then restart QGIS.
- A Google account and an Earth Engine enabled Google Cloud project for Earth Engine operations. You need permission to use the selected Cloud project. The first authentication may open a browser for Google sign-in and consent.

The plugin uses the Earth Engine Python API (`earthengine-api`) to communicate with Earth Engine. QGIS itself does not include that API by default.

### Open the plugin

1. Start QGIS and open the project you want to work in, if applicable.
2. Open **Plugins** and select **GeoToolkit for Google Earth Engine**. Depending on your QGIS layout, the plugin may also be available from its toolbar button.
3. The plugin opens as a five-step wizard: **Area of Interest**, **Dataset Selection**, **Dataset Options**, **Output and Run**, and **Results**.

### Authenticate and initialize Earth Engine

Use **Authenticate and Initialize** in the top-right of the plugin. If prompted, complete Google sign-in and allow Earth Engine access. Enter or confirm the Earth Engine Cloud project ID when requested. A successful connection is shown by the connection-status indicator at the top-left.

Authentication authorizes Earth Engine requests. It does not itself start an export. If the indicator is disconnected, initialize again before starting a download. The plugin may restore a saved project ID when reopened, but you should confirm the connection status for the current QGIS session.

## 2. Step 1 — Choose an area of interest

The AOI applies to every selected dataset in the session.

### Use a polygon layer

1. In **Layer type**, choose **Polygon layer**.
2. Select a polygon layer from the QGIS project. Use **Browse** if you need to load or locate a layer.
3. Optionally check **Use selected features only** to use only the currently selected polygons. If unchecked, all valid polygon features in the layer are used.
4. Review the summary panel, which reports the AOI source, feature count, area, and coordinate reference system (CRS) when available.

The plugin combines the selected polygon geometries to define the export region. Make sure the layer contains the intended features before continuing.

### Use the current map extent

Choose **Current map extent** to use the visible QGIS map canvas extent as the AOI. Set the map canvas to the area you need before proceeding. The map extent is a rectangle; it does not follow an irregular boundary.

### Geometry versus bounding box

For polygon AOIs, the processing setting uses the selected geometry as the area of interest. The bounding-box option uses the enclosing rectangle and can include areas outside an irregular polygon. Use the bounding box when a rectangular extent is intended or when a dataset/service requires a simpler region. Check the AOI summary before moving on.

## 3. Step 2 — Select datasets

The dataset browser groups products by type. Select one or more datasets; the options and output overview will be built from that selection.

### Imagery

- **Landsat RGB** — cloud-masked median true-colour surface-reflectance composite. Mission availability varies by place and date.
- **Landsat False Color** — Landsat 8/9 near-infrared false-colour composite (near infrared, red, green display bands).
- **Sentinel 2 RGB** — cloud-masked median true-colour Sentinel-2 surface-reflectance composite.

### Indices

Indices are derived from Landsat or Sentinel-2 imagery, according to the sensor selection in **Dataset Options**. Choose the sensor source and date range that suit the study. Common products include:

- **NDVI — Vegetation Index**: relative vegetation greenness.
- **NDBI — Built-up Index**: highlights built-up surfaces using near-infrared and shortwave-infrared reflectance.
- **DBSI — Dry Built-up Soil Index**: combines shortwave-infrared, green, and NDVI information to distinguish dry/built-up surfaces.
- **UI — Urban Index**: uses shortwave-infrared and near-infrared reflectance to highlight urban surfaces.
- **NDWI — Water Index**: highlights water-related features; interpretation depends on the selected sensor and formula.
- **LST — Land Surface Temperature**: a Landsat thermal product. Sentinel-2 does not provide the thermal band needed for this product.

Indices are calculated by Earth Engine from the underlying imagery. They are not the same as a pre-existing, single-scene image, and cloud cover, date range, and sensor choice affect the composite.

### Other raster products

- **Population (WorldPop Global2 — Count)** — gridded population count data.
- **Building Height (Open Buildings 2.5D Temporal)** — rasterized building-height product from Google's Open Buildings temporal data.

### Building vectors

- **Open Buildings Polygon V3** — building footprint polygons.
- **Microsoft Buildings** — building footprints from Microsoft's global or US structures collections. Depending on the available collection, you must choose a country, or a US state, in dataset options.
- **OpenBuildingMap (by GFZ)** — provider-hosted building tiles identified by level-6 Quadkeys.
- **Global Building Atlas Polygons** — building polygons identified by 5-degree grid tile IDs.

Coverage, temporal range, source, band/formula information, and credit attribution are shown in the dataset information panel. Read the panel for a selected item before exporting, especially for regional datasets.

## 4. Step 3 — Configure dataset options

The **Dataset Options** page displays settings only for the datasets you selected. Each dataset may have different controls.

### Common imagery and index options

- Set a **start date** and **end date** for products that use an image collection. Choose dates for which the sensor has observations in your AOI.
- Choose the imagery source for indices where the interface offers a sensor setting (Landsat, Sentinel-2, or both, depending on the current option controls).
- Set cloud filtering or masking options if offered. A stricter cloud setting may reduce cloudy observations but can also leave fewer valid images.
- Use the dataset card/reference image and metadata to confirm that the selected product, sensor, and bands match your intended analysis.

If a date range contains no usable imagery over the AOI, Earth Engine may return an empty composite or report an error. Expand the date range, relax cloud filtering, or check dataset coverage.

### Microsoft Buildings options

Choose the country for the global Microsoft collection. For United States structures, choose the relevant state abbreviation/name when that option is provided. The available Earth Engine asset names can differ by region; check the selected country/state carefully before exporting.

### OpenBuildingMap and Global Building Atlas tile IDs

Enter one tile ID per line. Multiple IDs are supported: the plugin creates a separate export job for each supplied tile ID.

- **OpenBuildingMap (GFZ)** uses six-digit level-6 Quadkeys. Each digit must be from `0` to `3`. Example:

  ```text
  300110
  300111
  300112
  ```

- **Global Building Atlas** uses 5-degree grid tile IDs. Enter the exact ID from the GBA tile finder, one per line. Example:

  ```text
  e035_n00_e040_s05
  e040_n00_e045_s05
  ```

Tile IDs identify provider tiles; the AOI still controls the area for datasets that are clipped by Earth Engine. Check the provider's tile finder or download page to ensure the tile covers your study area. Large OpenBuildingMap tiles can be several gigabytes, so confirm disk space and expected transfer time before downloading.

## 5. Step 4 — Set output and start the download

### Select destination

For raster products, choose **Local computer** or **Google Drive** under **Save to**.

- **Local computer** saves the output under the selected local folder. Use **Browse** to choose a writable folder with enough free space.
- **Google Drive** creates Earth Engine export tasks in the specified Drive folder. Authenticate and initialize Earth Engine first. The plugin reports task IDs/status; the task must finish on Earth Engine before the output is available in Drive.

Building-vector products use Earth Engine table exports to Google Drive because provider tables can be large and direct downloads can fail. For those products, expect a Drive task and retrieve the completed file from the configured Drive folder. The export format is shown in the output summary/results.

### Choose file organization and format

The output page lets you review naming and organization controls, including dataset-based subfolders and filename patterns. Raster outputs are generally GeoTIFF. For vector downloads, the plugin uses supported Earth Engine table formats and may try alternate formats when a requested vector format is unsupported or fails. Earth Engine does not accept every desktop GIS format directly; in particular, GeoPackage is not an Earth Engine table-export format.

Choose the output CRS, raster compression, and resampling method as appropriate. The same output CRS can be used for raster and vector exports where the export supports reprojection. Keep the source CRS or use a suitable projected CRS for your mapping/analysis. Nearest-neighbour resampling is appropriate for categorical values; continuous surfaces may need a different method.

### Review the request overview

Before starting, check each row in **Request Overview**:

- Dataset name and output type.
- Resolution or product scale.
- Estimated pixels and size, when the AOI and Earth Engine metadata allow the plugin to estimate them.
- Any missing AOI or metadata note.

An estimate is a guide, not a guarantee. Actual output size depends on valid data, compression, region shape, and the selected resolution.

Click **Start Download** once the AOI, dataset choices, options, destination, folder, CRS, and format are correct. Jobs appear in **Results**. Long downloads and Earth Engine task exports can continue for a while; allow the job to complete and check its status instead of closing QGIS during active local downloads.

## 6. Step 5 — Monitor results and history

### Current results

The **Current results** table tracks the jobs started in the current session. It shows the dataset, output type, path or Earth Engine task reference, status, and elapsed time. Elapsed time updates while jobs are active and is recorded when the job finishes.

Typical statuses include queued/preparing, downloading, downloaded/completed, and failed. For Google Drive exports, a queued task is not yet a downloaded local file: check the task status and then look in the target Drive folder after completion.

When a job fails, select/read its error details in the results table. Common causes include an invalid tile ID, missing access to a Cloud project or dataset, no valid imagery in the selected dates, a region that is too large for a direct request, insufficient local disk space, network interruptions, or a temporary Earth Engine server error.

### Add outputs to the QGIS project

Use **Add to project** after files have been downloaded locally and are ready to load. This loads compatible local results into the active QGIS project. A Google Drive task that is still queued does not yet have a local file to add.

### View history

Open **View history** to review earlier download jobs after the current session. History is retained in the plugin's history log. Use the history controls to clear old entries if the list becomes too large. Clearing the displayed/stored history does not delete downloaded output files from disk or Google Drive.

### Start a new session

Use **New session** when you want to clear the current run's working selections/results and start another download workflow. This is a UI/session reset; it does not delete existing output files or cancel completed Earth Engine exports. Check any still-running Earth Engine tasks separately before starting duplicate exports.

## 7. Practical guidance for large exports

- Start with a small AOI or a single dataset to confirm the connection, dataset settings, and output location.
- Larger AOIs, finer resolution, and multiple datasets increase data volume and processing time.
- For large rasters, exporting to Google Drive can avoid Earth Engine's per-request download payload limits. Local raster downloads may be divided into smaller spatial pieces by the plugin and mosaicked, but this still needs adequate disk space and time.
- Use a coarser scale or smaller AOI if Earth Engine rejects a local download as too large.
- Download vector data by only the needed tiles. Large tiles may take a long time and consume substantial storage.
- Avoid launching duplicate jobs while an earlier task is still running.
- Keep the output folder on a drive with sufficient free space and normal write permissions.
- If a service reports a 500/connection error, retry the affected tile later; server-side failures can be temporary.

## 8. Troubleshooting

### Missing dependencies message

The message lists unavailable Python packages and shows the QGIS Python interpreter path. Install the listed packages using that interpreter in a terminal, then restart QGIS and open the plugin again. Do not install into a different standalone Python environment; QGIS must be able to import the packages.

### Authentication or project initialization fails

1. Check that you can sign into the intended Google account in the browser.
2. Confirm that the Cloud project ID is correct and that Earth Engine is enabled for it.
3. Confirm your account has permission to use that project and the relevant datasets.
4. Click **Authenticate and Initialize** again and complete any browser consent step.
5. Check the connection indicator before starting exports.

### No images, empty composite, or a band error

Confirm sensor availability for the AOI and date range. Some products use specific Landsat missions or bands. For LST, use Landsat because Sentinel-2 has no thermal band. Widen the date range if there are few observations and check cloud settings.

### Earth Engine says the request is too large

Reduce the AOI, use a coarser resolution, or select Google Drive for the raster export. Very large outputs can exceed the direct-download request limit even when your computer has enough disk space.

### Local file or permission error

Select an existing writable folder, confirm sufficient disk space, and avoid a destination that is disconnected or read-only. Close programs that may be locking the target output file and retry.

### Vector export errors

Verify tile IDs and confirm that each tile contains data for the intended area. For provider tables, use the Google Drive export path and allow the Earth Engine task to finish. If an Earth Engine server returns a 500 error, retry later; changing a desktop file extension does not convert an unsupported Earth Engine table format.

## 9. Data credits and attribution

Dataset providers and credit notes are displayed in the plugin's dataset information panel. Preserve the relevant attribution when publishing or redistributing exported data. Typical providers include USGS/NASA Landsat, the European Union/ESA Copernicus Sentinel-2 program, WorldPop, Google Research Open Buildings, Microsoft, GFZ OpenBuildingMap, and the Global Building Atlas. Follow the specific terms and licenses listed for each dataset; licensing is not necessarily the same across providers.

## 10. A simple first-use checklist

1. Open a QGIS project and launch GeoToolkit.
2. Authenticate and initialize Earth Engine; confirm the status says connected.
3. Set a polygon layer or map extent as the AOI and inspect the summary.
4. Select one dataset and review its information card.
5. Set dates, sensor, tile IDs, or region-specific options as needed.
6. Choose the output destination and review the request overview.
7. Start the job and follow its status and elapsed time in Results.
8. Load completed local files into QGIS or retrieve completed Drive exports from Google Drive.

