from genericpath import isfile
import os
import json
import logging
import html

from qgis.core import QgsMessageLog, Qgis, QgsProject, QgsSettings

with open(os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')) as cfg_file:
    cfg_json = json.load(cfg_file)

# Load the secrets.json file with sensitive information that is git ignored.
secrets_path = os.path.join(os.path.dirname(__file__), '..', '..', 'secrets.json')
if os.path.isfile(secrets_path):
    with open(secrets_path) as cfg_file:
        secrets_json = json.load(cfg_file)
        if 'constants' in secrets_json:
            cfg_json['constants'].update(secrets_json['constants'])

# We include these so that
_DEFAULTS = cfg_json['defaultSettings']
CONSTANTS = cfg_json['constants']

# BASE is the name we want to use inside the settings keys
MESSAGE_CATEGORY = CONSTANTS['logCategory']


class SettingsBorg(object):
    _shared_state = {}
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

        # The iface is important as a pointer so we can get to the messagebar
        if iface is not None and 'iface' not in self.__dict__:
            self.iface = iface
        if not self._initdone:
            self.proj = QgsProject.instance()
            self.s = QgsSettings()
            self.s.beginGroup(CONSTANTS['settingsCategory'])

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

    def log(self, msg: str, level: Qgis.MessageLevel = Qgis.Info):
        QgsMessageLog.logMessage(msg, MESSAGE_CATEGORY, level=level)

    def msg_bar(self, title: str, msg: str, level: Qgis.MessageLevel = Qgis.Info, duration: int = 5):
        if self.iface is not None:
            self.iface.messageBar().pushMessage(title, msg, level=level, duration=duration)
        # Fall back to regular logging
        else:
            QgsMessageLog.logMessage("{}: {}".format(title, msg), MESSAGE_CATEGORY, level=level)

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
            value = json.loads(self.s.value(key, default))['v']
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
        self.log("SETTINGS SET: {}={} of type '{}'".format(key, value, html.escape(str(type(value)))), level=Qgis.Info)
