from gettext import npgettext
import json
from logging import NullHandler
from report import Report
import os
from xml.etree import ElementTree as ET
from plotting import pie_chart, bar_chart
import numpy as np


class QRiSReport(Report):

    def __init__(self, project_path, rs_project=None):
        self.json_path = os.path.join(project_path, "metrics_rsc_new.json")
        self.report_path = os.path.join(project_path, "test_report.html")
        self.veg_types_path = os.path.join(project_path, "vegetation_types.json")
        self.reach_codes_path = os.path.join(project_path, "reach_codes.json")
        self.waterbody_codes_path = os.path.join(project_path, "waterbody_codes.json")
        self.agencies_path = os.path.join(project_path, "agencies.json")
        self.transportation_path = os.path.join(project_path, "transportation.json")

        super().__init__(self.report_path)

        # The report has a core CSS file but we can extend it with our own if we want:
        # css_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'brat_report.css')
        # self.add_css(css_path)

        self.images_dir = os.path.join(project_path, 'images')
        # safe_makedirs(self.images_dir)

        self.build_qris_report()

    def build_qris_report(self):
        section = self.section('ReportIntro', 'Slope')

        with open(self.json_path) as f:
            json_data = json.loads(f.read())
        slope_data_unformatted = json_data['project']['metrics']['raster']['floatingPoint'][4]['SLOPE']['binnedCounts']['bins0']
        total_area = json_data['project']['metrics']['raster']['floatingPoint'][4]['SLOPE']["count"]
        table_wrapper = ET.Element('div', attrib={'class': 'tableWrapper'})
        slope_data = []

        # Convert list to readable format
        for i in range(0, len(slope_data_unformatted)):
            if slope_data_unformatted[i][1] is None:
                new_key = str(slope_data_unformatted[i][0]) + "%+"
            else:
                new_key = str(slope_data_unformatted[i][0]) + "-" + str(slope_data_unformatted[i][1]) + "%"
            slope_data.append([new_key, slope_data_unformatted[i][2]])

        # Add percentages to list
        for entry in slope_data:
            entry.append(str(round(float(entry[1]) / total_area * 100, 2)) + "%")

        column_labels = ["Slope", "Area (ha)", "Percent"]
        Report.create_table_from_2d_array(slope_data, table_wrapper, {'id': 'SlopeTable'}, column_labels)
        section.append(table_wrapper)

        self.setup_pie_chart(section, slope_data, "slope", "Slope")
        self.setup_bar_chart(section, slope_data, "slope", "Slope", "Slope", "Percentage")

        # Convert list of vegetation strings and IDs to dict
        with open(self.veg_types_path) as f:
            veg_list = json.loads(f.read())
        veg_dict = {row['vegetation_id']: row['name'] for row in veg_list}

        # Data with a similar format
        sections_info = [("EXVEG", "Existing Vegetation", 0), ("HISTVEG", "Historic Vegetation", 1)]

        for section_info in sections_info:

            section = self.section('ReportIntro', section_info[1])
            veg_data_unformatted = json_data['project']['metrics']['raster']['categorical'][section_info[2]][section_info[0]]['categories']
            veg_data = []
            # Convert dict to np array
            for key in veg_data_unformatted.keys():
                veg_data.append([key, veg_data_unformatted[key]["area"]])
            np_veg = np.array(veg_data)
            np_veg = np_veg.astype(float)

            veg_data_trimmed = []
            total_count = np_veg.sum(axis=0)[1]

            # Adds first 9 values to new list
            for i in range(0, 9):
                max_index = np_veg.argmax(axis=0)[1]
                veg_data_trimmed.append([str(int(np_veg[max_index].tolist()[0])), veg_dict[np_veg[max_index].tolist()[0]], np_veg[max_index].tolist()[1]])
                np_veg = np.delete(np_veg, max_index, axis=0)

            # Combines leftover data into Other category and adds it to list
            veg_data_trimmed.append(["Other", "Other", int(np_veg.sum(axis=0)[1])])

            # Adds percentages to list
            for entry in veg_data_trimmed:
                entry.append(str(round(float(entry[2]) / total_count * 100, 2)) + "%")

            table_wrapper = ET.Element('div', attrib={'class': 'tableWrapper'})
            column_labels = ["Code", "Vegetation", "Area (ha)", "Percent"]
            Report.create_table_from_2d_array(veg_data_trimmed, table_wrapper, {'id': 'SlopeTable'}, column_labels)
            section.append(table_wrapper)

            self.setup_pie_chart(section, veg_data_trimmed, section_info[0], section_info[1])
            self.setup_bar_chart(section, veg_data_trimmed, section_info[0], section_info[1], "Vegetation Type", "Percentage")

        section = self.section('ReportIntro', 'NHD Flowlines')
        with open(self.reach_codes_path) as f:
            reach_codes_list = json.loads(f.read())
        rc_dict = {str(row['ReachCode']): row['DisplayName'] for row in reach_codes_list}
        nhdflowlines_unformatted = json_data['project']['metrics']['vector']['polyline'][0]['NHDFlowline']['fields']['FCode']
        total_length = json_data['project']['metrics']['vector']['polyline'][0]['NHDFlowline']['lengthTotal'] / 1000

        nhdflowlines = []
        for key in nhdflowlines_unformatted.keys():
            nhdflowlines.append([key, rc_dict[key], nhdflowlines_unformatted[key] / 1000])

        # TODO Add converted distance (km or mi)
        for entry in nhdflowlines:
            entry.append(entry[2] * 0.621371)
            entry.append(str(round(float(entry[2]) / total_length * 100, 2)) + "%")

        table_wrapper = ET.Element('div', attrib={'class': 'tableWrapper'})
        column_labels = ["FCode", "Name", "Length (km)", "Length (mi)", "Percent"]
        Report.create_table_from_2d_array(nhdflowlines, table_wrapper, {'id': 'SlopeTable'}, column_labels)
        section.append(table_wrapper)
        self.setup_pie_chart(section, nhdflowlines, "nhdflowlines", "NHD Flowlines")
        self.setup_bar_chart(section, nhdflowlines, "nhdflowlines", "NHD Flowlines", "Type", "Percentage")

        # NHD Waterbodies
        section = self.section('ReportIntro', 'NHD Waterbodies')
        with open(self.waterbody_codes_path) as f:
            wb_dict = json.loads(f.read())[0]
        nhd_wb_unformatted = json_data['project']['metrics']['vector']['polygon'][1]['NHDWaterbody']['fields']['FCode']
        total_area = json_data['project']['metrics']['vector']['polygon'][1]['NHDWaterbody']['areaTotal']

        nhd_waterbodies = []
        for key in nhd_wb_unformatted.keys():
            nhd_waterbodies.append([key, wb_dict[key], nhd_wb_unformatted[key]])

        for entry in nhd_waterbodies:
            entry.append(str(round(float(entry[2]) / total_area * 100, 2)) + "%")

        table_wrapper = ET.Element('div', attrib={'class': 'tableWrapper'})
        column_labels = ["FCode", "Name", "Area ()", "Percent"]
        Report.create_table_from_2d_array(nhd_waterbodies, table_wrapper, {'id': 'SlopeTable'}, column_labels)
        section.append(table_wrapper)
        self.setup_pie_chart(section, nhd_waterbodies, "nhdwaterbodies", "NHD Waterbodies")
        self.setup_bar_chart(section, nhd_waterbodies, "nhdwaterbodies", "NHD Waterbodies", "Type", "Percentage")

        # Ownership
        section = self.section('ReportIntro', 'Ownership')
        with open(self.agencies_path) as f:
            ownership_list = json.loads(f.read())
        ownership_dict = {str(row['Abbreviation']): row['Name'] for row in ownership_list}
        ownership_unformatted = json_data['project']['metrics']['vector']['polygon'][3]['Ownership']['fields']['ADMIN_AGEN']
        total_area = json_data['project']['metrics']['vector']['polygon'][3]['Ownership']['areaTotal']

        ownership_data = []
        for key in ownership_unformatted.keys():
            ownership_data.append([key, ownership_dict[key], ownership_unformatted[key]])

        for entry in ownership_data:
            entry.append(str(round(float(entry[2]) / total_area * 100, 2)) + "%")

        table_wrapper = ET.Element('div', attrib={'class': 'tableWrapper'})
        column_labels = ["Code", "Name", "Area (ha)", "Percent"]
        Report.create_table_from_2d_array(ownership_data, table_wrapper, {'id': 'SlopeTable'}, column_labels)
        section.append(table_wrapper)
        self.setup_pie_chart(section, ownership_data, "ownership", "Ownership")
        self.setup_bar_chart(section, ownership_data, "ownership", "Ownership", "Agency", "Percentage")

        # Transportation
        section = self.section('ReportIntro', 'Transportation')

        with open(self.transportation_path) as f:
            transportation_dict = json.loads(f.read())[0]
        transport_unformatted = json_data['project']['metrics']['vector']['polyline'][1]['Roads']['fields']['TNMFRC']
        total_length = json_data['project']['metrics']['vector']['polyline'][1]['Roads']["lengthTotal"] / 1000

        transport_data = []
        for key in transport_unformatted.keys():
            transport_data.append([key, transportation_dict[key], transport_unformatted[key] / 1000])

        for entry in transport_data:
            entry.append(entry[2] * 0.621371)
            entry.append(str(round(float(entry[2]) / total_length * 100, 2)) + "%")

        table_wrapper = ET.Element('div', attrib={'class': 'tableWrapper'})
        column_labels = ["Code", "Type", "Length (km)", "Length (mi)", "Percent"]
        Report.create_table_from_2d_array(transport_data, table_wrapper, {'id': 'SlopeTable'}, column_labels)
        section.append(table_wrapper)
        self.setup_pie_chart(section, transport_data, "roads", "Roads")
        self.setup_bar_chart(section, transport_data, "roads", "Roads", "Road Type", "Percentage")

        table_wrapper = ET.Element('div', attrib={'class': 'tableWrapper'})
        rail_length = json_data['project']['metrics']['vector']['polyline'][2]['Rail']["lengthTotal"] / 1000
        total_length_data = [["Roads", total_length, total_length * 0.621371], ["Rail", rail_length, rail_length * 0.621371]]
        column_labels = ["Type", "Length (km)", "Length(mi)"]
        Report.create_table_from_2d_array(total_length_data, table_wrapper, {'id': 'SlopeTable'}, column_labels)
        section.append(table_wrapper)

    def setup_bar_chart(self, section, data, name, title, x_label, y_label):
        # labels = [row[0] for row in data]

        if len(data[0]) == 4:
            labels = [row[0] + "-" + row[1][:30] + "..." if len(row[1]) > 30 else row[0] + "-" + row[1] for row in data]
            percentages = [float(row[3][:-1]) for row in data]
        elif len(data[0]) == 3:
            labels = [row[0][:30] + "..." if len(row[0]) > 30 else row[0] for row in data]
            percentages = [float(row[2][:-1]) for row in data]
        elif len(data[0]) == 5:
            labels = [row[0] + "-" + row[1][:30] + "..." if len(row[1]) > 30 else row[0] + "-" + row[1] for row in data]
            percentages = [float(row[4][:-1]) for row in data]
        else:
            breakpoint

        img_wrap_bar = ET.Element('div', attrib={'class': 'imgWrap'})
        bar_chart_img_path = os.path.join(self.images_dir, 'attribute_{}.png'.format(name + "_bar"))
        bar_chart(percentages, labels, bar_chart_img_path, x_label, y_label, title)

        bar_img = ET.Element('img', attrib={'class': 'boxplot', 'alt': 'boxplot', 'src': '{}/{}'.format(os.path.basename(self.images_dir), os.path.basename(bar_chart_img_path))})
        img_wrap_bar.append(bar_img)
        reach_wrapper_inner_bar = ET.Element('div', attrib={'class': 'reachAtributeInner'})
        section.append(reach_wrapper_inner_bar)
        reach_wrapper_inner_bar.append(img_wrap_bar)

    def setup_pie_chart(self, section, data, name, title):
        img_wrap = ET.Element('div', attrib={'class': 'imgWrap'})
        image_path = os.path.join(self.images_dir, 'attribute_{}.png'.format(name + "_pie"))

        if len(data[0]) == 4:
            labels = [row[0] + "-" + row[1][:30] + "..." if len(row[1]) > 30 else row[0] + "-" + row[1] for row in data]
            values = [row[2] for row in data]
        elif len(data[0]) == 3:
            labels = [row[0][:30] + "..." if len(row[0]) > 30 else row[0] for row in data]
            values = [row[1] for row in data]
        elif len(data[0]) == 5:
            labels = [row[0] + "-" + row[1][:30] + "..." if len(row[1]) > 30 else row[0] + "-" + row[1] for row in data]
            values = [float(row[4][:-1]) for row in data]
        else:
            breakpoint

        pie_chart(values, labels, image_path, title)

        img = ET.Element('img', attrib={'class': 'boxplot', 'alt': 'boxplot', 'src': '{}/{}'.format(os.path.basename(self.images_dir), os.path.basename(image_path))})
        img_wrap.append(img)
        reach_wrapper_inner = ET.Element('div', attrib={'class': 'reachAtributeInner'})
        section.append(reach_wrapper_inner)
        reach_wrapper_inner.append(img_wrap)


if __name__ == '__main__':
    # cfg = ModelConfig('http://xml.riverscapes.xyz/Projects/XSD/V1/BRAT.xsd', __version__)
    # project = RSProject(cfg, args.projectxml)

    # json_path = "C:\\Users\\tyguy\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\developer\\python\\plugins\\QRiS\\src\\gp\\report_creation\\metrics_rsc_new.json"
    file_path = "C:\\Users\\tyguy\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\developer\\python\\plugins\\QRiS\\src\\gp\\report_creation"
    report = QRiSReport(file_path)
    report.write()
