"""Earth Engine raster/vector export worker used by the QGIS dialog."""
from __future__ import annotations

import json
import gc
import math
import os
import sqlite3
import shutil
import tempfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from qgis.PyQt.QtCore import QObject, pyqtSignal


class EarthEngineDownloadWorker(QObject):
    """Run EE requests off the GUI thread and report per-product status."""

    progress = pyqtSignal(int, str, str, str)
    finished = pyqtSignal()

    def __init__(self, project_id, jobs, geometry, destination, local_folder, drive_folder,
                 worker_count=2):
        super().__init__()
        self.project_id = project_id
        self.jobs = jobs
        self.geometry = geometry
        self.destination = destination
        self.local_folder = local_folder
        self.drive_folder = drive_folder
        self.worker_count = max(1, min(4, int(worker_count)))
        self._table_tasks = []

    @staticmethod
    def _landsat(ee, region, start, end, cloud, mask):
        specs = [
            ("LANDSAT/LT04/C02/T1_L2", ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"], ["blue", "green", "red", "nir", "swir1", "swir2"]),
            ("LANDSAT/LT05/C02/T1_L2", ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"], ["blue", "green", "red", "nir", "swir1", "swir2"]),
            ("LANDSAT/LE07/C02/T1_L2", ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"], ["blue", "green", "red", "nir", "swir1", "swir2"]),
            ("LANDSAT/LC08/C02/T1_L2", ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"], ["blue", "green", "red", "nir", "swir1", "swir2"]),
            ("LANDSAT/LC09/C02/T1_L2", ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"], ["blue", "green", "red", "nir", "swir1", "swir2"]),
        ]
        collections = []
        for collection_id, bands, names in specs:
            col = ee.ImageCollection(collection_id).filterBounds(region).filterDate(start, end).filter(ee.Filter.lte("CLOUD_COVER", cloud))
            def prep(image, bands=bands, names=names):
                qa = image.select("QA_PIXEL")
                good = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0)) if mask else ee.Image(1)
                return image.updateMask(good).select(bands, names).multiply(0.0000275).add(-0.2).copyProperties(image, ["system:time_start"])
            collections.append(col.map(prep))
        merged = collections[0]
        for col in collections[1:]:
            merged = merged.merge(col)
        return merged

    @staticmethod
    def _sentinel(ee, region, start, end, cloud, mask):
        col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region).filterDate(start, end).filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", cloud))
        def prep(image):
            qa = image.select("QA60")
            good = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0)) if mask else ee.Image(1)
            return image.updateMask(good).select(["B2", "B3", "B4", "B8", "B11", "B12"], ["blue", "green", "red", "nir", "swir1", "swir2"]).divide(10000).copyProperties(image, ["system:time_start"])
        return col.map(prep)

    def _image(self, ee, job, region):
        title = job["title"]
        options = job["options"]
        start = options.get("start", "2020-01-01")
        end = options.get("end", "2021-01-01")
        cloud = options.get("cloud", 20)
        mask = options.get("mask", True)
        if title.startswith(("Landsat RGB", "Landsat False Color")) or (title.startswith("LST") or "LST" in title):
            collection = self._landsat(ee, region, start, end, cloud, mask)
            composite = collection.median()
            if "False Color" in title:
                return composite.select(["nir", "red", "green"], ["SR_B5", "SR_B4", "SR_B3"]), 30
            if "LST" in title:
                # Use Landsat 8/9 surface temperature where the ST product exists.
                thermal = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")).filterBounds(region).filterDate(start, end).filter(ee.Filter.lte("CLOUD_COVER", cloud))
                def temperature_celsius(image):
                    qa = image.select("QA_PIXEL")
                    cloud_free = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 4).eq(0))
                    return image.select("ST_B10").updateMask(cloud_free).multiply(0.00341802).add(149.0).subtract(273.15).rename("LST_C")
                return thermal.map(temperature_celsius).median().rename("LST_C"), 30
            return composite.select(["red", "green", "blue"], ["red", "green", "blue"]), 30
        if title.startswith("Sentinel 2 RGB"):
            return self._sentinel(ee, region, start, end, cloud, mask).median().select(["red", "green", "blue"]), 10
        if title.startswith("Population (WorldPop"):
            year = int(options.get("year", 2024))
            image = ee.ImageCollection("WorldPop/GP/100m/R2025A/v1/pop").filter(ee.Filter.eq("year", year)).mosaic()
            return image.select("population").rename("population_count").clip(region), 100
        if title.startswith("Building Height"):
            year = int(options.get("year", 2023))
            band = options.get("band", "building_height")
            col = ee.ImageCollection("GOOGLE/Research/open-buildings-temporal/v1").filterBounds(region).filterDate(f"{year}-01-01", f"{year + 1}-01-01")
            return col.mosaic().select(band).clip(region), 4
        index_names = ("NDVI", "NDBI", "DBSI", "UI", "NDWI")
        index = next((n for n in index_names if n in title), None)
        if index:
            sensor = job.get("sensor", "Landsat")
            col = self._landsat(ee, region, start, end, cloud, mask) if sensor == "Landsat" else self._sentinel(ee, region, start, end, cloud, mask)
            image = col.median()
            ndvi = image.normalizedDifference(["nir", "red"])
            if index == "NDVI": result = ndvi
            elif index == "NDBI": result = image.normalizedDifference(["swir1", "nir"])
            elif index == "DBSI": result = image.normalizedDifference(["swir1", "green"]).subtract(ndvi)
            elif index == "UI": result = image.normalizedDifference(["swir2", "nir"])
            else: result = image.normalizedDifference(["green", "nir"])
            return result.rename(index).clip(region), 30 if sensor == "Landsat" else 10
        return None, None

    @staticmethod
    def _is_payload_limit_error(error):
        message = str(error).lower()
        return any(token in message for token in (
            "total request size", "must be less than or equal to 50331648",
            "request size exceeds", "request payload size", "48 mib",
        ))

    @staticmethod
    def _bounds(region):
        rings = region.bounds(1).coordinates().getInfo()
        points = [point for ring in rings for point in ring]
        return (min(point[0] for point in points), min(point[1] for point in points),
                max(point[0] for point in points), max(point[1] for point in points))

    def _download_image_piece(self, ee, requests, image, region, name, scale, folder,
                              crs="EPSG:4326", depth=0, band_count=None):
        """Download one image piece, splitting proactively and on EE size errors."""
        params = {"name": name, "region": region, "scale": scale,
                  "crs": crs,
                  "format": "ZIPPED_GEO_TIFF"}
        payload_error = None
        try:
            if band_count is None:
                band_count = max(1, int(image.bandNames().size().getInfo()))
            area_m2 = float(region.area(100).getInfo())
            estimated_bytes = (area_m2 / max(float(scale), 1.0) ** 2) * band_count * 4
            west, south, east, north = self._bounds(region)
            estimated_width = abs(east - west) * 111320 / max(float(scale), 1.0)
            estimated_height = abs(north - south) * 111320 / max(float(scale), 1.0)
            if estimated_bytes > 32 * 1024 * 1024 or max(estimated_width, estimated_height) > 9000:
                raise RuntimeError(
                    f"total request size is estimated at {int(estimated_bytes)} bytes "
                    f"with a {int(max(estimated_width, estimated_height))}-pixel longest dimension; "
                    "splitting this raster request before Earth Engine rejects it"
                )
            url = image.getDownloadURL(params)
            with requests.get(url, timeout=300, stream=True) as response:
                if not response.ok:
                    detail = response.text[:2000]
                    if self._is_payload_limit_error(detail):
                        raise RuntimeError(detail)
                    raise RuntimeError(
                        f"Earth Engine image download returned HTTP {response.status_code}: "
                        f"{detail or response.reason}"
                    )
                # Keep large zipped rasters off the Python heap; this avoids a
                # response.content + BytesIO + source.read() triple copy.
                with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024,
                                                   mode="w+b") as archive_file:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            archive_file.write(chunk)
                    archive_file.seek(0)
                    with zipfile.ZipFile(archive_file) as archive:
                        tif_names = [n for n in archive.namelist()
                                     if n.lower().endswith((".tif", ".tiff"))]
                        if not tif_names:
                            raise RuntimeError("Earth Engine response did not contain a GeoTIFF.")
                        output_path = os.path.join(folder, name + ".tif")
                        with archive.open(tif_names[0]) as source, open(output_path, "wb") as output:
                            shutil.copyfileobj(source, output, length=1024 * 1024)
            return [output_path]
        except Exception as exc:
            if not self._is_payload_limit_error(exc):
                raise
            payload_error = exc
            if depth >= 8:
                raise RuntimeError(
                    "Earth Engine still reports an oversized request after eight tile splits. "
                    "Choose a coarser resolution or export this dataset to Google Drive."
                ) from exc

        west, south, east, north = self._bounds(region)
        mid_x, mid_y = (west + east) / 2, (south + north) / 2
        if east - west < 1e-7 or north - south < 1e-7:
            raise RuntimeError(
                "Earth Engine rejected a tiny AOI tile as oversized; use Google Drive for this export."
            ) from payload_error
        rectangles = (
            (west, south, mid_x, mid_y), (mid_x, south, east, mid_y),
            (west, mid_y, mid_x, north), (mid_x, mid_y, east, north),
        )
        pieces = []
        for tile_index, coords in enumerate(rectangles):
            tile = ee.Geometry.Rectangle(list(coords), proj="EPSG:4326", geodesic=False)
            clipped = region.intersection(tile, 1)
            if clipped.area(1).getInfo() <= 0:
                continue
            pieces.extend(self._download_image_piece(
                ee, requests, image.clip(clipped), clipped,
                f"{name}_part{tile_index + 1}", scale, folder, crs, depth + 1,
                band_count,
            ))
        if not pieces:
            raise RuntimeError("Earth Engine produced no non-empty tiles for this area.")
        return pieces

    def _download_local_image(self, ee, requests, image, region, job, scale):
        """Save one GeoTIFF, mosaicking spatial tiles when the local API limit is hit."""
        os.makedirs(self.local_folder, exist_ok=True)
        final_path = os.path.join(self.local_folder, job["name"] + ".tif")
        with tempfile.TemporaryDirectory(prefix="geotoolkit_ee_") as temp_folder:
            pieces = self._download_image_piece(
                ee, requests, image, region, job["name"], scale, temp_folder,
                job.get("options", {}).get("crs", "EPSG:4326"),
            )
            if len(pieces) == 1:
                staged_path = final_path + ".partial"
                try:
                    shutil.copy2(pieces[0], staged_path)
                    os.replace(staged_path, final_path)
                    os.remove(pieces[0])
                finally:
                    if os.path.exists(staged_path):
                        os.remove(staged_path)
                return final_path
            try:
                from osgeo import gdal
                gdal.UseExceptions()
                result = gdal.Warp(
                    final_path, pieces, format="GTiff",
                    creationOptions=["COMPRESS=LZW", "TILED=YES"],
                    resampleAlg="near",
                )
                if result is None:
                    raise RuntimeError("GDAL could not mosaic the downloaded image tiles.")
                result.FlushCache()
                result = None
            except Exception as exc:
                if os.path.exists(final_path):
                    os.remove(final_path)
                raise RuntimeError(
                    "The image was downloaded in tiles, but QGIS GDAL could not mosaic them: " + str(exc)
                ) from exc
        return final_path

    def _process_job(self, ee, requests, region, index, job):
        """Run one product export. Safe for bounded local worker threads."""
        title = job["title"]
        is_vector = title.startswith((
            "Open Buildings Polygon V3",
            "Global Building Atlas Polygons",
            "OpenBuildingMap",
            "Microsoft Buildings",
        ))
        self.progress.emit(
            index, title,
            "Preparing task" if is_vector else "Downloading",
            "Preparing Earth Engine table export…" if is_vector else "Preparing Earth Engine request…",
        )
        image, scale = self._image(ee, job, region)
        if image is not None:
            if self.destination == "Google Drive":
                task = ee.batch.Export.image.toDrive(
                    image=image, description=job["name"], folder=self.drive_folder,
                    fileNamePrefix=job["name"], region=region, scale=scale,
                    crs=job.get("options", {}).get("crs", "EPSG:4326"),
                    maxPixels=1e13, fileFormat="GeoTIFF",
                )
                task.start()
                self.progress.emit(index, title, "Queued in Google Drive", task.id)
                return task
            path = self._download_local_image(ee, requests, image, region, job, scale)
            self.progress.emit(index, title, "Downloaded", path)
            return None
        if title.startswith("Open Buildings Polygon V3"):
            collection = ee.FeatureCollection(
                "GOOGLE/Research/open-buildings/v3/polygons"
            ).filterBounds(region)
        elif title.startswith("Global Building Atlas Polygons"):
            tile_id = job.get("tile_ids", [""])[0]
            collection = ee.FeatureCollection(
                "projects/sat-io/open-datasets/GLOBAL_BUILDING_ATLAS/" + tile_id
            ).filterBounds(region)
        elif title.startswith("OpenBuildingMap"):
            tile_id = job.get("tile_ids", [""])[0]
            collection = ee.FeatureCollection(
                "projects/sat-io/open-datasets/OPEN-BUILDING-MAPS/tiles/building_" + tile_id  # pragma: allowlist secret -- public EE asset path
            ).filterBounds(region)
        elif title.startswith("Microsoft Buildings"):
            options = job.get("options", {})
            country_name = options.get("ms_country", "").strip()
            if not country_name:
                raise ValueError("Select a country for Microsoft Buildings.")
            if country_name == "United States":
                state_code = options.get("ms_state_code", "").strip().upper()
                if not state_code:
                    raise ValueError("Select a U.S. state for the Microsoft Buildings download.")
                asset_id = (
                    "projects/sat-io/open-datasets/ORNL/USA-STRUCTURES/USA_ST_" + state_code
                )
            else:
                asset_id = "projects/sat-io/open-datasets/MSBuildings/" + country_name
            aoi = region
            collection = (
                ee.FeatureCollection(asset_id)
                .filterBounds(aoi)
                .map(lambda feature: ee.Feature(
                    feature.geometry().intersection(aoi, ee.ErrorMargin(1))
                ).copyProperties(feature))
            )
        else:
            raise RuntimeError(
                "This provider does not expose a verified Earth Engine asset or "
                "configured download endpoint. Use the dataset provider's tile "
                "download and import the result into QGIS."
            )
        self._export_table(ee, requests, index, job, collection)
        return None

    def _download_openbuildingmap(self, requests, index, job):
        """Fetch a GFZ level-6 quadkey tile (GeoPackage compressed as bzip2)."""
        import bz2

        tile = job.get("tile_ids", [""])[0].strip()
        if len(tile) != 6 or any(char not in "0123" for char in tile):
            raise ValueError("OpenBuildingMap requires a six-digit Quadkey using only 0–3.")
        # GFZ Data Services keeps the published tile files under this DOI package.
        url = ("https://datapub.gfz.de/download/10.5880.GFZ.LKUT.2025.002-Caweb/"
               f"2025-002_Oostwegel-et-al_data/building.{tile}.gpkg.bz2")
        os.makedirs(self.local_folder, exist_ok=True)
        output_path = os.path.join(self.local_folder, job["name"] + ".gpkg")
        compressed_path = output_path + ".bz2.partial"
        staged_path = output_path + ".partial"
        try:
            with requests.get(url, timeout=300, stream=True) as response:
                response.raise_for_status()
                with open(compressed_path, "wb") as target:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            target.write(chunk)
            with bz2.open(compressed_path, "rb") as source, open(staged_path, "wb") as target:
                shutil.copyfileobj(source, target, 1024 * 1024)
            # Reject an HTML error page or corrupt archive before publishing it.
            db = sqlite3.connect(staged_path)
            try:
                db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            finally:
                db.close()
            os.replace(staged_path, output_path)
            self.progress.emit(index, job["title"], "Downloaded", output_path)
        finally:
            for path in (compressed_path, staged_path):
                if os.path.exists(path):
                    os.remove(path)

    def run(self):
        tasks = []
        try:
            import ee
            import requests
            ee.Initialize(project=self.project_id)
            region = ee.Geometry(json.loads(self.geometry))
            if self.destination == "Local computer":
                os.makedirs(self.local_folder, exist_ok=True)
            if self.destination == "Local computer" and self.worker_count > 1:
                # Concurrent work is limited to local downloads and capped in
                # the UI. Keep Drive task creation on its existing serial path.
                with ThreadPoolExecutor(max_workers=self.worker_count,
                                        thread_name_prefix="GeoToolkitDownload") as pool:
                    futures = {
                        pool.submit(self._process_job, ee, requests, region, index, job):
                        (index, job["title"])
                        for index, job in enumerate(self.jobs)
                    }
                    for future in as_completed(futures):
                        index, title = futures[future]
                        try:
                            future.result()
                        except Exception as exc:
                            self.progress.emit(index, title, "Failed", str(exc))
            else:
                for index, job in enumerate(self.jobs):
                    try:
                        task = self._process_job(ee, requests, region, index, job)
                        if task is not None:
                            tasks.append((index, job["title"], task))
                    except Exception as exc:
                        self.progress.emit(index, job["title"], "Failed", str(exc))
            tasks.extend(getattr(self, "_table_tasks", []))
            pending = list(tasks)
            while pending:
                still_running = []
                for index, title, task in pending:
                    try:
                        status = task.status()
                        state = status.get("state", "UNKNOWN")
                        if state in ("COMPLETED", "FAILED", "CANCELLED"):
                            detail = status.get("error_message", "Export completed in Google Drive")
                            self.progress.emit(index, title, state.title(), detail)
                        else:
                            still_running.append((index, title, task))
                    except Exception as exc:
                        self.progress.emit(index, title, "Failed", str(exc))
                pending = still_running
                if pending:
                    time.sleep(8)
        except Exception as exc:
            self.progress.emit(-1, "Earth Engine", "Failed", str(exc))
        finally:
            self.finished.emit()

    def _export_table(self, ee, requests, index, job, collection):
        # All supported vector datasets use asynchronous EE Drive tasks,
        # regardless of the raster destination selected in the dialog.
        task = ee.batch.Export.table.toDrive(
            collection=collection,
            description=job["name"],
            folder=self.drive_folder,
            fileNamePrefix=job["name"],
            fileFormat="KML",
        )
        task.start()
        self._table_tasks.append((index, job["title"], task))
        self.progress.emit(index, job["title"], "Queued in Google Drive", task.id)

    def _download_sharded_geojson(self, ee, requests, index, job, collection):
        """Partition oversized tables into disjoint random shards, then merge locally."""
        from osgeo import gdal

        count = int(collection.size().getInfo())
        if count <= 0:
            raise RuntimeError("The selected vector area contains no features.")
        properties = collection.first().propertyNames()
        property_names = properties.getInfo()
        if not property_names:
            raise RuntimeError("Earth Engine returned no vector properties.")
        shard_column = "__geotoolkit_partition"
        randomized = collection.randomColumn(columnName=shard_column, seed=20261101)
        partition_count = min(128, max(2, math.ceil(count / 20000)))
        output_json = os.path.join(self.local_folder, job["name"] + ".geojson")
        staged_json = output_json + ".partial"
        output_gpkg = os.path.join(self.local_folder, job["name"] + ".gpkg")

        def fetch_range(low, high, depth, serial, temp_folder):
            subset = randomized.filter(ee.Filter.gte(shard_column, low))
            upper_filter = ee.Filter.lte(shard_column, high) if high >= 1 else ee.Filter.lt(shard_column, high)
            subset = subset.filter(upper_filter).select(property_names)
            chunk_path = os.path.join(temp_folder, f"part_{serial}.geojson")
            last_error = None
            for attempt in range(3):
                try:
                    url = subset.getDownloadURL(filetype="geojson")
                    byte_count = 0
                    with requests.get(url, timeout=300, stream=True) as response:
                        response.raise_for_status()
                        with open(chunk_path, "wb") as target:
                            for block in response.iter_content(1024 * 1024):
                                if block:
                                    target.write(block)
                                    byte_count += len(block)
                    if byte_count == 0:
                        raise RuntimeError("Earth Engine returned an empty shard.")
                    with open(chunk_path, "r", encoding="utf-8") as source:
                        shard_data = json.load(source)
                    if shard_data.get("type") != "FeatureCollection":
                        raise RuntimeError("Earth Engine returned a non-GeoJSON shard.")
                    if not shard_data.get("features"):
                        os.remove(chunk_path)
                        return []
                    return [chunk_path]
                except Exception as exc:
                    last_error = exc
                    message = str(exc).lower()
                    retryable = any(token in message for token in (
                        "500 server error", "502 server error", "503 server error",
                        "504 server error", "internal server error", "service unavailable",
                        "gateway timeout", "connection aborted", "remote end closed",
                        "remote disconnected", "connection reset", "timed out",
                    ))
                    if retryable and attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    break
            if os.path.exists(chunk_path):
                os.remove(chunk_path)
            if not retryable or depth >= 4:
                raise RuntimeError(f"partition [{low:.6f}, {high:.6f}] failed: {last_error}") from last_error
            quarter = (high - low) / 4
            found = []
            for offset in range(4):
                child_low = low + quarter * offset
                child_high = high if offset == 3 else child_low + quarter
                found.extend(fetch_range(child_low, child_high, depth + 1,
                                         f"{serial}_{offset + 1}", temp_folder))
            return found

        os.makedirs(self.local_folder, exist_ok=True)
        try:
            with tempfile.TemporaryDirectory(prefix="geotoolkit_gba_parts_") as temp_folder:
                chunks = []
                for part in range(partition_count):
                    low = part / partition_count
                    high = (part + 1) / partition_count
                    chunks.extend(fetch_range(low, high, 0, str(part + 1), temp_folder))
                if not chunks:
                    raise RuntimeError("Earth Engine returned no vector features for the selected tile.")
                with open(staged_json, "w", encoding="utf-8") as merged:
                    merged.write('{"type":"FeatureCollection","features":[')
                    first_feature = True
                    for chunk_path in chunks:
                        # Each shard is capped at roughly 20k features, keeping
                        # parsing bounded while the merged output streams to disk.
                        with open(chunk_path, "r", encoding="utf-8") as source:
                            shard_data = json.load(source)
                        for feature in shard_data["features"]:
                            if not first_feature:
                                merged.write(",")
                            json.dump(feature, merged, separators=(",", ":"))
                            first_feature = False
                    merged.write("]}")
                try:
                    gdal.UseExceptions()
                    result = gdal.VectorTranslate(output_gpkg, staged_json, format="GPKG")
                    if result is not None:
                        result.FlushCache()
                        result = None
                    gc.collect()
                    if os.path.exists(output_gpkg) and os.path.getsize(output_gpkg) > 0:
                        db = sqlite3.connect(output_gpkg)
                        try:
                            valid_gpkg = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='gpkg_contents'").fetchone()
                        finally:
                            db.close()
                        if valid_gpkg:
                            os.remove(staged_json)
                            return output_gpkg
                except Exception as exc:
                    self.progress.emit(
                        index,
                        job["title"],
                        "Preparing fallback",
                        f"GeoPackage creation failed; using GeoJSON instead: {exc}",
                    )
                if os.path.exists(output_gpkg):
                    try:
                        os.remove(output_gpkg)
                    except OSError as cleanup_error:
                        self.progress.emit(
                            index,
                            job["title"],
                            "Preparing fallback",
                            f"Could not remove the incomplete GeoPackage; continuing with GeoJSON: {cleanup_error}",
                        )
                os.replace(staged_json, output_json)
                return output_json
        finally:
            for path in (staged_json, output_gpkg):
                if os.path.exists(path) and os.path.getsize(path) == 0:
                    os.remove(path)
