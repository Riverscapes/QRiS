import logging

from qgis.PyQt.QtCore import QObject, pyqtSignal

from .RSReportsAPI import RSReportsAPI

logger = logging.getLogger(__name__)


class ReportWorker(QObject):
    """Runs the report-generation flow in a background thread."""

    progress = pyqtSignal(str, int, str)  # status, progress%, message
    finished = pyqtSignal(dict)  # final report object
    error = pyqtSignal(str)  # error message

    def __init__(self, polygon_path: str, report_type_id: str | None = None):
        super().__init__()
        self.polygon_path = polygon_path
        self.report_type_id = report_type_id

    def run(self):
        try:
            api = RSReportsAPI()

            if not api.is_authenticated:
                self.progress.emit("AUTHENTICATING", 0, "Opening browser for sign in...")
                api.login()

            # Step 1: Look up report types (find the Rapid Assessment type)
            self.progress.emit("LOOKUP", 5, "Looking up report types...")
            report_type_id = self.report_type_id
            if report_type_id is None:
                types = api.get_report_types()
                # Find the first non-hidden report type
                visible = [t for t in types if not t.get("hidden", False)]
                if visible:
                    report_type_id = visible[0]["id"]
                    logger.info("Using report type: %s (%s)", visible[0]["name"], report_type_id)
                else:
                    raise RuntimeError("No visible report types found on the server.")

            # Step 2: Create the report
            self.progress.emit("CREATING", 10, "Creating report record...")
            report = api.create_report(
                name="NWP 27 Rapid Assessment Report",
                description="Automatically generated from the NWP 27 Wizard",
                report_type_id=report_type_id,
            )
            report_id = report["id"]
            creator_id = report["createdBy"]["id"]
            logger.info("Report created: %s", report_id)

            # Step 3: Get upload URL
            self.progress.emit("UPLOADING", 30, "Requesting upload URL...")
            uploads = api.get_upload_urls(report_id, ["input.geojson"], "INPUTS")
            if not uploads:
                raise RuntimeError("No upload URLs returned from server.")
            upload_info = uploads[0]

            # Step 4: Upload the GeoJSON
            self.progress.emit("UPLOADING", 40, "Uploading project extent...")
            api.upload_geojson_file(upload_info["url"], upload_info["fields"], self.polygon_path)

            # Step 5: Start the report
            self.progress.emit("STARTING", 50, "Starting report generation...")
            api.start_report(report_id)

            # Step 6: Poll for completion
            self.progress.emit("RUNNING", 60, "Report is being generated...")

            def on_progress(status, progress_pct, msg):
                mapped = 60 + int(progress_pct * 0.35)  # scale 0-100% → 60-95%
                self.progress.emit(status, min(mapped, 95), msg)

            final = api.poll_until_complete(report_id, progress_callback=on_progress)

            self.progress.emit("COMPLETE", 100, "Report generation complete!")
            final["_creator_id"] = creator_id
            self.finished.emit(final)

        except Exception as e:
            logger.exception("Report generation failed")
            self.error.emit(str(e))
