import base64
import html
import json
import os
from typing import ClassVar

from qgis.core import Qgis, QgsMessageLog, QgsProject, QgsSettings
from qgis.PyQt.QtCore import QSettings as _LegacyQSettings

from ...__version__ import __version__
from ..compat import MESSAGE_LEVEL_INFO, MESSAGE_LEVEL_WARNING
from .units import Units

with open(os.path.join(os.path.dirname(__file__), "..", "..", "config.json")) as cfg_file:
    cfg_json = json.load(cfg_file)

# Load the secrets.json file with sensitive information that is git ignored.
secrets_path = os.path.join(os.path.dirname(__file__), "..", "..", "secrets.json")
if os.path.isfile(secrets_path):
    with open(secrets_path) as cfg_file:
        secrets_json = json.load(cfg_file)
        if "constants" in secrets_json:
            cfg_json["constants"].update(secrets_json["constants"])

# We include these so that
_DEFAULTS = cfg_json["defaultSettings"]
CONSTANTS = cfg_json["constants"]

# BASE is the name we want to use inside the settings keys
MESSAGE_CATEGORY = CONSTANTS["logCategory"]


class SettingsBorg:
    _shared_state: ClassVar[dict] = {}
    _initdone = False

    def __init__(self):
        self.__dict__ = self._shared_state


# https://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/settings.html
# NB: We use json here to get better simple values back. This is a bit hack-y


