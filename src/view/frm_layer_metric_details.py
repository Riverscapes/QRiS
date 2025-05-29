from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextBrowser
from PyQt5.QtGui import QDesktopServices
from typing import Union

from ..model.protocol import Protocol
from ..model.layer import Layer
from ..model.metric import Metric
from ..QRiS.protocol_parser import LayerDefinition, MetricDefinition

class FrmLayerMetricDetails(QDialog):
    def __init__(self, parent, qris_project, layer: Union[Layer, LayerDefinition] = None, metric: Union[Metric, MetricDefinition] = None):
        super().__init__(parent)
        
        title = "Layer Details" if layer is not None else "Metric Details"
        self.setWindowTitle(title)
        self.setUI()

        self.qris_project = qris_project
        self.layer = layer
        self.analysis_metric = metric

        protocol_name = None
        protocol_version = None
        layer_name = None
        layer_version = None

        metric_name = None
        metric_version = None

        self.html_content = f"""
        <html>
        <head>
            <style type="text/css">
                body {{ font-family: Arial, sans-serif; font-size: 14px; }}
                h1 {{ color: #333; }}
                p {{ margin: 5px 0; }}
            </style>
        </head>
        <body>"""

        if isinstance(self.layer, LayerDefinition):
            protocol_name = self.layer.protocol_definition.label
            protocol_machine_code = self.layer.protocol_definition.machine_code if self.layer.protocol_definition.machine_code else "No machine name available."
            protocol_version = self.layer.protocol_definition.version
            protocol_description = self.layer.protocol_definition.description if self.layer.protocol_definition.description else "No description available."
            protocol_url = self.layer.protocol_definition.url if self.layer.protocol_definition.url else "No URL available."
            # make the protocol_url clickable
            protocol_url = f'<a href="{protocol_url}">{protocol_url}</a>' if protocol_url else "No URL available."
            protocol_citation = self.layer.protocol_definition.citation if self.layer.protocol_definition.citation else "No citation available."
            protocol_author = self.layer.protocol_definition.author if self.layer.protocol_definition.author else "No author available."
            protocol_creation_date = self.layer.protocol_definition.creation_date if self.layer.protocol_definition.creation_date else "No creation date available."
            protocol_updated_date = self.layer.protocol_definition.updated_date if self.layer.protocol_definition.updated_date else "No updated date available."
            protocol_metadata = []
            if self.layer.protocol_definition.metadata:
                for key, value in self.layer.protocol_definition.metadata.items():
                    protocol_metadata.append(f"<p><strong>{key}:</strong> {value}</p>")
        
            layer_name = self.layer.label
            layer_id = self.layer.id
            layer_version = self.layer.version
            layer_description = self.layer.description if self.layer.description else "No description available."

        elif isinstance(self.layer, Layer):
            # Layer
            layer_name = self.layer.name
            layer_id = self.layer.layer_id
            layer_version = self.layer.layer_version
            layer_description = self.layer.description if self.layer.description else "No description available."
            layer_metadata = []
            if self.layer.metadata:
                for key, value in self.layer.metadata.items():
                    layer_metadata.append(f"<p><strong>{key}:</strong> {value}</p>")
            # Protocol
            protocol: Protocol = self.layer.get_layer_protocol(qris_project.protocols)    
            protocol_name = protocol.name if protocol else "Unknown"
            protocol_machine_code = protocol.machine_code if protocol else "Unknown"
            protocol_version = protocol.version if protocol else "Unknown"            
            protocol_description = protocol.description if protocol else "No protocol description available."
            protocol_url = protocol.system_metadata.get('url', 'Unknown') if protocol.system_metadata else "Unknown"
            # make the protocol_url clickable
            protocol_url = f'<a href="{protocol_url}">{protocol_url}</a>' if protocol_url else "Unknown"
            protocol_citation = protocol.system_metadata.get('citation', 'Unknown') if protocol.system_metadata else "Unknown"
            protocol_author = protocol.system_metadata.get('author', 'Unknown') if protocol.system_metadata else "Unknown"
            protocol_creation_date = protocol.system_metadata.get('creation_date', 'Unknown') if protocol.system_metadata else "Unknown"
            protocol_updated_date = protocol.system_metadata.get('updated_date', 'Unknown') if protocol.system_metadata else "Unknown"

            protocol_metadata = []
            if protocol.metadata:
                for key, value in protocol.metadata.items():
                    protocol_metadata.append(f"<p><strong>{key}:</strong> {value}</p>")
        
        elif isinstance(self.analysis_metric, MetricDefinition):

            pass

        elif isinstance(self.analysis_metric, Metric):

            # Metric
            metric_label = self.analysis_metric.name
            metric_name = self.analysis_metric.machine_name
            metric_version = self.analysis_metric.version
            metric_description = self.analysis_metric.description if self.analysis_metric.description else "No description available."
            metric_function = self.analysis_metric.metric_function
            metric_params = self.analysis_metric.metric_params
            metric_url = self.analysis_metric.definition_url if self.analysis_metric.definition_url else "No URL available."
            metric_metadata = []
            if self.analysis_metric.metadata:
                for key, value in self.analysis_metric.metadata.items():
                    metric_metadata.append(f"<p><strong>{key}:</strong> {value}</p>")

            # Protocol
            protocol: Protocol = self.analysis_metric.get_metric_protocol(self.qris_project.protocols)    
            protocol_name = protocol.name if protocol else "Unknown"
            protocol_machine_code = protocol.machine_code if protocol else "Unknown"
            protocol_version = protocol.version if protocol else "Unknown"            
            protocol_description = protocol.description if protocol else "No protocol description available."
            protocol_url = protocol.system_metadata.get('url', 'Unknown') if protocol.system_metadata else "Unknown"
            # make the protocol_url clickable
            protocol_url = f'<a href="{protocol_url}">{protocol_url}</a>' if protocol_url else "Unknown"
            protocol_citation = protocol.system_metadata.get('citation', 'Unknown') if protocol.system_metadata else "Unknown"
            protocol_author = protocol.system_metadata.get('author', 'Unknown') if protocol.system_metadata else "Unknown"
            protocol_creation_date = protocol.system_metadata.get('creation_date', 'Unknown') if protocol.system_metadata else "Unknown"
            protocol_updated_date = protocol.system_metadata.get('updated_date', 'Unknown') if protocol.system_metadata else "Unknown"

            protocol_metadata = []
            if protocol.metadata:
                for key, value in protocol.metadata.items():
                    protocol_metadata.append(f"<p><strong>{key}:</strong> {value}</p>")
        
        else:
            self.html_content += """
            No layer or protocol information available.
            """
            self.text_edit.setHtml(self.html_content)
            return

        if self.layer is not None:
            self.html_content += f"""
                <h1>Layer Information</h1>
                <p><strong>Name:</strong> {layer_name}</p>
                <p><strong>ID:</strong> {layer_id}</p>
                <p><strong>Version:</strong> {layer_version}</p>
                <p><strong>Description:</strong> {layer_description}</p>
                """
            if layer_metadata:
                self.html_content += "".join(layer_metadata)
        
        if self.analysis_metric is not None:
            self.html_content += f"""
                <h1>Metric Information</h1>
                <p><strong>Name:</strong> {metric_label}</p>
                <p><strong>ID:</strong> {metric_name}</p>
                <p><strong>Version:</strong> {metric_version}</p>
                <p><strong>Description:</strong> {metric_description}</p>
                <p><strong>Calculation Type:</strong> {metric_function}</p>
                <p><strong>URL:</strong> {metric_url}</p>
                """
            if metric_metadata:
                self.html_content += "".join(metric_metadata)

        self.html_content += f"""
            <h1>Protocol Information</h1>
            <p><strong>Name:</strong> {protocol_name}</p>
            <p><strong>Machine Code:</strong> {protocol_machine_code}</p>
            <p><strong>Version:</strong> {protocol_version} (last updated: {protocol_updated_date})</p>
            <p><strong>Description:</strong> {protocol_description}</p>
            <p><strong>Created by:</strong> {protocol_author} on {protocol_creation_date}</p>
            <p><strong>URL:</strong> {protocol_url}</p>
            <p><strong>Citation:</strong> {protocol_citation}</p>
            """
        if protocol_metadata:
            self.html_content += "".join(protocol_metadata)
        
        self.html_content += """
        </body>
        </html>
        """

        self.text_edit.setHtml(self.html_content)

    def open_link_in_browser(self, url):
        QDesktopServices.openUrl(url)
        self.text_edit.setHtml(self.html_content)

    def setUI(self):
        self.setMinimumSize(400, 600)
        layout = QVBoxLayout(self)
        self.text_edit = QTextBrowser(self)  # Use QTextBrowser instead of QTextEdit
        self.text_edit.setAcceptRichText(True)
        self.text_edit.setReadOnly(True) 
        self.text_edit.setOpenExternalLinks(False)  # Disable internal opening
        self.text_edit.anchorClicked.connect(self.open_link_in_browser)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
