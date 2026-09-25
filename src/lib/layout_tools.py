import os.path

from qgis.core import (
    QgsLayoutExporter,
    QgsLayoutFrame,
    QgsLayoutItemLabel,
    QgsLayoutItemManualTable,
    QgsLayoutItemMap,
    QgsLayoutItemTextTable,
    QgsLayoutTableColumn,
    QgsPrintLayout,
    QgsProject,
    QgsReadWriteContext,
    QgsTableCell,
)
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtXml import QDomDocument

from ..QRiS.settings import Settings


def _get_layout_by_id(layout_id: str, warn_if_missing: bool = True) -> QgsPrintLayout:
    qgis_project = QgsProject.instance()
    layout = qgis_project.layoutManager().layoutByName(layout_id)
    if not layout and warn_if_missing is True:
        QtWidgets.QMessageBox.warning(Settings().iface.mainWindow(), "QRiS", f"Layout '{layout_id}' does not exist.")
        return None
    return layout


def open_layout(layout_template_path, layout_name=None, show_designer=True):
    """
    Open a QGIS layout from a template file or XML string.

    Parameters:
    layout_template_path (str): Path to the layout template file (.qpt) or an XML string.
    layout_name (str, optional): Name to use for the layout. If None, the name is derived
        from the template file name.
    show_designer (bool): If True, open the QGIS layout designer UI. Default True.

    Returns:
    QgsPrintLayout: The layout that was loaded/opened, or None on failure.
    """

    if layout_template_path is None:
        QtWidgets.QMessageBox.warning(Settings().iface.mainWindow(), "QRiS", "Template selection invalid.")
        return None

    qgis_project = QgsProject.instance()
    layout = QgsPrintLayout(qgis_project)
    layout.initializeDefaults()
    doc = QDomDocument()

    if layout_name:
        base_name = layout_name
    else:
        base_name = os.path.splitext(os.path.basename(layout_template_path))[0]

    if layout_template_path.lower().endswith(".qpt"):
        template_type = "file"
    else:
        template_type = "xml"

    if template_type == "file":
        with open(layout_template_path) as f:
            template_content_str = f.read()
        doc.setContent(template_content_str)
    else:  # xml
        doc.setContent(layout_template_path)

    layout.loadFromTemplate(doc, QgsReadWriteContext())

    # Check for duplicate names
    layout_name = base_name

    # Check if layout already exists in QGIS project
    existing_layout = qgis_project.layoutManager().layoutByName(layout_name)
    if existing_layout:
        if show_designer:
            Settings().iface.openLayoutDesigner(existing_layout)
        return existing_layout

    counter = 1
    while qgis_project.layoutManager().layoutByName(layout_name):
        layout_name = f"{base_name} ({counter})"
        counter += 1

    layout.setName(layout_name)
    qgis_project.layoutManager().addLayout(layout)

    # Set map extent for all map items to match canvas
    canvas_extent = Settings().iface.mapCanvas().extent()
    for item in layout.items():
        if isinstance(item, QgsLayoutItemMap):
            item.zoomToExtent(canvas_extent)
            item.refresh()

    if show_designer:
        Settings().iface.openLayoutDesigner(layout)

    return layout


def serialize_layout(layout_id: str) -> str:
    """
    Serialize a QGIS layout to an XML string. This includes graphics rendered as part of the layout.

    Parameters:
    layout_id (str): The ID (name) of the layout to serialize.

    Returns:
    str: The XML string representation of the layout, or an empty string if the layout does not exist.
    """

    layout = _get_layout_by_id(layout_id, False)
    if not layout:
        return ""

    doc = QDomDocument()
    context = QgsReadWriteContext()

    # QGIS 3 exposes saveToTemplate; QGIS 4 removed it in favor of XML writers.
    if hasattr(layout, "saveToTemplate"):
        layout.saveToTemplate(doc, context)
        return doc.toString()

    for writer_name in ("writeLayoutXml", "writeXml"):
        writer = getattr(layout, writer_name, None)
        if callable(writer):
            try:
                layout_element = writer(doc, context)
            except TypeError:
                layout_element = writer(doc)

            if not layout_element.isNull():
                doc.appendChild(layout_element)
            return doc.toString()

    return ""


