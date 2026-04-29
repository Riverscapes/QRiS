"""Tests for protocol metric dependency policy validation."""

import os
import sys
import tempfile
import unittest

try:
    from utilities import get_qgis_app
except ImportError:
    from .utilities import get_qgis_app

get_qgis_app()

current_dir = os.path.dirname(os.path.abspath(__file__))
plugin_root = os.path.dirname(current_dir)
parent_root = os.path.dirname(plugin_root)

if parent_root not in sys.path:
    sys.path.insert(0, parent_root)

from qris_dev.src.QRiS.protocol_parser import (  # noqa: E402
    MetricDefinition,
    ProtocolDefinition,
    load_protocool_from_xml,
)
from qris_dev.src.model.project import (  # noqa: E402
    INTRINSIC_SYSTEM_PROTOCOL_MACHINE_CODE,
    validate_protocol_metric_dependencies,
)


def build_metric(metric_id, dependencies=None):
    return MetricDefinition(
        id=metric_id,
        version='1.0',
        calculation_machine_code='count',
        label=metric_id,
        default_level='Metric',
        parameters={'metric_dependencies': dependencies} if dependencies else None,
    )


def build_protocol(machine_code, status='production', protocol_type='dce', metrics=None):
    return ProtocolDefinition(
        machine_code=machine_code,
        protocol_type=protocol_type,
        version='1.0',
        status=status,
        label=machine_code,
        description='desc',
        url='https://example.com',
        citation='cite',
        author='author',
        creation_date='2026-01-01',
        updated_date='2026-01-01',
        metrics=metrics or [],
    )


class TestProtocolDependencyValidation(unittest.TestCase):

    def test_same_protocol_dependency_allowed(self):
        metric = build_metric('m2', [{'metric_id_ref': 'm1'}])
        protocol = build_protocol('USER_A', metrics=[metric])

        errors = validate_protocol_metric_dependencies([protocol])
        self.assertEqual(errors, [])

    def test_user_to_intrinsic_dependency_allowed(self):
        metric = build_metric('m2', [{
            'metric_id_ref': 'intrinsic_length',
            'protocol_machine_code_ref': INTRINSIC_SYSTEM_PROTOCOL_MACHINE_CODE,
        }])
        protocol = build_protocol('USER_A', metrics=[metric])

        errors = validate_protocol_metric_dependencies([protocol])
        self.assertEqual(errors, [])

    def test_cross_user_protocol_dependency_blocked(self):
        metric = build_metric('m2', [{
            'metric_id_ref': 'm1',
            'protocol_machine_code_ref': 'USER_B',
        }])
        protocol = build_protocol('USER_A', metrics=[metric])

        errors = validate_protocol_metric_dependencies([protocol])
        self.assertEqual(len(errors), 1)
        self.assertIn('cross-user-protocol', errors[0])

    def test_system_protocol_cannot_reference_user_protocol(self):
        metric = build_metric('sys_metric', [{
            'metric_id_ref': 'm1',
            'protocol_machine_code_ref': 'USER_A',
        }])
        protocol = build_protocol(
            INTRINSIC_SYSTEM_PROTOCOL_MACHINE_CODE,
            status='production',
            protocol_type='system',
            metrics=[metric],
        )

        errors = validate_protocol_metric_dependencies([protocol])
        self.assertEqual(len(errors), 1)
        self.assertIn('cannot reference user protocol', errors[0])

    def test_multiple_system_protocols_blocked(self):
        p1 = build_protocol(INTRINSIC_SYSTEM_PROTOCOL_MACHINE_CODE, status='production', protocol_type='system')
        p2 = build_protocol('OTHER_SYSTEM', status='production', protocol_type='system')

        errors = validate_protocol_metric_dependencies([p1, p2])
        self.assertEqual(len(errors), 1)
        self.assertIn('Only one system protocol is supported', errors[0])

    def test_parser_reads_metric_dependencies(self):
        xml = """
<Protocol machine_code=\"USER_A\" protocol_type=\"dce\" version=\"1.0\" status=\"production\">
  <Label>User A</Label>
  <Description>desc</Description>
  <URL>https://example.com</URL>
  <Citation>cite</Citation>
  <Author>author</Author>
  <CreationDate>2026-01-01</CreationDate>
  <UpdatedDate>2026-01-01</UpdatedDate>
  <Layers></Layers>
  <Metrics>
    <Metric id=\"m2\" version=\"1.0\" calculation_machine_code=\"count\">
      <Label>M2</Label>
      <DefaultLevel>Metric</DefaultLevel>
      <Parameters>
        <MetricDependency metric_id_ref=\"m1\" protocol_machine_code_ref=\"USER_A\" usage=\"derived\" version=\"1.0\" />
      </Parameters>
    </Metric>
  </Metrics>
</Protocol>
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp:
            tmp.write(xml)
            tmp_path = tmp.name

        try:
            protocol = load_protocool_from_xml(tmp_path)
            self.assertIsNotNone(protocol)
            self.assertEqual(len(protocol.metrics), 1)
            params = protocol.metrics[0].parameters
            self.assertIn('metric_dependencies', params)
            self.assertEqual(params['metric_dependencies'][0]['metric_id_ref'], 'm1')
            self.assertEqual(params['metric_dependencies'][0]['protocol_machine_code_ref'], 'USER_A')
        finally:
            os.remove(tmp_path)

    def test_system_protocol_xml_parses_and_validates(self):
        protocol_path = os.path.join(
            plugin_root,
            'resources',
            'protocols',
            'riverscape_system_protocol.xml',
        )

        self.assertTrue(os.path.exists(protocol_path), f"Missing protocol file: {protocol_path}")

        protocol = load_protocool_from_xml(protocol_path)
        self.assertIsNotNone(protocol)
        self.assertEqual(protocol.machine_code, INTRINSIC_SYSTEM_PROTOCOL_MACHINE_CODE)
        self.assertEqual(protocol.protocol_type, 'system')
        self.assertEqual(protocol.status, 'production')
        self.assertGreaterEqual(len(protocol.metrics), 1)

        errors = validate_protocol_metric_dependencies([protocol])
        self.assertEqual(errors, [], f"Unexpected dependency validation errors: {errors}")


if __name__ == '__main__':
    unittest.main()
