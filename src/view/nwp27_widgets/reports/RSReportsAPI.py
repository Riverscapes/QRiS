"""
RSReportsAPI.py — Standalone client for the Riverscapes Reports GraphQL API.

Mirrors the Auth0 PKCE authentication flow from QRAVEPlugin's GraphQLAPI
but without any QGIS dependency.  Uses only the standard library + requests.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import socket
import threading
import time
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests

logger = logging.getLogger(__name__)

CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"


class RSReportsAPIError(Exception):
    pass


class RSReportsAPI:
    """Handles Auth0 authentication and GraphQL queries for the Reports API."""

    # Shared in-memory token across all instances (avoids re-auth)
    _shared_access_token: str | None = None
    _shared_token_expires: float | None = None
    _shared_auth_lock = threading.Lock()

    def __init__(
        self,
        graphql_url: str = "https://api.reports.riverscapes.net",
        auth_domain: str = "auth.riverscapes.net",
        auth_client_id: str = "pH1ADlGVi69rMozJS1cixkuL5DMVLhKC",
        auth_audience: str = "https://api.riverscapes.net",
        auth_scope: str = "openid",
        auth_port: int = 4721,
        auth_success_url: str = "https://data.riverscapes.net/login_success",
    ):
        self.graphql_url = graphql_url
        self.auth_domain = auth_domain
        self.auth_client_id = auth_client_id
        self.auth_audience = auth_audience
        self.auth_scope = auth_scope
        self.auth_port = auth_port
        self.auth_success_url = auth_success_url

        self.access_token: str | None = None
        self._token_lock = RSReportsAPI._shared_auth_lock

        # Try to reuse a shared token
        if RSReportsAPI._shared_access_token and RSReportsAPI._shared_token_expires and float(RSReportsAPI._shared_token_expires) > time.time() + 300:
            self.access_token = RSReportsAPI._shared_access_token
            logger.info("Using shared in-memory token (expires in %ds)",
                        int(float(RSReportsAPI._shared_token_expires) - time.time()))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def login(self, force: bool = False) -> None:
        """Perform the Auth0 PKCE login flow (opens browser)."""
        self._refresh_token(force=force)

    @property
    def is_authenticated(self) -> bool:
        return self.access_token is not None

    # ------------------------------------------------------------------
    # GraphQL helpers
    # ------------------------------------------------------------------

    def gql(self, query: str, variables: dict | None = None) -> dict:
        """Send a synchronous GraphQL query/mutation and return the JSON data.

        Retries once if the token has expired (re-authenticates).
        """
        if not self.access_token:
            self.login()

        headers = {"authorization": f"Bearer {self.access_token}"}
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        resp = requests.post(self.graphql_url, json=payload, headers=headers, timeout=30)
        if resp.status_code != 200:
            raise RSReportsAPIError(
                f"GraphQL request failed (HTTP {resp.status_code}): {resp.text}"
            )

        body = resp.json()
        if body.get("errors"):
            # Check for auth expiry — retry once
            msgs = [e.get("message", "") for e in body["errors"]]
            if any("authenticated" in m or "Unauthorized" in m or "unauthorized" in m for m in msgs):
                logger.info("Token expired; re-authenticating...")
                self.login(force=True)
                headers["authorization"] = f"Bearer {self.access_token}"
                resp = requests.post(self.graphql_url, json=payload, headers=headers, timeout=30)
                if resp.status_code != 200:
                    raise RSReportsAPIError(
                        f"GraphQL retry failed (HTTP {resp.status_code}): {resp.text}"
                    )
                body = resp.json()
                if body.get("errors"):
                    raise RSReportsAPIError(
                        f"GraphQL errors after re-auth: {body['errors']}"
                    )
            else:
                raise RSReportsAPIError(f"GraphQL errors: {body['errors']}")

        return body["data"]

    # ------------------------------------------------------------------
    # Report operations
    # ------------------------------------------------------------------

    def get_report_types(self) -> list[dict]:
        """List all available report types."""
        query = """
        query GetReportTypes {
          reportTypes {
            limit
            offset
            total
            items {
              id
              name
              shortName
              description
              version
              hidden
              parameters
            }
          }
        }
        """
        data = self.gql(query)
        return data["reportTypes"]["items"]

    def create_report(
        self,
        name: str,
        report_type_id: str,
        description: str = "",
        parameters: dict | None = None,
    ) -> dict:
        """Create a new report record (status = CREATED). Returns the report object."""
        query = """
        mutation CreateReport($report: RSReportInput!) {
          createReport(report: $report) {
            id
            name
            status
            progress
            createdAt
            outputs
            parameters
            reportType { id name }
            createdBy { id name }
          }
        }
        """
        if parameters is None:
            parameters = {"unitSystem": "imperial", "includeGeometries": False, "includePBI": False}

        variables = {
            "report": {
                "name": name,
                "description": description,
                "reportTypeId": report_type_id,
                "parameters": parameters,
            }
        }
        return self.gql(query, variables)["createReport"]

    def get_upload_urls(
        self, report_id: str, file_paths: list[str], file_type: str = "INPUTS"
    ) -> list[dict]:
        """Get pre-signed S3 upload URLs for input files."""
        query = """
        query GetUploadUrls($reportId: ID!, $filePaths: [String!]!, $fileType: FileTypeEnum!) {
          uploadUrls(reportId: $reportId, filePaths: $filePaths, fileType: $fileType) {
            fileType
            url
            fields
          }
        }
        """
        data = self.gql(query, {
            "reportId": report_id,
            "filePaths": file_paths,
            "fileType": file_type,
        })
        return data["uploadUrls"]

    def upload_geojson_file(
        self, upload_url: str, upload_fields: dict, geojson_path: str
    ) -> None:
        """Upload a GeoJSON file to S3 using the pre-signed URL and form fields."""
        with open(geojson_path, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

        geojson_bytes = json.dumps(geojson_data).encode("utf-8")

        files: dict[str, tuple] = {}
        for key, value in upload_fields.items():
            files[key] = (None, str(value))

        content_type = upload_fields.get("Content-Type", "application/geo+json")
        files["file"] = ("input.geojson", geojson_bytes, content_type)

        resp = requests.post(upload_url, files=files)
        resp.raise_for_status()
        logger.info("GeoJSON uploaded successfully (HTTP %s)", resp.status_code)

    def start_report(self, report_id: str) -> dict:
        """Start report processing (status → QUEUED)."""
        query = """
        mutation StartReport($reportId: ID!) {
          startReport(reportId: $reportId) {
            id
            status
            progress
            statusMessage
          }
        }
        """
        return self.gql(query, {"reportId": report_id})["startReport"]

    def get_report(self, report_id: str) -> dict:
        """Get the current state of a report."""
        query = """
        query GetReport($reportId: ID!) {
          report(reportId: $reportId) {
            id
            name
            status
            progress
            statusMessage
            outputs
            createdAt
            reportType { id name }
            createdBy { id name }
          }
        }
        """
        return self.gql(query, {"reportId": report_id})["report"]

    def poll_until_complete(
        self,
        report_id: str,
        interval_sec: int = 5,
        timeout_sec: int = 600,
        progress_callback: Callable[[str, int, str], None] | None = None,
    ) -> dict:
        """Poll the report until it reaches a terminal status.

        Calls *progress_callback* (status, progress, message) on each poll.
        """
        terminal = {"COMPLETE", "ERROR", "STOPPED", "DELETED"}
        start = time.time()

        while True:
            report = self.get_report(report_id)
            status = report["status"]
            progress = report.get("progress", 0)
            msg = report.get("statusMessage") or ""

            elapsed = time.time() - start
            logger.info("[%4.0fs] Status: %-10s Progress: %3d%%  %s",
                        elapsed, status, progress, msg)

            if progress_callback:
                progress_callback(status, progress, msg)

            if status in terminal:
                return report

            if elapsed > timeout_sec:
                raise RSReportsAPIError(
                    f"Report {report_id} did not complete within {timeout_sec}s"
                )

            time.sleep(interval_sec)

    def get_download_urls(
        self, report_id: str, file_types: list[str] | None = None
    ) -> list[dict]:
        """Get signed download URLs for report outputs."""
        if file_types is None:
            file_types = ["HTML", "PDF", "ZIP", "LOG"]

        query = """
        query GetDownloadUrls($reportId: ID!, $fileTypes: [FileTypeEnum!]) {
          downloadUrls(reportId: $reportId, fileTypes: $fileTypes) {
            fileType
            url
            fields
          }
        }
        """
        data = self.gql(query, {"reportId": report_id, "fileTypes": file_types})
        return data["downloadUrls"]

    @staticmethod
    def get_report_view_urls(creator_id: str, report_id: str) -> dict[str, str]:
        """Return human-readable URLs for the report outputs."""
        base = f"https://reports.riverscapes.net/reports/{creator_id}/{report_id}"
        return {
            "view": f"https://reports.riverscapes.net/report/{report_id}",
            "html": f"{base}/report.html",
            "pdf": f"{base}/report_static.pdf",
            "zip": f"{base}/report.zip",
            "log": f"{base}/report.log",
        }

    # ------------------------------------------------------------------
    # Auth0 PKCE internals (ported from QRAVEPlugin GraphQLAPI)
    # ------------------------------------------------------------------

    def _refresh_token(self, force: bool = False) -> None:
        logger.info("Authenticating on %s", self.graphql_url)

        if self._token_lock.locked():
            logger.info("Authentication already in progress — waiting for lock...")

        with self._token_lock:
            # Re-check shared token inside the lock
            if RSReportsAPI._shared_access_token and RSReportsAPI._shared_token_expires and float(RSReportsAPI._shared_token_expires) > time.time() + 300:
                self.access_token = RSReportsAPI._shared_access_token
                logger.info("Token fetched by another instance — reusing.")
                return

            if self.access_token and not force:
                logger.info("Token already exists — not refreshing.")
                return

            code_verifier = self._generate_random(128)
            code_challenge = self._generate_challenge(code_verifier)
            state = self._generate_random(32)

            redirect_url = f"http://localhost:{self.auth_port}/rscli/"
            login_url = urlparse(f"https://{self.auth_domain}/authorize")
            query_params = {
                "client_id": self.auth_client_id,
                "response_type": "code",
                "scope": self.auth_scope,
                "state": state,
                "audience": self.auth_audience,
                "redirect_uri": redirect_url,
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
            }
            login_url = login_url._replace(query=urlencode(query_params))

            # Open the browser
            import webbrowser
            webbrowser.open(urlunparse(login_url))

            auth_code = self._wait_for_auth_code()
            token_url = f"https://{self.auth_domain}/oauth/token"
            data = {
                "grant_type": "authorization_code",
                "client_id": self.auth_client_id,
                "code_verifier": code_verifier,
                "code": auth_code,
                "redirect_uri": redirect_url,
            }
            resp = requests.post(
                token_url,
                headers={"content-type": "application/x-www-form-urlencoded"},
                data=data,
                timeout=60,
            )
            resp.raise_for_status()
            token_data = resp.json()

            self.access_token = token_data["access_token"]
            expires_at = time.time() + token_data["expires_in"]

            # Share the token globally
            RSReportsAPI._shared_access_token = self.access_token
            RSReportsAPI._shared_token_expires = expires_at

            logger.info("Authentication successful")

    def _wait_for_auth_code(self) -> str:
        """Start a local HTTP server to receive the Auth0 callback."""

        class AuthHandler(BaseHTTPRequestHandler):
            def __init__(self, outer, *args, **kwargs):
                self.outer = outer
                super().__init__(*args, **kwargs)

            def log_message(self, fmt, *args):
                logger.info(fmt, *args)

            def do_GET(self):
                parsed = urlparse(self.path)
                params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
                self.server.query_resp = params
                success = "code" in self.server.query_resp and "error" not in self.server.query_resp

                body = (
                    "<html><body><p>Authentication successful. You may close this window.</p></body></html>"
                    if success
                    else f"<html><body><p>Authentication failed: {params}</p></body></html>"
                )
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(body.encode())
                self.server.shutdown()

        # Check port availability
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("", self.auth_port))
            except OSError:
                raise RSReportsAPIError(
                    f"Port {self.auth_port} is unavailable for the auth callback. "
                    "A VPN or firewall may be blocking it."
                )

        server = ThreadingHTTPServer(
            ("localhost", self.auth_port),
            lambda *args, **kwargs: AuthHandler(self, *args, **kwargs),
        )

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        start = time.time()
        while time.time() - start < 120:
            if not thread.is_alive():
                break
            time.sleep(0.5)

        if not hasattr(server, "query_resp"):
            server.shutdown()
            raise RSReportsAPIError("Authentication timed out or was cancelled.")

        if "error" in server.query_resp or "code" not in server.query_resp:
            raise RSReportsAPIError(
                f"Authentication failed: {json.dumps(server.query_resp)}"
            )

        return server.query_resp["code"]

    # ------------------------------------------------------------------
    # PKCE helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_challenge(code: str) -> str:
        return RSReportsAPI._base64_url(
            hashlib.sha256(code.encode("utf-8")).digest()
        )

    @staticmethod
    def _base64_url(data: bytes) -> str:
        return (
            base64.urlsafe_b64encode(data)
            .decode("utf-8")
            .replace("=", "")
            .replace("+", "-")
            .replace("/", "_")
        )

    @staticmethod
    def _generate_random(size: int) -> str:
        buffer = os.urandom(size)
        return "".join(CHARSET[b % len(CHARSET)] for b in buffer)