def print_layout(layout_id: str, out_pdf_path: str) -> None:
    """
    Print a QGIS layout to a PDF file.

    Parameters:
    layout_id (str): The ID (name) of the layout to print.
    out_pdf_path (str): The path to the output PDF file.

    Returns:
    None
    """

    layout = _get_layout_by_id(layout_id)
    if not layout:
        QtWidgets.QMessageBox.warning(Settings().iface.mainWindow(), "QRiS", f"Layout '{layout_id}' does not exist.")
        return

    exporter = QgsLayoutExporter(layout)
    result = exporter.exportToPdf(out_pdf_path, QgsLayoutExporter.PdfExportSettings())
    if result != QgsLayoutExporter.Success:
        QtWidgets.QMessageBox.warning(Settings().iface.mainWindow(), "QRiS", f"Failed to export layout '{layout_id}' to PDF.")


def set_layout_text(layout_id: str, slug: str, text: str) -> None:
    """
    Set dynamic text in a QGIS layout. This is basically a find-and-replace operation for all text within the layout.

    Parameters:
    layout_id (str): The ID (name) of the layout to modify.
    slug (str): The placeholder text (slug) to replace.
    text (str): The text to replace the slug with.

    Returns:
    None
    """
    layout = _get_layout_by_id(layout_id, False)
    if not layout:
        return

    for item in layout.items():
        if isinstance(item, QgsLayoutItemLabel):
            label_text = item.text()
            if slug in label_text:
                item.setText(label_text.replace(slug, text))
    layout.refresh()


def set_layout_table(layout_id: str, table_name: str, data: list[list[str]]) -> None:
    """
    Populate a QgsLayoutItemTextTable in a layout with the given data.

    The first row of *data* is treated as column headers; subsequent rows
    are the table body.  The table is found by its item ID (display name)
    in the layout.

    The text/formatting of the table will honor the existing styles and
    formatting set in the table layout, but not the individual cell/text
    contents. DO NOT USE the "Edit Table..." button to set the font properties.
    Use the Fonts and Text Styling options of the table itself.

    This function will add as many rows as needed to accomodate the table,
    but sizing of the table may prevent all rows from being visible within
    the layout and may need to be adjusted manually.

    Make sure to include the expected number of columns for the table layout.

    Parameters:
    layout_id (str): The ID (name) of the layout to modify.
    table_name (str): The item ID of the text table in the layout.
    data (list[list[str]]): 2D list — first row = headers, rest = data rows.

    Returns:
    None
    """
    layout = _get_layout_by_id(layout_id)
    if not layout:
        return

    if not data or len(data) < 1:
        QtWidgets.QMessageBox.warning(Settings().iface.mainWindow(), "QRiS", "No table data provided.")
        return

    # Find the table by its Item ID (stored on QgsLayoutFrame.id())
    # Iterate layout items to find a frame whose id matches, then get its multi-frame
    table_item = None
    for frame in layout.items():
        if isinstance(frame, QgsLayoutFrame):
            mf = frame.multiFrame()
            if mf and isinstance(mf, (QgsLayoutItemTextTable, QgsLayoutItemManualTable)) and frame.id() == table_name:
                table_item = mf
                break

    if not table_item:
        QtWidgets.QMessageBox.warning(
            Settings().iface.mainWindow(),
            "QRiS",
            f"Table '{table_name}' not found in layout '{layout_id}'.",
        )
        return

    headers = data[0]
    rows = data[1:]

    # ── Update column headers ─────────────────────────────────────────
    existing_headers = table_item.headers()
    for i, header in enumerate(headers):
        if i < len(existing_headers):
            existing_headers[i].setHeading(header)
        else:
            existing_headers.append(QgsLayoutTableColumn(header))
    table_item.setHeaders(existing_headers)
    table_item.setIncludeTableHeader(True)

    # ── Update cell data ──────────────────────────────────────────────
    table_contents = []
    for row_data in rows:
        table_contents.append([QgsTableCell(val) for val in row_data])
    table_item.setTableContents(table_contents)

    table_item.refresh()
    layout.refresh()
