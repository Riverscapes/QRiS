# -*- coding: utf-8 -*-
"""
/***************************************************************************
 RIPT
                                 A QGIS plugin
 Riverscapes Integrated Planning Tool (RIPT)
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-05-06
        git sha              : $Format:%H$
        copyright            : (C) 2021 by North Arrow Research
        email                : info@northarrowresearch.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.core import QgsApplication
from .processing_provider.provider import Provider
from .classes.settings import Settings, CONSTANTS

# Initialize Qt resources from file resources.py
from . import resources

# Import the code for the DockWidget
from .ript_dockwidget import RIPTDockWidget
from .new_project_dialog import NewProjectDialog
from .ript_project import RiptProject
import os.path


class RIPTToolbar:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'RIPT_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Riverscapes Integrated Planning Tool (RIPT)')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'RIPT')
        self.toolbar.setObjectName(u'RIPT')

        self.settings = Settings(iface=self.iface)

        # print "** INITIALIZING RIPT"

        self.pluginIsActive = False
        self.dockwidget = None

    # noinspection PyMethodMayBeStatic

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('RIPT', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initProcessing(self):
        self.provider = Provider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # Initialize the processing framework
        self.initProcessing()

        icon_path = ':/plugins/ript_toolbar/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'QRiS'),
            callback=self.run,
            parent=self.iface.mainWindow())

        self.newProjectAction = QAction(QIcon(':/plugins/ript_toolbar/NewProject.png'), self.tr(u'new QRiS Project'), self.iface.mainWindow())
        self.newProjectAction.triggered.connect(self.newProjectDlg)
        self.toolbar.addAction(self.newProjectAction)

        self.openProjectAction = QAction(QIcon(':/plugins/ript_toolbar/OpenProject.png'), self.tr(u'Open QRiS Project'), self.iface.mainWindow())
        self.openProjectAction.triggered.connect(self.projectBrowserDlg)
        self.toolbar.addAction(self.openProjectAction)

        # self.addLayerAction = QAction(QIcon(':/plugins/ript_toolbar/AddToMap.png'), self.tr(u'new RIPT Project'), self.iface.mainWindow())
        # self.addLayerAction.triggered.connect(self.addLayerDlg)
        # self.addLayerAction.setEnabled(False)
        # self.toolbar.addAction(self.addLayerAction)

    # --------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # print "** CLOSING RIPT"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # Need to de-initialize the processing framework
        QgsApplication.processingRegistry().removeProvider(self.provider)

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Riverscapes Integrated Planning Tool (RIPT)'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    # --------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            # print "** STARTING RIPT"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget is None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = RIPTDockWidget()
                self.dockwidget.iface = self.iface

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

    def projectBrowserDlg(self):
        """
        Browse for a project directory
        :return:
        """
        last_browse_path = self.settings.getValue('lastBrowsePath')
        last_dir = os.path.dirname(last_browse_path) if last_browse_path is not None else None

        dialog_return = QFileDialog.getOpenFileName(self.dockwidget, "Open a RIPT project", last_dir, self.tr("RIPT Project files (project.ript)"))
        if dialog_return is not None and dialog_return[0] != "" and os.path.isfile(dialog_return[0]):
            # We set the proect path in the project settings. This way it will be saved with the QgsProject file
            if self.dockwidget is None or self.dockwidget.isHidden() is True:
                # self.toggle_widget(forceOn=True)
                project = RiptProject()
                project.load_from_project_file(dialog_return[0])
                self.openProject(project)

    def newProjectDlg(self):

        self.new_project_dlg = NewProjectDialog()
        self.new_project_dlg.dataChange.connect(self.openProject)

        # if ript_project is not None:
        #     # We set the proect path in the project settings. This way it will be saved with the QgsProject file
        #     if self.dockwidget is None or self.dockwidget.isHidden() is True:
        #         self.toggle_widget(forceOn=True)

    def toggle_widget(self, forceOn=False):
        """Toggle the widget open and closed when clicking the toolbar"""
        if not self.pluginIsActive:
            self.pluginIsActive = True

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget is None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = RIPTDockWidget()
                # self.metawidget = RIPTMetaWidget()
                # Hook metadata changes up to the metawidget
                # self.dockwidget.metaChange.connect(self.metawidget.load)

                # Run a network sync operation to get the latest stuff. Don't force it.
                #  This is just a quick check
                # self.net_sync_load()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            # self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.metawidget)
            self.dockwidget.show()

        else:
            if self.dockwidget is not None:
                if self.dockwidget.isHidden():
                    self.dockwidget.show()
                elif forceOn is False:
                    self.dockwidget.hide()

        # The metawidget always starts hidden
        # if self.metawidget is not None:
        #     self.metawidget.hide()

        # if self.dockwidget is not None and not self.dockwidget.isHidden():
        #     self.qproject.writeEntry(CONSTANTS['settingsCategory'], 'enabled', True)
        # else:
        #     self.qproject.removeEntry(CONSTANTS['settingsCategory'], 'enabled')

    def openProject(self, project):
        self.toggle_widget()
        self.dockwidget.openProject(project)
        # self.addLayerAction.setEnabled(True)

    def addLayerDlg(self):

        if self.dockwidget is not None:
            if self.dockwidget.current_project is not None:
                last_browse_path = self.settings.getValue('lastBrowsePath')
                last_dir = os.path.dirname(last_browse_path) if last_browse_path is not None else None

                dialog_return = QFileDialog.getOpenFileName(self.dockwidget, "Add GIS layer to RIPT project", last_dir, self.tr("GIS Data Sources (*.gpkg, *.tif)"))
                if dialog_return is not None and dialog_return[0] != "" and os.path.isfile(dialog_return[0]):
                    pass
            else:
                self.iface.messageBar().pushMessage("RIPT", "Cannot Add layer: No RIPT project is currently open.", level=1)

    def addLayer(self, layer):
        pass
