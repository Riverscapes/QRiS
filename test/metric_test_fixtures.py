"""Shared fixtures for metric tests that build temporary GeoPackages."""

import os
import shutil
import sqlite3
import tempfile

from osgeo import ogr, osr


def create_temp_gpkg(filename="test_project.gpkg"):
    """Create a temporary folder and GeoPackage datasource."""
    test_dir = tempfile.mkdtemp()
    gpkg_path = os.path.join(test_dir, filename)
    driver = ogr.GetDriverByName("GPKG")
    ds = driver.CreateDataSource(gpkg_path)
    return test_dir, gpkg_path, ds


def cleanup_temp_gpkg(ds, test_dir):
    """Release the datasource and remove the temp folder."""
    ds = None
    try:
        shutil.rmtree(test_dir)
    except Exception:
        pass
    return ds


def create_spatial_ref(epsg):
    """Create and return an OGR spatial reference from an EPSG code."""
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    return srs


def create_sample_frame_layer(ds, srs, ring_points, fid=1, layer_name="sample_frame_features"):
    """Create a sample frame polygon layer with one feature and return it."""
    sf_layer = ds.CreateLayer(layer_name, srs=srs, geom_type=ogr.wkbPolygon25D)
    sf_layer.CreateField(ogr.FieldDefn("fid", ogr.OFTInteger))

    sf_feat = ogr.Feature(sf_layer.GetLayerDefn())
    sf_geom = ogr.Geometry(ogr.wkbPolygon)
    ring = ogr.Geometry(ogr.wkbLinearRing)
    for x, y in ring_points:
        ring.AddPoint(x, y)
    sf_geom.AddGeometry(ring)
    sf_feat.SetGeometry(sf_geom)
    sf_feat.SetField("fid", fid)
    sf_layer.CreateFeature(sf_feat)

    return sf_layer


def create_dce_layer(ds, layer_name, srs, geom_type):
    """Create a DCE layer with the standard metric fields and return it."""
    layer = ds.CreateLayer(layer_name, srs=srs, geom_type=geom_type)
    layer.CreateField(ogr.FieldDefn("event_id", ogr.OFTInteger))
    layer.CreateField(ogr.FieldDefn("event_layer_id", ogr.OFTInteger))
    layer.CreateField(ogr.FieldDefn("metadata", ogr.OFTString))
    return layer


def create_layers_table(gpkg_path, rows):
    """Create the layers table and insert provided (id, fc_name, geom_type) rows."""
    conn = sqlite3.connect(gpkg_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE layers (id INTEGER PRIMARY KEY, fc_name TEXT, geom_type TEXT)")
    cur.executemany("INSERT INTO layers (id, fc_name, geom_type) VALUES (?, ?, ?)", rows)
    conn.commit()
    conn.close()
