"""Regression tests for GitHub #1141 - "DCE Attribute form not refreshing values properly".

Metadata values on QRiS feature layers are exposed as expression (virtual) fields such as
``structure_type (metadata)``.  QGIS only evaluates those expressions when a feature is
fetched, and ``QgsVectorLayerCache`` (the cache behind ``QgsAttributeTableModel``) patches
only the single attribute that changed, so the virtual columns kept serving stale values
after a Save in the attribute table's form view until the user pressed Refresh.

The fix installs an ``attributeValueChanged`` hook (``refresh_attribute_table_cache``) that
emits ``QgsMapLayer::dataChanged`` - deferred with ``QTimer.singleShot(0, ...)`` so the
attribute table model is not reset from inside ``QgsAttributeForm::saveEdits()``.
"""

import unittest

from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer
from qgis.PyQt.QtCore import QCoreApplication

from ..src.QRiS.riverscapes_map_manager import METADATA_REFRESH_HOOK, RiverscapesMapManager
from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()

METADATA_FIELD = "metadata"
NOTES_FIELD = "notes"
EXPRESSION_FIELD = "structure_type (metadata)"
METADATA_A = '{"metadata": {"structure_type": "A"}}'
METADATA_B = '{"metadata": {"structure_type": "B"}}'

try:  # QgsVectorLayerCache has lived in qgis.core since QGIS 2.x, but guard anyway
    from qgis.core import QgsVectorLayerCache

    HAS_VECTOR_LAYER_CACHE = hasattr(QgsVectorLayerCache, "attributeValue")
except ImportError:  # pragma: no cover - only on exotic builds
    QgsVectorLayerCache = None
    HAS_VECTOR_LAYER_CACHE = False


