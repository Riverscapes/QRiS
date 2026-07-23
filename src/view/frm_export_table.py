import csv
import json

from qgis.PyQt import QtWidgets
import xlwt

from .frm_export_base import FrmBaseExport


class FrmTableExport(FrmBaseExport):
    """Dialog for exporting tabular rows to CSV, Excel, or JSON files."""

    def __init__(self, parent, data=None, base_name="table_export", project_path=None, export_type=None):
        super().__init__(parent, base_name=base_name, project_path=project_path, export_type=export_type)
        self.data = data
        self.setWindowTitle("Export Table")
        self.setup_export_ui(["CSV", "Excel", "JSON"])

    def get_headers(self):
        if not self.data:
            return []

        headers = list(self.data[0].keys())
        for row in self.data[1:]:
            for key in row.keys():
                if key not in headers:
                    headers.append(key)
        return headers

    def export_table(self, filename):
        if not self.data:
            return False, "No data available."

        headers = self.get_headers()
        if len(headers) < 1:
            return False, "No export columns were found."

        lower = filename.lower()
        if lower.endswith(".csv"):
            with open(filename, "w", newline="", encoding="utf-8") as export_file:
                writer = csv.DictWriter(export_file, fieldnames=headers, extrasaction="ignore")
                writer.writeheader()
                for row in self.data:
                    writer.writerow({key: row.get(key, "") for key in headers})
            return True, ""

        if lower.endswith(".json"):
            normalized = [{key: row.get(key, "") for key in headers} for row in self.data]
            with open(filename, "w", encoding="utf-8") as export_file:
                json.dump(normalized, export_file, ensure_ascii=False, indent=2)
            return True, ""

        if lower.endswith(".xlsx") or lower.endswith(".xls"):
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet("Export")

            for col, key in enumerate(headers):
                worksheet.write(0, col, key)

            for row_idx, row in enumerate(self.data):
                for col_idx, key in enumerate(headers):
                    worksheet.write(row_idx + 1, col_idx, row.get(key, ""))

            workbook.save(filename)
            return True, ""

        return False, "Unsupported output format."

    def accept(self):
        out_file = self.leFile.text() if self.leFile is not None else ""
        if not out_file:
            QtWidgets.QMessageBox.warning(self, "Export Table", "Please select an output file.")
            return

        success, msg = self.export_table(out_file)
        if success:
            super().accept()
            self.show_export_success(out_file)
        else:
            QtWidgets.QMessageBox.critical(self, "Export Failed", f"Error: {msg}")
