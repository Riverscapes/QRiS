import os
from xml.etree import ElementTree as ET
import datetime
from jinja2 import Template
from uuid import uuid4


class Report():
    def __init__(self, file_path):

        self.template_path = "C:\\Users\\tyguy\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\developer\\python\\plugins\\QRiS\\src\\gp\\report_creation\\templates"

        self.file_path = file_path
        if os.path.isfile(self.file_path):
            os.remove(self.file_path)
        # self.css_files = []
        self.footer = ''
        self.toc = []
        self.css_files = []

        # Add in our common CSS. This can be extended
        self.add_css(os.path.join(self.template_path, 'report.css'))

        self.main_el = ET.Element('main', attrib={'id': 'ReportInner'})

    @staticmethod
    def create_table_from_dict(values, el_parent, attrib, context):
        if attrib is None:
            attrib = {}
        if 'class' in attrib:
            attrib['class'] = 'dictable {}'.format(attrib['class'])
        else:
            attrib['class'] = 'dictable'

        table = ET.Element('table', attrib=attrib)

        tbody = ET.Element('tbody')
        table.append(tbody)

        for key, val in values.items():

            tr = ET.Element('tr')
            tbody.append(tr)

            th = ET.Element('th')
            th.text = key
            tr.append(th)

            formatted_val, class_name = Report.format_value(val)
            td = ET.Element('td')
            td.text = str(formatted_val)
            tr.append(td)

            if context[0] is not None:
                total_area = context[0]
                percentages = ET.Element('td')
                percentages.text = str(round(int(val) / total_area * 100)) + "%"
                # percentages.text = "abc"

                tr.append(percentages)
        breakpoint
        el_parent.append(table)
        breakpoint

    @staticmethod
    def format_value(value, val_type=None):
        """[summary]

        Args:
            value ([type]): [description]
            val_type ([type], optional): Type to try and force

        Returns:
            [type]: [description]
        """
        formatted = ''
        class_name = ''

        try:
            if val_type == str or isinstance(value, str):
                formatted = value
                class_name = 'text'
            elif val_type == float or isinstance(value, float):
                formatted = '{0:,.2f}'.format(value)
                class_name = 'float num'
            elif val_type == int or isinstance(value, int):
                formatted = '{0:,d}'.format(value)
                class_name = 'int num'

        except Exception as e:
            print(e)
            return value, 'unknown'

        return formatted, class_name

    @staticmethod
    def header(level, text, el_parent):

        hEl = ET.Element('h{}'.format(level), attrib={'class': 'report-header', 'id': str(uuid4())})
        hEl.text = text
        el_parent.append(hEl)
        return hEl

    def write(self):
        css_template = "<style>\n{}\n</style>"
        html_inner = ET.tostring(self.main_el, method="html", encoding='unicode')
        styles = ''.join([css_template.format(css) for css in self.css_files])

        # toc = ''
        # if len(self.toc) > 0:
        #     toc = ET.tostring(self._table_of_contents(), method="html", encoding='unicode')
        # Get my HTML templae and render it

        with open(os.path.join(self.template_path, 'template.html')) as t:
            template = Template(t.read())

        now = datetime.datetime.now()
        final_render = template.render(report={
            'date': now.strftime('%B %d, %Y - %I:%M%p'),
            'head': styles,
            'body': html_inner,
            'footer': self.footer
        })

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(final_render)

    def section(self, sectionid, title, el_parent=None, level=1, attrib=None):
        if attrib is None:
            attrib = {}
        the_id = sectionid if sectionid is not None else str(uuid4())

        if 'class' in attrib:
            attrib['class'] = 'report-section {}'.format(attrib['class'])
        else:
            attrib['class'] = 'report-section'

        section = ET.Element('section', attrib={'id': the_id, **attrib})
        section_inner = ET.Element('div', attrib={'class': 'section-inner'})

        hlevel = level + 1
        if title:
            h_el = Report.header(hlevel, title, section)
            a_el = ET.Element('a', attrib={'class': 'nav-top', 'href': '#TOC'})
            a_el.text = 'Top'
            h_el.append(a_el)

        section.append(section_inner)
        self.toc.append({
            'level': level,
            'title': title,
            'sectionid': the_id
        })
        real_parent = self.main_el if el_parent is None else el_parent
        real_parent.append(section)

        return section_inner

    def add_css(self, filepath):
        with open(filepath) as css_file:
            css = css_file.read()
        self.css_files.append(css)

    @staticmethod
    def create_table_from_2d_array(values, el_parent, attrib, labels):
        if attrib is None:
            attrib = {}
        if 'class' in attrib:
            attrib['class'] = 'dictable {}'.format(attrib['class'])
        else:
            attrib['class'] = 'dictable'

        table = ET.Element('table', attrib=attrib)

        tbody = ET.Element('tbody')
        table.append(tbody)

        # Add labels to top row of table
        tr = ET.Element('tr')
        tbody.append(tr)
        for label in labels:
            th = ET.Element('th')
            th.text = str(label)
            tr.append(th)

        for i in range(0, len(values)):
            tr = ET.Element('tr')
            tbody.append(tr)
            for j in range(0, len(values[i])):
                if j == 0:
                    th = ET.Element('th')
                    th.text = str(values[i][j])
                    tr.append(th)
                else:
                    formatted_val, val_type = Report.format_value(values[i][j])
                    td = ET.Element('td')
                    td.text = str(formatted_val)
                    tr.append(td)
        el_parent.append(table)
