
import os
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.dom import minidom


class Layer():
    def __init__(self, name, path, type='Layer') -> None:
        self.name = name
        self.path = path
        self.type = type


class Raster(Layer):

    def __init__(self, name, path) -> None:
        super().__init__(name, path, type='Raster')

        self.surfaces = {}

    def add_surface(self, surface_name, surface_path, surface_type):

        self.surfaces[surface_name] = Layer(surface_name, surface_path, surface_type)


class RiptProject():

    version = "0.0.1"

    def __init__(self, name=None) -> None:

        self.project_name = name
        self.time_created = datetime.now(timezone.utc).astimezone().isoformat()
        self.description = ""
        self.filename = None
        self.project_path = None

        self.detrended_rasters = {}
        self.project_layers = {}

    def add_layer(self, layer_name, layer_path, parent=None, meta=None):

        relpath = os.path.relpath(layer_path, self.project_path)
        self.project_layers[layer_name] = Layer(layer_name, relpath, "Layer")

    def add_detrended(self, detrended_name, path, parent=None, meta=None):

        relpath = os.path.relpath(path, self.project_path)
        self.detrended_rasters[detrended_name] = Raster(detrended_name, relpath)

    def load_from_project_file(self, filename=None):
        self.filename = filename if filename is not None else self.filename

        self.project_path = os.path.dirname(filename)

        tree = ET.parse(filename)
        root = tree.getroot()

        self.project_name = [elem.text for elem in root if elem.tag == 'Name'][0]
        self.time_created = [elem.text for elem in root if elem.tag == 'DateTimeCreated'][0]
        self.description = [elem.text for elem in root if elem.tag == 'Description'][0]

        detrended = root.find('DetrendedRasters')
        if detrended is not None:
            for raster_elem in detrended.iter('Raster'):
                raster = Raster(raster_elem.find('Name').text,
                                raster_elem.find('Path').text)
                surfaces = raster_elem.find('Surfaces')
                if surfaces is not None:
                    for surface in surfaces.iter('Surface'):
                        raster.surfaces[surface.find('Name').text] = Layer(surface.find('Name').text,
                                                                           surface.find('Path').text,
                                                                           surface.find('SurfaceType').text)
                self.detrended_rasters[raster_elem.find('Name').text] = raster

        layers = root.find('ProjectLayers')
        if layers is not None:
            for layer_elem in layers.iter('Layer'):
                self.project_layers[layer_elem.find('Name').text] = Layer(layer_elem.find('Name').text,
                                                                          layer_elem.find('Path').text,
                                                                          'Layer')

        return

    def export_project_file(self, filename=None):

        self.filename = filename if filename is not None else self.filename

        root = Element('Project')

        project_name = SubElement(root, 'Name')
        project_name.text = self.project_name

        timestamp = SubElement(root, "DateTimeCreated")
        timestamp.text = self.time_created

        version = SubElement(root, "RIPTVersion")
        version.text = self.version

        description = SubElement(root, "Description")
        description.text = self.description

        # Add gis layers and rasters
        detrended_rasters = SubElement(root, "DetrendedRasters")
        for raster in self.detrended_rasters.values():
            r = SubElement(detrended_rasters, "Raster")
            name = SubElement(r, "Name")
            name.text = raster.name
            path = SubElement(r, "Path")
            path.text = raster.path
            # Add Surfaces if exists
            if len(raster.surfaces) > 0:
                surfaces = SubElement(r, "Surfaces")
                for surface in raster.surfaces.values():
                    s = SubElement(surfaces, "Surface")
                    name = SubElement(s, "Name")
                    name.text = surface.name
                    path = SubElement(s, "Path")
                    path.text = surface.path
                    stype = SubElement(s, 'SurfaceType')
                    stype.text = surface.type

        project_layers = SubElement(root, "ProjectLayers")
        for layer in self.project_layers.values():
            lyr = SubElement(project_layers, "Layer")
            name = SubElement(lyr, "Name")
            name.text = layer.name
            path = SubElement(lyr, "Path")
            path.text = layer.path

        output = prettify(root)

        with open(self.filename, 'w') as outfile:
            outfile.write(output)


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")
