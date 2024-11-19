# *****************************************************************************
#
# IdentifyPlus
# ---------------------------------------------------------
# Extended identify tool. Supports displaying and modifying photos.
#
# Copyright (C) 2012-2015 NextGIS (info@nextgis.com)
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# A copy of the GNU General Public License is available on the World Wide Web
# at <http://www.gnu.org/licenses/>. You can also obtain it by writing
# to the Free Software Foundation, 51 Franklin Street, Suite 500 Boston,
# MA 02110-1335 USA.
#
# *****************************************************************************

import os
from typing import List
from . import resources  # noqa: F401

from qgis.core import Qgis, QgsApplication
from qgis.gui import QgisInterface
from qgis.PyQt.QtCore import Qt, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox

from .aboutdialog import AboutDialog
from .identifyplusmaptool import IdentifyPlusMapTool
from .identifyplusresults import IdentifyPlusResults, IdentifyPlusResultsDock
from .identifytool import IdentifyTool
from .identifytools import allTools
from .qgis_plugin_base import Plugin


class IdentifyPlus(Plugin):
    iface: QgisInterface
    __activate_tool_action: QAction
    __open_about_dialog_action: QAction
    __identify_tool: IdentifyPlusMapTool
    __identify_results_dock: IdentifyPlusResultsDock
    __identify_results: IdentifyPlusResults

    def __init__(self, iface: QgisInterface) -> None:
        super().__init__(iface, "IdentifyPlus")
        self.iface = iface

        self.__init_translator()

    def initGui(self) -> None:
        if Qgis.QGIS_VERSION_INT < 30000:
            version = Qgis.QGIS_VERSION[: Qgis.version().find("-")]
            QMessageBox.warning(
                parent=self.iface.mainWindow(),
                title=self.tr("Error"),
                text=self.tr("QGIS {} detected.").format(version)
                + "\n"
                + self.tr(
                    "This version of IdentifyPlus requires at least QGIS version 3.0."
                )
                + "\n"
                + self.tr("Plugin will not be enabled."),
            )
            return

        self.__init_menus()
        self.__init_dock()
        self.__init_tool()

    def unload(self) -> None:
        self.__unload_tool()
        self.__unload_dock()
        self.__unload_menus()

    def tr(self, source_text: str) -> str:
        return QgsApplication.translate("IdentifyPlus", source_text)

    def getTargetIdentTools(self) -> List[IdentifyTool]:
        return allTools()

    def activateTool(self) -> None:
        self.iface.mapCanvas().setMapTool(self.__identify_tool)
        self.__activate_tool_action.setChecked(True)

    def __on_map_tool_changed(self, tool):
        if tool != self.__identify_tool:
            self.__activate_tool_action.setChecked(False)

    def about(self):
        dlg = AboutDialog("identifyplus")
        dlg.exec()

    def __init_translator(self):
        plugin_dir = os.path.dirname(__file__)
        locale = QgsApplication.instance().locale()
        locale_path = os.path.join(
            plugin_dir, "i18n", f"identifyplus_{locale}.qm"
        )

        if not os.path.exists(locale_path):
            return

        self.translator = QTranslator()
        self.translator.load(locale_path)
        QgsApplication.installTranslator(self.translator)

    def __init_menus(self):
        self.__activate_tool_action = QAction(
            self.tr("IdentifyPlus"), self.iface.mainWindow()
        )
        self.__activate_tool_action.setIcon(
            QIcon(":/plugins/identifyplus/icons/identifyplus.svg")
        )
        self.__activate_tool_action.setWhatsThis(
            self.tr("Extended identify tool")
        )
        self.__activate_tool_action.setCheckable(True)
        self.__activate_tool_action.triggered.connect(self.activateTool)
        self.iface.addPluginToMenu(
            self.tr("IdentifyPlus"), self.__activate_tool_action
        )
        self.iface.attributesToolBar().addAction(self.__activate_tool_action)

        self.__open_about_dialog_action = QAction(
            self.tr("About IdentifyPlus…"), self.iface.mainWindow()
        )
        self.__open_about_dialog_action.setIcon(
            QIcon(":/plugins/identifyplus/icons/about.png")
        )
        self.__open_about_dialog_action.setWhatsThis(
            self.tr("About IdentifyPlus")
        )
        self.__open_about_dialog_action.triggered.connect(self.about)
        self.iface.addPluginToMenu(
            self.tr("IdentifyPlus"), self.__open_about_dialog_action
        )

        self.__show_help_action = QAction(
            QIcon(":/plugins/identifyplus/icons/identifyplus.svg"),
            "NextGIS IdentifyPlus",
        )
        self.__show_help_action.triggered.connect(self.about)
        plugin_help_menu = self.iface.pluginHelpMenu()
        assert plugin_help_menu is not None
        plugin_help_menu.addAction(self.__show_help_action)

    def __unload_menus(self):
        self.iface.attributesToolBar().removeAction(
            self.__activate_tool_action
        )
        self.iface.removePluginMenu(
            self.tr("IdentifyPlus"), self.__activate_tool_action
        )
        self.__activate_tool_action.deleteLater()

        self.iface.removePluginMenu(
            self.tr("IdentifyPlus"), self.__open_about_dialog_action
        )
        self.__open_about_dialog_action.deleteLater()

    def __init_dock(self):
        self.__identify_results_dock = IdentifyPlusResultsDock()

        self.__identify_results = IdentifyPlusResults(
            self.__identify_results_dock
        )
        self.__identify_results_dock.setWidget(self.__identify_results)

        self.iface.addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea, self.__identify_results_dock
        )
        self.__identify_results_dock.hide()

    def __unload_dock(self):
        self.__identify_results_dock.setVisible(False)
        self.iface.removeDockWidget(self.__identify_results_dock)
        self.__identify_results_dock.deleteLater()

    def __init_tool(self):
        # prepare map tool
        self.__identify_tool = IdentifyPlusMapTool(self.iface.mapCanvas())
        Plugin().plPrint(">>> IdentifyPlusMapTool initialized")

        self.__identify_tool.avalableChanged.connect(
            self.__activate_tool_action.setEnabled
        )
        self.__activate_tool_action.setEnabled(
            self.__identify_tool.isAvalable()
        )

        self.iface.mapCanvas().mapToolSet.connect(self.__on_map_tool_changed)

        self.__identify_tool.identified.connect(
            self.__identify_results.appendIdentifyRes
        )
        self.__identify_tool.progressChanged.connect(
            self.__identify_results.progressShow
        )
        self.__identify_tool.identifyStarted.connect(
            self.__identify_results.identifyProcessStart
        )
        self.__identify_tool.identifyFinished.connect(
            self.__identify_results.identifyProcessFinish
        )
        self.__identify_tool.identifyStarted.connect(
            self.__identify_results_dock.show
        )
        self.__identify_tool.progressChanged.connect(
            self.__identify_results_dock.raise_
        )

    def __unload_tool(self):
        if self.iface.mapCanvas().mapTool() == self.__identify_tool:
            self.iface.mapCanvas().unsetMapTool(self.__identify_tool)

        self.iface.mapCanvas().mapToolSet.disconnect(
            self.__on_map_tool_changed
        )

        self.__identify_tool.deleteLater()
