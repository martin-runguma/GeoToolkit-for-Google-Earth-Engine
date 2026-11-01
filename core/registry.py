"""Dataset registry: declarative metadata only. No GUI, no Earth Engine calls."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, List, Optional, Tuple


class Status(str, Enum):
    VERIFIED = "verified"
    NEEDS_CONFIG = "needs_config"
    UNAVAILABLE = "unavailable"

    @property
    def label(self) -> str:
        return {
            "verified": "Verified",
            "needs_config": "Needs configuration",
            "unavailable": "Unavailable",
        }[self.value]


class Category(str, Enum):
    IMAGERY = "Satellite imagery"
    INDICES = "Spectral indices"
    BUILDINGS = "Building products"
    POPULATION = "Population"
    OTHER = "Other datasets"


CATEGORY_BLURB = {
    Category.IMAGERY: "Optical surface-reflectance composites.",
    Category.INDICES: "Indices calculated from imagery, or existing index products where available.",
    Category.BUILDINGS: "Footprint polygons, presence, count and height products. These are different data types and are not interchangeable.",
    Category.POPULATION: "Gridded population estimates.",
    Category.OTHER: "Extension point for additional datasets.",
}


class OutputType(str, Enum):
    RGB_RASTER = "rgb_raster"
    INDEX_RASTER = "index_raster"
    HEIGHT_RASTER = "height_raster"
    PRESENCE_RASTER = "presence_raster"
    COUNT_RASTER = "count_raster"
    POPULATION_RASTER = "population_raster"
    BUILDING_POLYGONS = "building_polygons"
    UNKNOWN = "unknown"

    @property
    def label(self) -> str:
        return _OUTPUT_LABELS[self.value]

    @property
    def is_vector(self) -> bool:
        return self is OutputType.BUILDING_POLYGONS

    @property
    def is_raster(self) -> bool:
        return self not in (OutputType.BUILDING_POLYGONS, OutputType.UNKNOWN)


_OUTPUT_LABELS = {
    "rgb_raster": "RGB raster",
    "index_raster": "Index raster",
    "height_raster": "Height raster",
    "presence_raster": "Presence raster",
    "count_raster": "Count raster",
    "population_raster": "Population raster",
    "building_polygons": "Footprint polygons",
    "unknown": "To be confirmed",
}


@dataclass(frozen=True)
class OptionField:
    """One user-configurable option. kind: date_range|int|float|choice|multichoice|bool"""
    key: str
    label: str
    kind: str
    default: Any = None
    choices: Tuple[Tuple[Any, str], ...] = ()   # (value, label)
    minimum: float = 0
    maximum: float = 100
    suffix: str = ""
    help: str = ""
    depends_on: Optional[Tuple[str, Any]] = None  # (other_key, required_value)


@dataclass(frozen=True)
class DatasetSpec:
    id: str
    title: str
    category: Category
    provider: str
    access: str
    output_type: OutputType
    status: Status
    short: str
    description: str = ""
    coverage: str = ""
    licence: str = ""
    gee_ids: Tuple[str, ...] = ()
    formula: str = ""
    bands: str = ""
    options: Tuple[OptionField, ...] = ()
    notes: str = ""
    regional: bool = False
    native_scale_m: Optional[float] = None

    @property
    def search_blob(self) -> str:
        return " ".join(
            [self.title, self.provider, self.short, self.description,
             self.output_type.label, self.category.value]
        ).lower()


class Registry:
    def __init__(self, specs: Iterable[DatasetSpec]):
        self._specs: List[DatasetSpec] = list(specs)
        self._by_id = {s.id: s for s in self._specs}

    def all(self) -> List[DatasetSpec]:
        return list(self._specs)

    def get(self, spec_id: str) -> DatasetSpec:
        return self._by_id[spec_id]

    def by_category(self, category: Category) -> List[DatasetSpec]:
        return [s for s in self._specs if s.category == category]

    def ordered(self, ids: Iterable[str]) -> List[DatasetSpec]:
        wanted = set(ids)
        return [s for s in self._specs if s.id in wanted]


def compatibility_notes(specs: List[DatasetSpec]) -> List[str]:
    notes: List[str] = []
    if any(s.output_type.is_vector for s in specs) and any(s.output_type.is_raster for s in specs):
        notes.append("Rasters and building footprints are written as separate files in different formats.")
    for s in specs:
        if s.regional and s.coverage:
            notes.append(f"{s.title} has regional coverage ({s.coverage}). Check that your AOI falls inside it.")
    return notes