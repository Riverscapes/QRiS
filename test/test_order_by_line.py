# coding=utf-8
"""Regression tests for ordering features by centerline."""

import unittest
from unittest.mock import patch

try:
    from utilities import get_qgis_app
except ImportError:
    from .utilities import get_qgis_app


class TestOrderByLineTask(unittest.TestCase):
    """Validate centerline-based ordering for cross sections."""

    @classmethod
    def setUpClass(cls):
        cls.QGIS_APP, cls.CANVAS, cls.IFACE, cls.PARENT = get_qgis_app()
        global QgsField, QgsFeature, QgsGeometry, QgsVectorLayer
        global QgsProject, QgsCoordinateReferenceSystem
        from qgis.core import (QgsField, QgsFeature, QgsGeometry, QgsVectorLayer,
                               QgsProject, QgsCoordinateReferenceSystem)

        try:
            from src.gp.order_by_line_task import OrderByLineTask
        except ImportError:
            from src.gp.order_by_line_task import OrderByLineTask
        cls.OrderByLineTask = OrderByLineTask

    def setUp(self):
        # Mirror field conditions from user report: geographic layer CRS and
        # project CRS in EPSG:4326 so task projects to metric for sorting.
        QgsProject.instance().setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))

        self.layer = QgsVectorLayer(
            'LineString?crs=EPSG:4326&field=name:string&field=sequence:integer',
            'cross_section_features',
            'memory')
        self.assertTrue(self.layer.isValid())

        dp = self.layer.dataProvider()
        feats = []

        # Intentionally out-of-order insertion and mixed digitizing direction.
        specs = [
            ('xs_4', 'LINESTRING(2 3.5, -1 3.5)'),
            ('xs_1', 'LINESTRING(-1 0.5, 2 0.5)'),
            ('xs_3', 'LINESTRING(-1 2.5, 2 2.5)'),
            ('xs_2', 'LINESTRING(2 1.5, -1 1.5)'),
        ]

        for name, wkt in specs:
            f = QgsFeature(self.layer.fields())
            f['name'] = name
            f['sequence'] = None
            f.setGeometry(QgsGeometry.fromWkt(wkt))
            feats.append(f)

        ok, _ = dp.addFeatures(feats)
        self.assertTrue(ok)

        self.centerline_forward = QgsGeometry.fromWkt(
            'LINESTRING(0 0, 1 1, 0 2, 1 3, 0 4)')
        self.centerline_reverse = QgsGeometry.fromWkt(
            'LINESTRING(0 4, 1 3, 0 2, 1 1, 0 0)')

    def _sequence_by_name(self):
        return {
            f['name']: f['sequence']
            for f in self.layer.getFeatures()
        }

    def _build_sample_frame_layer(self):
        layer = QgsVectorLayer(
            'Polygon?crs=EPSG:4326&field=fid:integer&field=name:string&field=display_label:string&field=flows_into:integer&field=flow_path:string',
            'sample_frame_features',
            'memory')
        self.assertTrue(layer.isValid())

        dp = layer.dataProvider()
        feats = []
        specs = [
            ('sf_4', 404, 'POLYGON((-0.80 3.60, 1.20 3.60, 1.20 4.00, -0.80 4.00, -0.80 3.60))'),
            ('sf_1', 101, 'POLYGON((-0.80 0.00, 1.20 0.00, 1.20 1.00, -0.80 1.00, -0.80 0.00))'),
            ('sf_3', 303, 'POLYGON((-0.80 2.40, 1.20 2.40, 1.20 3.20, -0.80 3.20, -0.80 2.40))'),
            ('sf_2', 202, 'POLYGON((-0.80 1.20, 1.20 1.20, 1.20 2.20, -0.80 2.20, -0.80 1.20))'),
            ('sf_out', 909, 'POLYGON((3.00 2.00, 3.80 2.00, 3.80 2.80, 3.00 2.80, 3.00 2.00))'),
        ]

        for name, fid, wkt in specs:
            f = QgsFeature(layer.fields())
            f['fid'] = fid
            f['name'] = name
            f['display_label'] = None if name != 'sf_out' else '99'
            f['flows_into'] = None if name != 'sf_out' else 777
            f['flow_path'] = None if name != 'sf_out' else 'Existing Path'
            f.setGeometry(QgsGeometry.fromWkt(wkt))
            feats.append(f)

        ok, _ = dp.addFeatures(feats)
        self.assertTrue(ok)
        return layer

    def test_cross_sections_ordered_by_centerline_not_digitized_order(self):
        task = self.OrderByLineTask(
            layer_path='mock://cross_section_features',
            centerline=self.centerline_forward,
            label_field='sequence',
            chain_field=None)

        with patch('src.gp.order_by_line.QgsVectorLayer', return_value=self.layer):
            self.assertTrue(task.run(), msg=str(task.exception))

        seq = self._sequence_by_name()
        self.assertEqual(seq['xs_1'], 1)
        self.assertEqual(seq['xs_2'], 2)
        self.assertEqual(seq['xs_3'], 3)
        self.assertEqual(seq['xs_4'], 4)

    def test_reversing_centerline_reverses_sequence(self):
        task = self.OrderByLineTask(
            layer_path='mock://cross_section_features',
            centerline=self.centerline_reverse,
            label_field='sequence',
            chain_field=None)

        with patch('src.gp.order_by_line.QgsVectorLayer', return_value=self.layer):
            self.assertTrue(task.run(), msg=str(task.exception))

        seq = self._sequence_by_name()
        self.assertEqual(seq['xs_1'], 4)
        self.assertEqual(seq['xs_2'], 3)
        self.assertEqual(seq['xs_3'], 2)
        self.assertEqual(seq['xs_4'], 1)

    def test_epsg4326_meander_realistic_cross_section_ordering(self):
        # Use a separate layer with coordinates in the same lon/lat range as the
        # reported issue and intentionally mixed digitizing order/direction.
        layer = QgsVectorLayer(
            'LineString?crs=EPSG:4326&field=name:string&field=sequence:integer',
            'cross_section_features_realistic',
            'memory')
        self.assertTrue(layer.isValid())

        dp = layer.dataProvider()
        feats = []
        specs = [
            ('xs_d', 'LINESTRING(-111.34390 42.94055, -111.34235 42.94070)'),
            ('xs_a', 'LINESTRING(-111.34420 42.94325, -111.34225 42.94320)'),
            ('xs_c', 'LINESTRING(-111.34410 42.94180, -111.34225 42.94160)'),
            ('xs_b', 'LINESTRING(-111.34415 42.94255, -111.34230 42.94230)'),
        ]

        for name, wkt in specs:
            f = QgsFeature(layer.fields())
            f['name'] = name
            f['sequence'] = None
            f.setGeometry(QgsGeometry.fromWkt(wkt))
            feats.append(f)

        ok, _ = dp.addFeatures(feats)
        self.assertTrue(ok)

        centerline_forward = QgsGeometry.fromWkt(
            'LINESTRING('
            '-111.34395 42.94010, '
            '-111.34360 42.94065, '
            '-111.34315 42.94120, '
            '-111.34370 42.94175, '
            '-111.34305 42.94235, '
            '-111.34355 42.94295, '
            '-111.34295 42.94355)'
        )
        centerline_reverse = QgsGeometry.fromWkt(
            'LINESTRING('
            '-111.34295 42.94355, '
            '-111.34355 42.94295, '
            '-111.34305 42.94235, '
            '-111.34370 42.94175, '
            '-111.34315 42.94120, '
            '-111.34360 42.94065, '
            '-111.34395 42.94010)'
        )

        task = self.OrderByLineTask(
            layer_path='mock://cross_section_features_realistic',
            centerline=centerline_forward,
            label_field='sequence',
            chain_field=None)

        with patch('src.gp.order_by_line.QgsVectorLayer', return_value=layer):
            self.assertTrue(task.run(), msg=str(task.exception))

        seq_forward = {f['name']: f['sequence'] for f in layer.getFeatures()}
        self.assertEqual(seq_forward['xs_d'], 1, msg=str(seq_forward))
        self.assertEqual(seq_forward['xs_c'], 2, msg=str(seq_forward))
        self.assertEqual(seq_forward['xs_b'], 3, msg=str(seq_forward))
        self.assertEqual(seq_forward['xs_a'], 4, msg=str(seq_forward))

        task = self.OrderByLineTask(
            layer_path='mock://cross_section_features_realistic',
            centerline=centerline_reverse,
            label_field='sequence',
            chain_field=None)

        with patch('src.gp.order_by_line.QgsVectorLayer', return_value=layer):
            self.assertTrue(task.run(), msg=str(task.exception))

        seq_reverse = {f['name']: f['sequence'] for f in layer.getFeatures()}
        self.assertEqual(seq_reverse['xs_d'], 4, msg=str(seq_reverse))
        self.assertEqual(seq_reverse['xs_c'], 3, msg=str(seq_reverse))
        self.assertEqual(seq_reverse['xs_b'], 2, msg=str(seq_reverse))
        self.assertEqual(seq_reverse['xs_a'], 1, msg=str(seq_reverse))

    def test_sample_frames_order_and_flows_into_chain(self):
        layer = self._build_sample_frame_layer()

        task = self.OrderByLineTask(
            layer_path='mock://sample_frame_features',
            centerline=self.centerline_forward,
            label_field='display_label',
            chain_field='flows_into',
            flow_path_field='flow_path',
            flow_path_value='Centerline A',
            intersecting_only=True)

        with patch('src.gp.order_by_line.QgsVectorLayer', return_value=layer):
            self.assertTrue(task.run(), msg=str(task.exception))

        by_name = {f['name']: f for f in layer.getFeatures()}

        self.assertEqual(by_name['sf_1']['display_label'], '1')
        self.assertEqual(by_name['sf_2']['display_label'], '2')
        self.assertEqual(by_name['sf_3']['display_label'], '3')
        self.assertEqual(by_name['sf_4']['display_label'], '4')

        self.assertEqual(by_name['sf_1']['flows_into'], by_name['sf_2']['fid'])
        self.assertEqual(by_name['sf_2']['flows_into'], by_name['sf_3']['fid'])
        self.assertEqual(by_name['sf_3']['flows_into'], by_name['sf_4']['fid'])
        self.assertIsNone(by_name['sf_4']['flows_into'])
        self.assertEqual(by_name['sf_1']['flow_path'], 'Centerline A')
        self.assertEqual(by_name['sf_2']['flow_path'], 'Centerline A')
        self.assertEqual(by_name['sf_3']['flow_path'], 'Centerline A')
        self.assertEqual(by_name['sf_4']['flow_path'], 'Centerline A')

        # Non-intersecting polygon should remain unchanged.
        self.assertEqual(by_name['sf_out']['display_label'], '99')
        self.assertEqual(by_name['sf_out']['flows_into'], 777)
        self.assertEqual(by_name['sf_out']['flow_path'], 'Existing Path')

    def test_sample_frames_reverse_centerline_reverses_order_and_chain(self):
        layer = self._build_sample_frame_layer()

        task = self.OrderByLineTask(
            layer_path='mock://sample_frame_features',
            centerline=self.centerline_reverse,
            label_field='display_label',
            chain_field='flows_into',
            flow_path_field='flow_path',
            flow_path_value='Centerline B',
            intersecting_only=True)

        with patch('src.gp.order_by_line.QgsVectorLayer', return_value=layer):
            self.assertTrue(task.run(), msg=str(task.exception))

        by_name = {f['name']: f for f in layer.getFeatures()}

        self.assertEqual(by_name['sf_4']['display_label'], '1')
        self.assertEqual(by_name['sf_3']['display_label'], '2')
        self.assertEqual(by_name['sf_2']['display_label'], '3')
        self.assertEqual(by_name['sf_1']['display_label'], '4')

        self.assertEqual(by_name['sf_4']['flows_into'], by_name['sf_3']['fid'])
        self.assertEqual(by_name['sf_3']['flows_into'], by_name['sf_2']['fid'])
        self.assertEqual(by_name['sf_2']['flows_into'], by_name['sf_1']['fid'])
        self.assertIsNone(by_name['sf_1']['flows_into'])
        self.assertEqual(by_name['sf_4']['flow_path'], 'Centerline B')
        self.assertEqual(by_name['sf_3']['flow_path'], 'Centerline B')
        self.assertEqual(by_name['sf_2']['flow_path'], 'Centerline B')
        self.assertEqual(by_name['sf_1']['flow_path'], 'Centerline B')

        # Non-intersecting polygon should remain unchanged.
        self.assertEqual(by_name['sf_out']['display_label'], '99')
        self.assertEqual(by_name['sf_out']['flows_into'], 777)
        self.assertEqual(by_name['sf_out']['flow_path'], 'Existing Path')


if __name__ == '__main__':
    unittest.main()