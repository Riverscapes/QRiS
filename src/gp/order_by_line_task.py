from qgis.PyQt.QtCore import QMetaType, pyqtSignal
from qgis.core import (QgsTask, QgsMessageLog, Qgis, QgsVectorLayer, QgsGeometry,
                       QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject,
                       QgsWkbTypes, QgsPointXY)


MESSAGE_CATEGORY = 'OrderByLineTask'


class OrderByLineTask(QgsTask):
    """
    Sorts features in a vector layer by their centroid's projected distance
    along a centerline, then writes a 1-indexed label field and an optional
    chain field (e.g. flows_into) back to the layer.

    Reusable for sample_frame_features, cross_section_features, or any layer
    whose features need to be ordered relative to a line geometry.

    Parameters
    ----------
    layer_path : str
        Data source path accepted by QgsVectorLayer (e.g. 'path.gpkg|layername=foo').
    centerline : QgsGeometry
        Line geometry used as the ordering reference. Must be in the same CRS
        as the features in layer_path.
    filter_expression : str, optional
        Subset filter applied to the layer before reading features
        (e.g. 'sample_frame_id = 5').
    label_field : str
        Field to write the 1-indexed sort position into. Default 'display_label'.
    chain_field : str, optional
        Field to write the next feature's FID into (NULL for the last feature).
        Omit for layers that have no topology chain (e.g. cross sections).
    """

    order_complete = pyqtSignal(bool)

    def __init__(self, layer_path: str, centerline: QgsGeometry,
                 filter_expression: str = None,
                 label_field: str = 'display_label',
                 chain_field: str = None,
                 secondary_label_field: str = None,
                 flow_path_field: str = None,
                 flow_path_value: str = None,
                 intersecting_only: bool = False) -> None:
        super().__init__('Order Features by Line Task', QgsTask.CanCancel)

        self.layer_path = layer_path
        self.centerline = centerline
        self.filter_expression = filter_expression
        self.label_field = label_field
        self.chain_field = chain_field
        self.secondary_label_field = secondary_label_field
        self.flow_path_field = flow_path_field
        self.flow_path_value = flow_path_value
        self.intersecting_only = intersecting_only
        self.exception = None

    def run(self):

        try:
            layer = QgsVectorLayer(self.layer_path)
            if self.filter_expression:
                if not layer.setSubsetString(self.filter_expression):
                    raise Exception(f'Filter expression failed to apply: {self.filter_expression}')

            all_features = list(layer.getFeatures())
            if not all_features:
                QgsMessageLog.logMessage(
                    f'OrderByLineTask: no features found (filter: {self.filter_expression})',
                    MESSAGE_CATEGORY, Qgis.Warning)
                return True

            # Reproject to a metric CRS for lineLocatePoint so the distance
            # calculation is in metres, not degrees (EPSG:4326 data would produce
            # distorted Euclidean distances in degree-space).
            source_crs = layer.crs()
            proj_crs = QgsProject.instance().crs()
            target_crs = proj_crs if not proj_crs.isGeographic() \
                else QgsCoordinateReferenceSystem('EPSG:3857')

            if source_crs.authid() != target_crs.authid():
                transform = QgsCoordinateTransform(
                    source_crs, target_crs, QgsProject.instance())
                cl_projected = QgsGeometry(self.centerline)
                cl_projected.transform(transform)
                QgsMessageLog.logMessage(
                    f'OrderByLineTask: reprojecting from {source_crs.authid()} '
                    f'to {target_crs.authid()} for distance calculation',
                    MESSAGE_CATEGORY, Qgis.Info)
            else:
                transform = None
                cl_projected = self.centerline

            # Guard against null/empty geometries.
            # Use intersection-based ordering: find where the centerline actually
            # enters each polygon (the upstream boundary) rather than the centroid,
            # which can project to the wrong segment around meanders.
            bad_fids = []

            def _collect_intersection_points(geom: QgsGeometry):
                if geom is None or geom.isNull() or geom.isEmpty():
                    return []

                points = []
                geom_type = QgsWkbTypes.geometryType(geom.wkbType())

                if geom_type == QgsWkbTypes.PointGeometry:
                    if geom.isMultipart():
                        points.extend(geom.asMultiPoint())
                    else:
                        points.append(geom.asPoint())
                elif geom_type == QgsWkbTypes.LineGeometry:
                    if geom.isMultipart():
                        for ln in geom.asMultiPolyline():
                            if len(ln) >= 2:
                                points.extend((ln[0], ln[-1]))
                            elif len(ln) == 1:
                                points.append(ln[0])
                    else:
                        ln = geom.asPolyline()
                        if len(ln) >= 2:
                            points.extend((ln[0], ln[-1]))
                        elif len(ln) == 1:
                            points.append(ln[0])
                else:
                    # Geometry collections can contain mixed point/line parts.
                    for part in geom.asGeometryCollection():
                        points.extend(_collect_intersection_points(part))

                return points

            def _sort_key(f):
                geom = f.geometry()
                if geom is None or geom.isNull() or geom.isEmpty():
                    bad_fids.append(f.id())
                    return float('inf')
                proj_geom = QgsGeometry(geom)
                if transform is not None:
                    proj_geom.transform(transform)
                # Primary: minimum lineLocatePoint distance among the endpoints of
                # the centerline-polygon intersection (= upstream entry point).
                # Only endpoints are checked — the minimum for a line is always
                # at an endpoint, avoiding expensive per-vertex iteration.
                intersection = cl_projected.intersection(proj_geom)
                if intersection and not intersection.isEmpty():
                    min_dist = float('inf')
                    points = _collect_intersection_points(intersection)
                    for pt in points:
                        d = cl_projected.lineLocatePoint(QgsGeometry.fromPointXY(QgsPointXY(pt)))
                        if d >= 0 and d < min_dist:
                            min_dist = d
                    if min_dist < float('inf'):
                        return min_dist

                # Fallback: nearest point along centerline to the feature geometry.
                nearest_on_line = cl_projected.nearestPoint(proj_geom)
                if nearest_on_line and not nearest_on_line.isEmpty():
                    d = cl_projected.lineLocatePoint(nearest_on_line)
                    if d >= 0:
                        return d

                bad_fids.append(f.id())
                return float('inf')

            features = all_features
            if self.intersecting_only:
                intersecting_features = []
                skipped_features = []
                for f in all_features:
                    geom = f.geometry()
                    if geom is None or geom.isNull() or geom.isEmpty():
                        skipped_features.append(f.id())
                        continue

                    proj_geom = QgsGeometry(geom)
                    if transform is not None:
                        proj_geom.transform(transform)

                    intersection = cl_projected.intersection(proj_geom)
                    if intersection and not intersection.isEmpty():
                        intersecting_features.append(f)
                    else:
                        skipped_features.append(f.id())

                features = intersecting_features

                if skipped_features:
                    QgsMessageLog.logMessage(
                        f'OrderByLineTask: skipped {len(skipped_features)} non-intersecting feature(s). '
                        f'FIDs: {skipped_features}',
                        MESSAGE_CATEGORY, Qgis.Info)

                if not features:
                    QgsMessageLog.logMessage(
                        'OrderByLineTask: no intersecting features found; no attributes updated.',
                        MESSAGE_CATEGORY, Qgis.Warning)
                    return True

            features.sort(key=_sort_key)

            if bad_fids:
                QgsMessageLog.logMessage(
                    f'OrderByLineTask: {len(bad_fids)} feature(s) had null/empty geometry '
                    f'and were placed at the end. FIDs: {bad_fids}',
                    MESSAGE_CATEGORY, Qgis.Warning)

            QgsMessageLog.logMessage(
                f'OrderByLineTask: ordering {len(features)} features '
                f'(filter: {self.filter_expression})',
                MESSAGE_CATEGORY, Qgis.Info)

            label_idx = layer.fields().indexOf(self.label_field) if self.label_field else -1
            chain_idx = layer.fields().indexOf(self.chain_field) if self.chain_field else -1
            secondary_idx = layer.fields().indexOf(self.secondary_label_field) if self.secondary_label_field else -1
            flow_path_idx = layer.fields().indexOf(self.flow_path_field) if self.flow_path_field else -1
            fid_field_idx = layer.fields().indexOf('fid')
            label_is_int = (label_idx >= 0 and
                            layer.fields().field(label_idx).type() in
                            (QMetaType.Int, QMetaType.LongLong, QMetaType.UInt, QMetaType.ULongLong))

            def _feature_chain_id(feature):
                if fid_field_idx >= 0:
                    fid_value = feature[fid_field_idx]
                    if fid_value is not None and fid_value != '':
                        return int(fid_value)
                return int(feature.id())

            attr_map = {}
            for i, feat in enumerate(features):
                attrs = {}
                if label_idx >= 0:
                    attrs[label_idx] = i + 1 if label_is_int else str(i + 1)
                if secondary_idx >= 0:
                    attrs[secondary_idx] = str(i + 1)
                if chain_idx >= 0:
                    attrs[chain_idx] = _feature_chain_id(features[i + 1]) if i < len(features) - 1 else None
                if flow_path_idx >= 0 and self.flow_path_value is not None:
                    attrs[flow_path_idx] = self.flow_path_value
                if attrs:
                    attr_map[feat.id()] = attrs

            if not layer.dataProvider().changeAttributeValues(attr_map):
                raise Exception('changeAttributeValues returned False — attribute update may be incomplete.')

            return True

        except Exception as ex:
            self.exception = ex
            return False

    def finished(self, result):
        if result:
            QgsMessageLog.logMessage(
                'Order by Line Task completed',
                MESSAGE_CATEGORY, Qgis.Success)
        else:
            if self.exception is None:
                QgsMessageLog.logMessage(
                    'Order by Line Task not successful but without exception '
                    '(probably the task was manually canceled by the user)',
                    MESSAGE_CATEGORY, Qgis.Warning)
            else:
                QgsMessageLog.logMessage(
                    f'Order by Line Task exception: {self.exception}',
                    MESSAGE_CATEGORY, Qgis.Critical)
                raise self.exception

        self.order_complete.emit(result)

    def cancel(self):
        QgsMessageLog.logMessage(
            'Order by Line Task was canceled',
            MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
