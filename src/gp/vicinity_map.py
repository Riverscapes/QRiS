import os
from typing import Tuple, List

from qgis.core import QgsTask, QgsMessageLog, Qgis, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsProject, QgsVectorLayer, QgsGeometry, QgsPointXY, QgsFeature, QgsMarkerSymbol, QgsFillSymbol, QgsField, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsTextBufferSettings, QgsMapSettings, QgsMapRendererCustomPainterJob, QgsMapLayer
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QSize, QRect
from qgis.PyQt.QtGui import QColor, QImage, QPainter
from qgis.PyQt.QtSvg import QSvgGenerator

from .map_centroid import build_aoi_centroids_layer
from ..QRiS.settings import Settings

MESSAGE_CATEGORY = 'QRiS'

class VicinityMapExportTask(QgsTask):
    """
    Async task for generating and exporting a vicinity map image.
    """

    # Signal to notify when done (success, output_path, error)
    on_complete = pyqtSignal(bool, str, object)

    def __init__(self, output_path, qris_project, render_params=None):
        super().__init__('Vicinity Map Export', QgsTask.CanCancel)
        self.output_path = output_path
        self.qris_project = qris_project
        self.render_params = render_params or {}
        self.exception = None

    def run(self):
        """
        Perform the map rendering and export.
        """
        try:
            centroid_point = self._resolve_centroid_point_wgs84()
            region_label, region_geometry = self._resolve_intersecting_state(centroid_point)
            if region_geometry is None:
                return False

            region_layer = self._build_region_render_layer(region_geometry, region_label)
            centroid_render_layer = self._build_centroid_render_layer(centroid_point)
            # Keep centroid first so it renders above the region polygon in map settings layer order.
            render_layers = [centroid_render_layer, region_layer]
            map_settings = self._build_map_settings(render_layers, region_geometry)
            return self._export_map(map_settings)
        except Exception as ex:
            self.exception = ex
            return False

    def _resolve_centroid_point_wgs84(self) -> QgsPointXY:
        """Build centroid from AOIs, then valley bottoms, then sample frames; return first point in EPSG:4326."""
        centroid_layer = None
        source_label = None
        attempted_sources = []

        centroid_sources = [
            ('AOI', list(self.qris_project.aois.keys())),
            ('Valley Bottom', list(self.qris_project.valley_bottoms.keys())),
            ('Sample Frame', list(self.qris_project.sample_frames.keys())),
        ]

        for label, source_ids in centroid_sources:
            if len(source_ids) == 0:
                continue

            attempted_sources.append(label)
            layer = build_aoi_centroids_layer(
                self.qris_project.project_file,
                source_ids,
                layer_name=f'{label} Centroids'
            )
            if layer is None or layer.featureCount() == 0:
                continue

            centroid_layer = layer
            source_label = label
            break

        if centroid_layer is None:
            if len(attempted_sources) == 0:
                raise Exception('Cannot generate vicinity map centroid: no AOI, valley bottom, or sample frame polygons are available.')
            raise Exception(
                'Cannot generate vicinity map centroid: available geometry sources did not contain valid polygon features '
                f'({", ".join(attempted_sources)}).'
            )

        centroid_point = None
        for feature in centroid_layer.getFeatures():
            geom = feature.geometry()
            if geom is not None and not geom.isEmpty():
                centroid_point = geom.asPoint()
                break

        if centroid_point is None:
            raise Exception(f'{source_label} centroid layer did not contain a valid point geometry.')

        centroid_crs = centroid_layer.crs()
        if not centroid_crs.isValid():
            raise Exception('AOI centroid layer has invalid CRS.')

        if centroid_crs.authid() == 'EPSG:4326':
            return centroid_point

        transform = QgsCoordinateTransform(
            centroid_crs,
            QgsCoordinateReferenceSystem('EPSG:4326'),
            QgsProject.instance().transformContext()
        )
        return transform.transform(centroid_point)

    def _resolve_intersecting_state(self, centroid_point_wgs84: QgsPointXY) -> Tuple[str, QgsGeometry]:
        """Return (region_label, region_geometry) for the region containing the centroid point, or (None, None) if not found."""
        states_path = Settings().resource_path('us_states_simplified.geojson')
        states_layer = QgsVectorLayer(states_path, "states", "ogr")
        if not states_layer.isValid():
            raise Exception('Could not load states layer from us_states_simplified.geojson.')

        point_in_layer_crs = QgsPointXY(centroid_point_wgs84.x(), centroid_point_wgs84.y())
        states_crs = states_layer.crs()
        wgs84 = QgsCoordinateReferenceSystem('EPSG:4326')
        if states_crs.isValid() and states_crs != wgs84:
            to_states = QgsCoordinateTransform(
                wgs84,
                states_crs,
                QgsProject.instance().transformContext()
            )
            point_in_layer_crs = to_states.transform(point_in_layer_crs)

        point_geom = QgsGeometry.fromPointXY(point_in_layer_crs)

        states_layer.selectByRect(point_geom.boundingBox())
        for state_feature in states_layer.selectedFeatures():
            state_geom = state_feature.geometry()
            if state_geom is None or state_geom.isEmpty() or not state_geom.intersects(point_geom):
                continue

            state_name = self._extract_region_label(state_feature)

            result_geom = QgsGeometry(state_geom)
            if states_crs.isValid() and states_crs != wgs84:
                to_wgs84 = QgsCoordinateTransform(
                    states_crs,
                    wgs84,
                    QgsProject.instance().transformContext()
                )
                result_geom.transform(to_wgs84)

            return state_name, result_geom

        self.exception = Exception(
            "Project location is outside supported regions. Cannot generate vicinity map. "
            "(No containing state found for centroid.)"
        )
        return None, None

    def _build_region_render_layer(self, region_geometry: QgsGeometry, region_label: str) -> QgsVectorLayer:
        """Build an in-memory region polygon layer with light gray fill and thick black border."""
        if region_geometry is None or region_geometry.isEmpty():
            raise Exception('Region geometry is not available for render layer creation.')

        region_layer = QgsVectorLayer('Polygon?crs=EPSG:4326', 'Selected Region', 'memory')
        if not region_layer.isValid():
            raise Exception('Could not create region render layer.')

        provider = region_layer.dataProvider()
        provider.addAttributes([QgsField('label_text', QVariant.String)])
        region_layer.updateFields()

        feature = QgsFeature(region_layer.fields())
        feature.setGeometry(QgsGeometry(region_geometry))
        feature['label_text'] = region_label or 'Selected Region'
        provider.addFeature(feature)
        region_layer.updateExtents()

        symbol = QgsFillSymbol.createSimple({
            'color': '240,240,240,185',
            'outline_color': '0,0,0,255',
            'outline_width': '1.4'
        })
        region_layer.renderer().setSymbol(symbol)

        label_settings = QgsPalLayerSettings()
        label_settings.enabled = True
        label_settings.fieldName = 'label_text'
        # TEMP (QGIS 3.28 support): remove this compatibility path when all clients are on newer QGIS.
        self._set_label_placement(label_settings, modern='Horizontal', legacy='Horizontal')

        text_format = QgsTextFormat()
        text_format.setSize(11)
        text_format.setColor(QColor(0, 0, 0))
        text_buffer = QgsTextBufferSettings()
        text_buffer.setEnabled(True)
        text_buffer.setSize(0.8)
        text_buffer.setColor(QColor(255, 255, 255))
        text_format.setBuffer(text_buffer)
        label_settings.setFormat(text_format)

        region_layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        region_layer.setLabelsEnabled(True)
        return region_layer

    def _build_centroid_render_layer(self, centroid_point: QgsPointXY) -> QgsVectorLayer:
        centroid_layer = QgsVectorLayer('Point?crs=EPSG:4326', 'Centroid', 'memory')
        if not centroid_layer.isValid():
            raise Exception('Could not create centroid render layer.')

        provider = centroid_layer.dataProvider()
        provider.addAttributes([QgsField('label_text', QVariant.String)])
        centroid_layer.updateFields()

        feature = QgsFeature(centroid_layer.fields())
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(centroid_point.x(), centroid_point.y())))
        feature['label_text'] = 'Project Location'
        provider.addFeature(feature)
        centroid_layer.updateExtents()

        symbol = QgsMarkerSymbol.createSimple({
            'name': 'star',
            'color': '0,0,0',
            'outline_color': '0,0,0',
            'outline_width': '0.4',
            'size': '5'
        })
        centroid_layer.renderer().setSymbol(symbol)

        label_settings = QgsPalLayerSettings()
        label_settings.enabled = True
        label_settings.fieldName = 'label_text'
        self._set_label_placement(label_settings, modern='AroundPoint', legacy='OverPoint')
        label_settings.dist = 2.0

        text_format = QgsTextFormat()
        text_format.setSize(10)
        text_format.setColor(QColor(0, 0, 0))
        text_buffer = QgsTextBufferSettings()
        text_buffer.setEnabled(True)
        text_buffer.setSize(0.8)
        text_buffer.setColor(QColor(255, 255, 255))
        text_format.setBuffer(text_buffer)
        label_settings.setFormat(text_format)

        centroid_layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        centroid_layer.setLabelsEnabled(True)
        return centroid_layer

    @staticmethod
    def _set_label_placement(label_settings: QgsPalLayerSettings, modern: str, legacy: str):
        """Set label placement with compatibility across QGIS API versions."""
        # TEMP (QGIS 3.28 support): remove legacy fallback once 3.28 is no longer supported.
        if hasattr(Qgis, 'LabelPlacement') and hasattr(Qgis.LabelPlacement, modern):
            label_settings.placement = getattr(Qgis.LabelPlacement, modern)
            return

        if hasattr(QgsPalLayerSettings, legacy):
            label_settings.placement = getattr(QgsPalLayerSettings, legacy)
            return

        raise Exception(f'Unsupported label placement: modern={modern}, legacy={legacy}')

    @staticmethod
    def _extract_region_label(feature: QgsFeature) -> str:
        """Extract the best available region label from a feature using case-insensitive field matching."""
        fields = feature.fields()
        field_name_map = {name.lower(): name for name in fields.names()}

        preferred_fields = ['state_name', 'name', 'state', 'province', 'region']
        for candidate in preferred_fields:
            actual_name = field_name_map.get(candidate)
            if not actual_name:
                continue

            value = feature[actual_name]
            text = str(value).strip() if value is not None else ''
            if text and any(ch.isalpha() for ch in text):
                return text

        # Fallback: first non-empty, non-ID-like text field value that contains letters.
        disallowed_field_names = {'fid', 'id', 'objectid', 'oid', 'gid', 'pk'}
        for field in fields:
            field_name = field.name().strip().lower()
            if field_name in disallowed_field_names or field_name.endswith('_id') or field_name.endswith('id'):
                continue

            value = feature[field.name()]
            text = str(value).strip() if value is not None else ''
            if text and text.lower() != 'none' and any(ch.isalpha() for ch in text):
                return text

        return 'Selected Region'

    def _build_map_settings(self, render_layers: List[QgsMapLayer], region_geometry: QgsGeometry) -> QgsMapSettings:
        """Create QgsMapSettings (CRS, extent, output size, dpi, antialiasing)."""
        if not render_layers:
            raise Exception('No render layers were provided for map settings.')
        if region_geometry is None or region_geometry.isEmpty():
            raise Exception('Region geometry is required to define map extent.')

        width = int(self.render_params.get('width', 1600))
        height = int(self.render_params.get('height', 1200))
        dpi = int(self.render_params.get('dpi', 300))
        padding_ratio = float(self.render_params.get('padding_ratio', 0.08))

        # Use the region outline as the source extent.
        extent = region_geometry.boundingBox()

        # Pad extent so labels and symbols are not clipped.
        pad_x = extent.width() * padding_ratio
        pad_y = extent.height() * padding_ratio
        if extent.width() == 0:
            pad_x = 0.1
        if extent.height() == 0:
            pad_y = 0.1

        extent.setXMinimum(extent.xMinimum() - pad_x)
        extent.setYMinimum(extent.yMinimum() - pad_y)
        extent.setXMaximum(extent.xMaximum() + pad_x)
        extent.setYMaximum(extent.yMaximum() + pad_y)

        map_settings = QgsMapSettings()
        map_settings.setLayers(render_layers)
        map_settings.setDestinationCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
        map_settings.setExtent(extent)
        map_settings.setOutputSize(QSize(width, height))
        map_settings.setOutputDpi(dpi)
        map_settings.setBackgroundColor(QColor(255, 255, 255))
        map_settings.setFlag(QgsMapSettings.Antialiasing, True)

        return map_settings

    def _detect_output_format(self) -> str:
        """Infer export format from file extension."""
        _, ext = os.path.splitext(self.output_path)
        ext = ext.lower().strip()
        if ext == '.svg':
            return 'svg'
        return 'png'

    def _export_map(self, map_settings: QgsMapSettings) -> bool:
        """Export map using one shared rendering path for PNG/SVG."""
        if map_settings is None:
            raise Exception('Map settings are required for export.')

        output_format = self._detect_output_format()
        output_size = map_settings.outputSize()

        if output_format == 'svg':
            paint_device = QSvgGenerator()
            paint_device.setFileName(self.output_path)
            paint_device.setSize(output_size)
            paint_device.setViewBox(QRect(0, 0, output_size.width(), output_size.height()))
            paint_device.setTitle('QRiS Vicinity Map')
        else:
            paint_device = QImage(output_size, QImage.Format_ARGB32_Premultiplied)
            paint_device.fill(QColor(255, 255, 255))

        painter = QPainter(paint_device)
        try:
            job = QgsMapRendererCustomPainterJob(map_settings, painter)
            job.start()
            job.waitForFinished()
        finally:
            painter.end()

        if output_format == 'svg':
            save_ok = os.path.exists(self.output_path) and os.path.getsize(self.output_path) > 0
        else:
            save_ok = paint_device.save(self.output_path, 'PNG')

        if not save_ok:
            raise Exception(f'Failed to save {output_format.upper()} export to: {self.output_path}')

        return True

    def finished(self, result: bool):
        """
        Called in the main thread after run() completes.
        """
        if result:
            QgsMessageLog.logMessage('Vicinity map export complete', MESSAGE_CATEGORY, Qgis.Success)
        else:
            QgsMessageLog.logMessage(f'Vicinity map export failed: {self.exception}', MESSAGE_CATEGORY, Qgis.Critical)
        self.on_complete.emit(result, self.output_path, self.exception)

    def cancel(self):
        QgsMessageLog.logMessage('Vicinity map export was canceled', MESSAGE_CATEGORY, Qgis.Info)
        super().cancel()
