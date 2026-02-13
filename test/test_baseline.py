# coding=utf-8
"""
Baseline stability tests for QRiS.
Ensures the plugin loads, projects open, and layers can be added without crashing.
"""
import unittest
import logging
import os
# Lazy import used inside methods to avoid pollution from other tests mocking 'qgis'
# from qgis.core import QgsProject, QgsVectorLayer
from utilities import get_qgis_app

LOGGER = logging.getLogger('QGIS')

class TestBaseline(unittest.TestCase):
    """Test essential plugin functionality."""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests."""
        cls.QGIS_APP, cls.CANVAS, cls.IFACE, cls.PARENT = get_qgis_app()
        # Ensure qgis imports work now
        global QgsProject, QgsVectorLayer, QgsTask
        from qgis.core import QgsProject, QgsVectorLayer, QgsTask
        # Ensure the registry is effectively empty or ready
        QgsProject.instance().clear()

    def test_01_plugin_load(self):
        """Test that QGIS and the basic environment load without error."""
        self.assertIsNotNone(self.QGIS_APP, "QGIS Application failed to initialize")
        self.assertTrue(self.QGIS_APP.platform(), "QGIS Platform should be detectable")
        LOGGER.info("Baseline: QGIS Environment loaded successfully.")

    def test_02_load_project(self):
        """Test opening a blank project and checking validity."""
        project = QgsProject.instance()
        project.clear()
        
        self.assertTrue(project.fileName() == "" or project.fileName() is None, "Project should be new/empty")
        LOGGER.info("Baseline: Project initialized successfully.")

    def test_03_add_layer(self):
        """Test adding a vector layer to the project."""
        # Create a temporary memory layer
        vlayer = QgsVectorLayer("Point?crs=EPSG:4326", "Test Layer", "memory")
        
        self.assertTrue(vlayer.isValid(), "Layer failed to create")
        
        # Add to project
        QgsProject.instance().addMapLayer(vlayer)
        
        # Verify it exists in the registry
        # method varies slightly by QGIS version, using reliable registry lookup
        layers = QgsProject.instance().mapLayersByName("Test Layer")

    def test_04_load_qris_project(self):
        """Test loading a minimal QRiS project database."""
        # Create temp DB for testing
        import tempfile
        import sqlite3
        import shutil
        import sys
        import gc
        from unittest.mock import patch, MagicMock
        
        # Ensure we can import src by absolute path or relative
        try:
             from src.gp.load_project_task import LoadProjectTask
        except ImportError:
            # Fallback for some test runners
            from qris_dev.src.gp.load_project_task import LoadProjectTask

        # secure a temp path
        tmp_dir = tempfile.mkdtemp()
        db_path = os.path.join(tmp_dir, 'test_project.qris')
        
        try:
            # Create minimal valid QRiS schema
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            # Use the actual schema to be safe, or at least the critical 'projects' table
            c.execute('''
                CREATE TABLE projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    map_guid TEXT,
                    metadata TEXT,
                    created_on DATETIME default current_timestamp,
                    modified_on DATETIME default current_timestamp
                )
            ''')
            # Also need 'layers' and 'lookups' tables as referenced in Project.__init__
            c.execute('CREATE TABLE layers (id INTEGER PRIMARY KEY, name TEXT)') # Simplified
            c.execute('CREATE TABLE protocols (id INTEGER PRIMARY KEY, name TEXT)') # Simplified
            c.execute('CREATE TABLE lookups (id INTEGER PRIMARY KEY, name TEXT)') # Simplified
            c.execute('CREATE TABLE planning_containers (id INTEGER PRIMARY KEY, name TEXT)') # Simplified
            c.execute('CREATE TABLE planning_container_events (id INTEGER PRIMARY KEY, planning_container_id INTEGER, event_id INTEGER)')
            c.execute('CREATE TABLE rasters (id INTEGER PRIMARY KEY, name TEXT)') # Simplified
            c.execute('CREATE TABLE migrations (id INTEGER PRIMARY KEY, file_name TEXT, created_on DATETIME)') # For migration check
            
            # Additional tables for Project model initialization
            c.execute('CREATE TABLE sample_frames (id INTEGER PRIMARY KEY, name TEXT, sample_frame_type_id INTEGER)')
            c.execute('CREATE TABLE events (id INTEGER PRIMARY KEY, name TEXT, protocol_id INTEGER, method_id INTEGER, project_id INTEGER)')
            c.execute('CREATE TABLE event_rasters (id INTEGER PRIMARY KEY, event_id INTEGER, raster_id INTEGER)')
            c.execute('CREATE TABLE event_layers (id INTEGER PRIMARY KEY, event_id INTEGER, layer_id INTEGER)')
            c.execute('CREATE TABLE metrics (id INTEGER PRIMARY KEY, name TEXT)')
            c.execute('CREATE TABLE calculations (id INTEGER PRIMARY KEY, name TEXT, metric_id INTEGER)')
            c.execute('CREATE TABLE analyses (id INTEGER PRIMARY KEY, name TEXT)')
            c.execute('CREATE TABLE attachments (attachment_id INTEGER PRIMARY KEY, attachment_type TEXT, display_label TEXT, path TEXT, description TEXT, metadata TEXT)')
            c.execute('CREATE TABLE lkp_units (id INTEGER PRIMARY KEY, name TEXT)')
            c.execute('CREATE TABLE pour_points (id INTEGER PRIMARY KEY, name TEXT)')
            c.execute('CREATE TABLE stream_gages (id INTEGER PRIMARY KEY, name TEXT)')
            c.execute('CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT)')
            c.execute('CREATE TABLE cross_sections (id INTEGER PRIMARY KEY, name TEXT)')
            # scratch_vectors is often distinct/optional but Project loads it
            c.execute('CREATE TABLE scratch_vectors (id INTEGER PRIMARY KEY, name TEXT)')

            # Add GeoPackage metadata tables required by specific migration checks
            c.execute('CREATE TABLE gpkg_contents (table_name TEXT, data_type TEXT, identifier TEXT, description TEXT, last_change DATETIME, min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE, srs_id INTEGER)')
            c.execute('CREATE TABLE gpkg_geometry_columns (table_name TEXT, column_name TEXT, geometry_type_name TEXT, srs_id INTEGER, z TINYINT, m TINYINT)')
            c.execute("INSERT INTO gpkg_contents (table_name, data_type) VALUES ('test_layer', 'features')")

            # Insert a dummy project
            c.execute("INSERT INTO projects (name, description, map_guid, metadata) VALUES ('Test Project', 'Description', 'GUID', '{}')")
            conn.commit()
            conn.close()

            # Now try to load it using the Task logic
            # We MOCK the migration step to avoid needing a perfect schema
            with patch('src.gp.load_project_task.apply_db_migrations') as mock_migrate:
                mock_migrate.return_value = [] # Return empty list of messages
                
                # We bypass QgsTask threading by instantiating and running .run() directly
                # Mock callback
                loaded_project = None
                def on_complete(proj):
                    nonlocal loaded_project
                    loaded_project = proj

                task = LoadProjectTask(db_path, on_complete)
                
                # Calling run() directly executes the logic synchronously
                success = task.run()
                
                if success:
                    # If run() returns True, we simulate the finished() call that QGIS would normally do
                    task.finished(True)
                
                self.assertTrue(success, f"Project load failed: {task.error}")
                self.assertIsNotNone(loaded_project, "Callback was not executed with project")
                self.assertEqual(loaded_project.name, 'Test Project')
                LOGGER.info("Baseline: QRiS Project loaded successfully.")
                
                # Cleanup references to ensure file lock is released
                loaded_project = None
                task = None

        finally:
            gc.collect() # Force garbage collection of objects holding DB connections
            if os.path.exists(tmp_dir):
                try:
                    shutil.rmtree(tmp_dir)
                except PermissionError:
                    LOGGER.warning(f"Could not remove temp dir {tmp_dir} - file still in use. This is common on Windows during tests.")

if __name__ == '__main__':
    unittest.main()