class Settings(SettingsBorg):
    """
    Read up on the Borg pattern if you don't already know it. Super useful
    """

    def __init__(self, iface=None):
        SettingsBorg.__init__(self)

        self.units = Units("meter", "square_meter")

        # The iface is important as a pointer so we can get to the messagebar
        if iface is not None and "iface" not in self.__dict__:
            self.iface = iface
        if not self._initdone:
            self.proj = QgsProject.instance()
            self.s = QgsSettings()
            self.s.beginGroup(CONSTANTS["settingsCategory"])

            # Do a sanity check and reset anything that looks fishy
            for key in _DEFAULTS.keys():
                # self.setValue(key, _DEFAULTS[key])  # UNCOMMENT THIS FOR EMERGENCY RESET
                if key not in self.s.childKeys():
                    self.setValue(key, _DEFAULTS[key])

            # Remove any settings that aren't in the defaults. This way we don't get settings building
            # Up over time
            for key in self.s.childKeys():
                if key not in _DEFAULTS:
                    self.s.remove(key)

            # Must be the last thing we do in init
            self._initdone = True

        # ── One-time migration from legacy QSettings("Riverscapes", "QRiS") ──
        if not self.getValue("_migrated_from_legacy"):
            self._migrate_legacy_settings()

    # ─────────────────────────────────────────────────────────────────────
    # Legacy migration shim
    # ─────────────────────────────────────────────────────────────────────
    _LEGACY_ORGANIZATION = "Riverscapes"
    _LEGACY_APPNAME = "QRiS"

    # Mapping: legacy key → our key (same name in most cases)
    _LEGACY_KEY_MAP = {
        "dock_widget_location": "dock_widget_location",
        "remove_layers_on_close": "remove_layers_on_close",
        "default_export_path": "default_export_path",
        "local_protocol_folder": "local_protocol_folder",
        "show_experimental_protocols": "show_experimental_protocols",
        "default_chart_font": "default_chart_font",
        "last_project_folder": "last_project_folder",
        "recent_projects": "recent_projects",
    }

    def _migrate_legacy_settings(self):
        """
        One-time copy of settings from the old QSettings("Riverscapes", "QRiS")
        store (Windows registry) into the QgsSettings-backed Borg store.
        After copying, the legacy keys are cleared so they are never re-read.
        """
        try:
            legacy = _LegacyQSettings(self._LEGACY_ORGANIZATION, self._LEGACY_APPNAME)
            migrated_count = 0

            for legacy_key, our_key in self._LEGACY_KEY_MAP.items():
                # Read the legacy value (use None as default so we can detect absence)
                value = legacy.value(legacy_key, None)
                if value is not None:
                    # Write into our store
                    self.setValue(our_key, value)
                    # Clear the legacy key
                    legacy.remove(legacy_key)
                    migrated_count += 1

            # Mark migration as done (even if nothing was migrated, so we don't
            # keep checking on every init)
            self.setValue("_migrated_from_legacy", True)
            legacy.sync()

            if migrated_count > 0:
                self.log(
                    f"Migrated {migrated_count} legacy setting(s) from QSettings('{self._LEGACY_ORGANIZATION}', '{self._LEGACY_APPNAME}').",
                    level=MESSAGE_LEVEL_INFO,
                )
        except Exception as e:
            self.log(f"Legacy settings migration failed: {e}", level=MESSAGE_LEVEL_WARNING)
            # Don't re-raise — the plugin should still work with defaults

    @staticmethod
    def log(msg: str, level: Qgis.MessageLevel = MESSAGE_LEVEL_INFO):
        QgsMessageLog.logMessage(msg, MESSAGE_CATEGORY, level=level)

    def msg_bar(self, title: str, msg: str, level: Qgis.MessageLevel = MESSAGE_LEVEL_INFO, duration: int = 5):
        if self.iface is not None:
            self.iface.messageBar().pushMessage(title, msg, level=level, duration=duration)
        # Fall back to regular logging
        else:
            QgsMessageLog.logMessage(f"{title}: {msg}", MESSAGE_CATEGORY, level=level)

    def resetAllSettings(self):
        for key in _DEFAULTS.keys():
            self.setValue(key, _DEFAULTS[key])
        # Remove any settings that aren't in the defaults. This way we don't get settings building
        # Up over time
        for key in self.s.childKeys():
            if key not in _DEFAULTS:
                self.s.remove(key)

    def getValue(self, key):
        """
        Get one setting from the in-memory store and if not present then the settings file
        :return:
        """
        value = None
        try:
            default = _DEFAULTS[key] if key in _DEFAULTS else None
            value = json.loads(self.s.value(key, default))["v"]
        except Exception as e:
            print(e)
            value = None
        return value

    def setValue(self, key, value):
        """
        Write or overwrite a setting. Update the in-memory store  at the same time
        :param name:
        :param settings:
        :return:
        """
        # Set it in the file
        self.s.setValue(key, json.dumps({"v": value}))
        self.log(f"SETTINGS SET: {key}={value} of type '{html.escape(str(type(value)))}'", level=MESSAGE_LEVEL_INFO)

    def getSecureValue(self, key: str) -> str:
        """
        Get a value stored with light obfuscation (base64) in QgsSettings.
        Protected by OS user account — no QGIS master password required.
        """
        try:
            self.s.beginGroup("secure")
            raw = self.s.value(key, None)
            self.s.endGroup()
            if raw:
                return base64.b64decode(raw.encode()).decode("utf-8")
        except Exception as e:
            self.log(f"Error getting secure setting {key}: {e}", level=MESSAGE_LEVEL_WARNING)
        return None

    def setSecureValue(self, key: str, value: str):
        """
        Write a value with light obfuscation (base64) into QgsSettings.
        Protected by OS user account — no QGIS master password required.
        """
        try:
            self.s.beginGroup("secure")
            if value:
                self.s.setValue(key, base64.b64encode(value.encode()).decode("utf-8"))
            else:
                self.s.remove(key)
            self.s.endGroup()
            self.log(f"SETTINGS SET: {key}=<obfuscated>", level=MESSAGE_LEVEL_INFO)
        except Exception as e:
            self.log(f"Error setting secure setting {key}: {e}", level=MESSAGE_LEVEL_WARNING)

    def plugin_root_path(self):
        """Return absolute path to the plugin root directory."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def version(self) -> str:
        """Return the current QRiS plugin version."""
        return __version__

    def resource_path(self, *parts):
        """Build an absolute path under the plugin resources directory."""
        return os.path.join(self.plugin_root_path(), "resources", *parts)

    def _load_lookups(self) -> dict:
        """Load lookups JSON from configured path; return empty dict when unavailable."""
        lookups_json_path = self.getValue("lookupsJson")
        if not lookups_json_path or not os.path.exists(lookups_json_path):
            return {}

        try:
            with open(lookups_json_path, encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except Exception as e:
            self.log(f"Error loading lookups JSON: {e}", level=MESSAGE_LEVEL_WARNING)
            return {}

    def get_lookup_values(self, section: str, key: str) -> list:
        """Return lookup values from lookups.json section/key as a list of strings."""
        values = self._load_lookups().get(section, {}).get(key, [])
        if not isinstance(values, list):
            return []
        return [str(value) for value in values if value is not None]
