from collections.abc import Iterable
from typing import Optional

from qgis import processing
from qgis.core import QgsVectorLayer


def build_aoi_centroids_layer(project_file: str, aoi_ids: Iterable[int], layer_name: str = "AOI Centroids") -> Optional[QgsVectorLayer]:
    """Build a temporary centroid layer for all AOI features in the project."""

    aoi_ids = [int(aoi_id) for aoi_id in aoi_ids]
    if len(aoi_ids) == 0:
        return None

    where_clause = ",".join(str(aoi_id) for aoi_id in aoi_ids)
    source_uri = f"{project_file}|layername=sample_frame_features|subset=sample_frame_id IN ({where_clause})"
    source_layer = QgsVectorLayer(source_uri, "AOI Features", "ogr")
    if not source_layer.isValid() or source_layer.featureCount() == 0:
        return None

    result = processing.run("native:dissolve", {"INPUT": source_layer, "FIELD": [], "SEPARATE_DISJOINT": False, "OUTPUT": "TEMPORARY_OUTPUT"})

    result = processing.run("native:centroids", {"INPUT": result["OUTPUT"], "ALL_PARTS": False, "OUTPUT": "TEMPORARY_OUTPUT"})

    output = result.get("OUTPUT")
    if isinstance(output, QgsVectorLayer):
        centroid_layer = output
    else:
        centroid_layer = QgsVectorLayer(str(output), layer_name, "ogr")

    if not centroid_layer.isValid():
        return None

    centroid_layer.setName(layer_name)
    return centroid_layer
