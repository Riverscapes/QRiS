
import os
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.dom import minidom


# These are classes to define our primary layer types and storing data about them
class ProjectExtent():
    """
    Constructs and stores project extent layer attributes. Used to populate the tree and write out to the project xml file.

    display_name (str): layer name used to display the layer in QGIS.
    table_name (str): GIS friendly name of the feature or table which will never change.
    description (str): Any comments or notes giving context to the layer.
    directory (str): Directory in which the input layer is stored
    geopackage (str): Name of the geopackage storing the layer
    """

    def __init__(self, display_name, feature_name, description, directory="projec_extents", geopackage="project_extents.gpkg") -> None:
        self.display_name = display_name
        self.feature_name = feature_name
        self.description = description
        self.directory = directory
        self.geopackage = geopackage

    def directory_path(self, project_path):
        return os.path.join(project_path, self.directory)

    def geopackage_path(self, project_path):
        return os.path.join(project_path, self.directory, self.geopackage)

    def full_path(self, project_path):
        return os.path.join(project_path, self.directory, self.geopackage + f"|layername={self.feature_name}")


class ProjectVector():
    pass


class ProjectRaster():
    pass


class Design():
    """Describes basic attributes of Low-Tech designs"""

    def __init__(self, directory="designs", geopackage="designs.gpkg") -> None:
        self.directory = directory
        self.geopackage = geopackage

    def directory_path(self, project_path):
        return os.path.join(project_path, self.directory)

    def geopackage_path(self, project_path):
        return os.path.join(project_path, self.directory, self.geopackage)

    def full_path(self, project_path, layer_name):
        """
        returns a complete full path to design geopackage tables
        layer_name (string): name of the geopackage layer
        zoi
        """
        return os.path.join(project_path, self.directory, self.geopackage + f"|layername={layer_name}")


class Raster():
    """Used to construct a list of reference raster layers within the project"""

    def __init__(self, name, path, type="Raster") -> None:
        self.name = name
        self.path = path
        self.type = type
        self.surfaces = {}

    def full_path(self, project_path):
        return os.path.join(project_path, self.path)

    # def add_surface(self, surface_name, surface_path, surface_type):
    #     self.surfaces[surface_name] = Layer(surface_name, surface_path, surface_type)


class QRiSProject():

    version = "0.0.1"

    def __init__(self, name=None) -> None:
        self.project_name = name
        self.time_created = datetime.now(timezone.utc).astimezone().isoformat()
        # TODO add a project description dialog
        self.description = ""
        self.filename = None
        self.project_path = None
        # self.detrended_rasters = {}
        self.project_extents = {}
        self.project_designs = Design()

    # def add_layer(self, layer_name, layer_path, parent=None, meta=None):
    #     relpath = os.path.relpath(layer_path, self.project_path)
    #     self.project_extents[layer_name] = Layer(layer_name, relpath, "Layer")

    # def add_detrended(self, detrended_name, path, parent=None, meta=None):
    #     relpath = os.path.relpath(path, self.project_path)
    #     self.detrended_rasters[detrended_name] = Raster(detrended_name, relpath)

    # TODO change to load_project_xml
    def load_project_file(self, filename=None):
        """uses the .qris project file to reference data structures within the project"""
        self.filename = filename if filename is not None else self.filename

        self.project_path = os.path.dirname(filename)

        tree = ET.parse(filename)
        root = tree.getroot()

        self.project_name = [elem.text for elem in root if elem.tag == 'Name'][0]
        self.time_created = [elem.text for elem in root if elem.tag == 'DateTimeCreated'][0]
        self.description = [elem.text for elem in root if elem.tag == 'Description'][0]

        # populate project layers dictionary
        layers = root.find('ProjectExtents')
        if layers is not None:
            for layer_elem in layers.iter('Extent'):
                self.project_extents[layer_elem.find('FeatureName').text] = ProjectExtent(layer_elem.find('DisplayName').text,
                                                                                          layer_elem.find('FeatureName').text,
                                                                                          layer_elem.find('Description').text,
                                                                                          layer_elem.find('Directory').text,
                                                                                          layer_elem.find('Geopackage').text)

        # populate detrended rasters dictionary
        # detrended = root.find('DetrendedRasters')
        # if detrended is not None:
        #     for raster_elem in detrended.iter('Raster'):
        #         raster = Raster(raster_elem.find('Name').text,
        #                         raster_elem.find('Path').text)
        #         surfaces = raster_elem.find('Surfaces')
        #         if surfaces is not None:
        #             for surface in surfaces.iter('Surface'):
        #                 raster.surfaces[surface.find('Name').text] = Layer(surface.find('Name').text,
        #                                                                    surface.find('Path').text,
        #                                                                    surface.find('SurfaceType').text)
        #         self.detrended_rasters[raster_elem.find('Name').text] = raster

    def write_project_xml(self, filename=None):
        """writes the project xml given """
        self.filename = filename if filename is not None else self.filename

        root = Element('Project')

        project_name = SubElement(root, 'Name')
        project_name.text = self.project_name

        timestamp = SubElement(root, "DateTimeCreated")
        timestamp.text = self.time_created

        version = SubElement(root, "QRiSVersion")
        version.text = self.version

        description = SubElement(root, "Description")
        description.text = self.description

        # # Add gis layers and rasters
        # detrended_rasters = SubElement(root, "DetrendedRasters")
        # for raster in self.detrended_rasters.values():
        #     r = SubElement(detrended_rasters, "Raster")
        #     name = SubElement(r, "Name")
        #     name.text = raster.name
        #     path = SubElement(r, "Path")
        #     path.text = raster.path
        #     # Add Surfaces if exists
        #     if len(raster.surfaces) > 0:
        #         surfaces = SubElement(r, "Surfaces")
        #         for surface in raster.surfaces.values():
        #             s = SubElement(surfaces, "Surface")
        #             name = SubElement(s, "Name")
        #             name.text = surface.name
        #             path = SubElement(s, "Path")
        #             path.text = surface.path
        #             stype = SubElement(s, 'SurfaceType')
        #             stype.text = surface.type

        # PROJECT EXTENTS
        project_extents = SubElement(root, "ProjectExtents")
        for layer in self.project_extents.values():
            Extent = SubElement(project_extents, "Extent")
            FeatureName = SubElement(Extent, "FeatureName")
            FeatureName.text = layer.feature_name
            DisplayName = SubElement(Extent, "DisplayName")
            DisplayName.text = layer.display_name
            Description = SubElement(Extent, "Description")
            Description.text = layer.description
            Directory = SubElement(Extent, "Directory")
            Directory.text = layer.directory
            Geopackage = SubElement(Extent, "Geopackage")
            Geopackage.text = layer.geopackage

        output = prettify(root)

        with open(self.filename, 'w') as outfile:
            outfile.write(output)


def prettify(elem):
    """Return a pretty-printed XML string for the Element"""
    rough_string = tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")