class TestMetadataAttributeRefresh(unittest.TestCase):
    """Verify that editing the metadata JSON invalidates the attribute table caches."""

    def setUp(self):
        self.manager = RiverscapesMapManager("QRiS")
        self.layers = []

    def tearDown(self):
        for layer in self.layers:
            if layer.isEditable():
                layer.rollBack()

    # ---------------------------------------------------------------- helpers
    def _make_layer(self, metadata_value: str = METADATA_A) -> QgsVectorLayer:
        """Build an in-memory DCE-like layer with the metadata virtual fields installed."""
        layer = QgsVectorLayer(f"Point?crs=EPSG:4326&field={METADATA_FIELD}:string&field={NOTES_FIELD}:string", "dce_points", "memory")
        self.assertTrue(layer.isValid(), "in-memory test layer failed to initialise")
        self.layers.append(layer)

        # Attribute edits (and adding a feature) require an edit session.
        self.assertTrue(layer.startEditing(), "could not start editing on the memory layer")
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(0, 0)))
        feature[METADATA_FIELD] = metadata_value
        feature[NOTES_FIELD] = "initial"
        self.assertTrue(layer.addFeature(feature))
        self.assertTrue(layer.commitChanges())

        # Expression fields are added to the provider, so do this outside an edit session.
        self.manager.set_metadata_virtual_fields(layer)
        self.assertTrue(layer.startEditing(), "could not start editing before changing attributes")
        return layer

    def _first_fid(self, layer: QgsVectorLayer) -> int:
        features = list(layer.getFeatures())
        self.assertEqual(len(features), 1, "expected exactly one feature in the test layer")
        return features[0].id()

    def _expression_field_index(self, layer: QgsVectorLayer) -> int:
        index = layer.fields().indexFromName(EXPRESSION_FIELD)
        self.assertNotEqual(index, -1, f"'{EXPRESSION_FIELD}' expression field was not added by set_metadata_virtual_fields")
        return index

    def _expression_value(self, layer: QgsVectorLayer, fid: int, field_index: int) -> str:
        feature = layer.getFeature(fid)
        self.assertTrue(feature.isValid(), f"feature {fid} could not be fetched")
        return str(feature[field_index])

    def _spy_data_changed(self, layer: QgsVectorLayer) -> list:
        emissions = []

        def _record(*_args) -> None:
            emissions.append(True)

        layer.dataChanged.connect(_record)
        return emissions

    def _flush_events(self) -> None:
        """Drain deferred callbacks scheduled with ``QTimer.singleShot(0, ...)``."""
        QCoreApplication.processEvents()
        QCoreApplication.sendPostedEvents()
        QCoreApplication.processEvents()

    # ------------------------------------------------------------------ tests
    def test_metadata_change_refreshes_virtual_fields(self):
        """Editing the metadata JSON must surface the new value in the virtual column."""
        layer = self._make_layer()
        fid = self._first_fid(layer)
        metadata_idx = layer.fields().indexFromName(METADATA_FIELD)
        expression_idx = self._expression_field_index(layer)

        self.assertEqual(self._expression_value(layer, fid, expression_idx), "A")

        self.assertTrue(layer.changeAttributeValue(fid, metadata_idx, METADATA_B))
        self._flush_events()

        self.assertEqual(self._expression_value(layer, fid, expression_idx), "B", "metadata virtual field was not refreshed after the metadata JSON changed")

    def test_data_changed_emitted_only_for_metadata_field(self):
        """Only metadata edits invalidate the cache - other attribute edits stay silent."""
        layer = self._make_layer()
        fid = self._first_fid(layer)
        metadata_idx = layer.fields().indexFromName(METADATA_FIELD)
        notes_idx = layer.fields().indexFromName(NOTES_FIELD)
        emissions = self._spy_data_changed(layer)

        self.assertTrue(layer.changeAttributeValue(fid, notes_idx, "edited"))
        self._flush_events()
        self.assertEqual(len(emissions), 0, "dataChanged must not be emitted for non-metadata attribute edits")

        self.assertTrue(layer.changeAttributeValue(fid, metadata_idx, METADATA_B))
        self._flush_events()
        self.assertEqual(len(emissions), 1, "a single metadata edit must emit dataChanged exactly once")

    def test_hook_is_idempotent(self):
        """Re-running set_metadata_virtual_fields must not stack duplicate hooks.

        ``frm_dockwidget.py`` re-applies the metadata fields on layers that already have
        them, so a second call must not double-connect ``attributeValueChanged``.
        """
        layer = self._make_layer()
        self.manager.set_metadata_virtual_fields(layer)
        self.assertEqual(layer.customProperty(METADATA_REFRESH_HOOK), "1", "the refresh hook guard property was not set on the layer")

        fid = self._first_fid(layer)
        metadata_idx = layer.fields().indexFromName(METADATA_FIELD)
        emissions = self._spy_data_changed(layer)

        self.assertTrue(layer.changeAttributeValue(fid, metadata_idx, METADATA_B))
        self._flush_events()
        self.assertEqual(len(emissions), 1, "installing the metadata hook twice must still emit dataChanged exactly once")

    def test_refresh_attribute_table_cache_ignores_other_fields(self):
        """The slot itself must filter on the metadata column index."""
        layer = self._make_layer()
        fid = self._first_fid(layer)
        metadata_idx = layer.fields().indexFromName(METADATA_FIELD)
        notes_idx = layer.fields().indexFromName(NOTES_FIELD)
        emissions = self._spy_data_changed(layer)

        self.manager.refresh_attribute_table_cache(layer, metadata_idx, fid, notes_idx, "edited")
        self._flush_events()
        self.assertEqual(len(emissions), 0, "refresh_attribute_table_cache must ignore non-metadata fields")

        self.manager.refresh_attribute_table_cache(layer, metadata_idx, fid, metadata_idx, METADATA_B)
        self._flush_events()
        self.assertEqual(len(emissions), 1, "refresh_attribute_table_cache must emit dataChanged for the metadata field")

    @unittest.skipUnless(HAS_VECTOR_LAYER_CACHE, "QgsVectorLayerCache.attributeValue is not available in this QGIS build")
    def test_layer_cache_serves_fresh_virtual_value(self):
        """The real regression: a warmed QgsVectorLayerCache must not serve stale virtual values."""
        layer = self._make_layer()
        fid = self._first_fid(layer)
        metadata_idx = layer.fields().indexFromName(METADATA_FIELD)
        expression_idx = self._expression_field_index(layer)

        cache = QgsVectorLayerCache(layer, 1000)
        try:
            self.assertEqual(str(cache.attributeValue(fid, expression_idx)), "A")
        except TypeError:  # pragma: no cover - signature differs between QGIS versions
            self.skipTest("QgsVectorLayerCache.attributeValue has an unexpected signature in this QGIS version")

        self.assertTrue(layer.changeAttributeValue(fid, metadata_idx, METADATA_B))
        self._flush_events()

        self.assertEqual(str(cache.attributeValue(fid, expression_idx)), "B", "cached attribute table model would still show the stale metadata value")


if __name__ == "__main__":
    unittest.main()
