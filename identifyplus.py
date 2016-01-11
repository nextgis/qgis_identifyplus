# -*- coding: utf-8 -*-

#******************************************************************************
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
#******************************************************************************

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from qgis_plugin_base import Plugin
from identifytools import allTools

from identifyplusmaptool import IdentifyPlusMapTool
from identifyplusresults import IdentifyPlusResultsDock, IdentifyPlusResults

import aboutdialog
import resources_rc

class IdentifyPlus(Plugin):
  def __init__(self, iface):
    Plugin.__init__(self, iface, "identifyplus")

    self.iface = iface

    self.qgsVersion = unicode(QGis.QGIS_VERSION_INT)

    # For i18n support
    userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/identifyplus"
    systemPluginPath = QgsApplication.prefixPath() + "/python/plugins/identifyplus"

    overrideLocale = bool(QSettings().value("locale/overrideFlag", False, bool))
    if not overrideLocale:
      localeFullName = QLocale.system().name()[:2]
    else:
      localeFullName = QSettings().value("locale/userLocale", "")

    if QFileInfo(userPluginPath).exists():
      translationPath = userPluginPath + "/i18n/identifyplus_" + localeFullName + ".qm"
    else:
      translationPath = systemPluginPath + "/i18n/identifyplus_" + localeFullName + ".qm"
    
    self.localePath = translationPath
    if QFileInfo(self.localePath).exists():
      self.translator = QTranslator()
      self.translator.load(self.localePath)
      QCoreApplication.installTranslator(self.translator)

  def getTargetIdentTools(self):
    return allTools()

  def initGui(self):
    if int(self.qgsVersion) < 10900:
      qgisVersion = self.qgsVersion[0] + "." + self.qgsVersion[2] + "." + self.qgsVersion[3]
      QMessageBox.warning(self.iface.mainWindow(),
                           QCoreApplication.translate("IdentifyPlus", "Error"),
                           QCoreApplication.translate("IdentifyPlus", "QGIS %s detected.\n") % (qgisVersion) +
                           QCoreApplication.translate("IdentifyPlus", "This version of IdentifyPlus requires at least QGIS version 2.0.\nPlugin will not be enabled."))
      return None

    self.actionRun = QAction(QCoreApplication.translate("IdentifyPlus", "IdentifyPlus"), self.iface.mainWindow())
    self.actionRun.setIcon(QIcon(":/plugins/identifyplus/icons/identifyplus.svg"))
    self.actionRun.setWhatsThis("Extended identify tool")
    self.actionRun.setCheckable(True)
    self.actionRun.triggered.connect(self.run)
    #self.actionRun.triggered.connect(self.mapToolInit)
    
    self.actionAbout = QAction(QCoreApplication.translate("IdentifyPlus", "About IdentifyPlus..."), self.iface.mainWindow())
    self.actionAbout.setIcon(QIcon(":/plugins/identifyplus/icons/about.png"))
    self.actionAbout.setWhatsThis("About IdentifyPlus")
    self.actionAbout.triggered.connect(self.about)
    
    self.iface.addPluginToMenu(QCoreApplication.translate("IdentifyPlus", "IdentifyPlus"), self.actionRun)
    self.iface.addPluginToMenu(QCoreApplication.translate("IdentifyPlus", "IdentifyPlus"), self.actionAbout)
    self.iface.attributesToolBar().addAction(self.actionRun)

    
    # prepare map tool   
    self.mapTool = IdentifyPlusMapTool(self.iface.mapCanvas())
    self.mapTool.avalableChanged.connect(self.actionRun.setEnabled)
    self.actionRun.setEnabled(self.mapTool.isAvalable())
    self.iface.mapCanvas().mapToolSet.connect(self.mapToolChanged)
          
    self.dockWidget = IdentifyPlusResultsDock(self.iface.mainWindow())
    
    self.wIdentifyResults = IdentifyPlusResults(self.dockWidget)
    self.dockWidget.setWidget(self.wIdentifyResults)

    self.mapTool.identified.connect(self.wIdentifyResults.appendIdentifyRes)
    self.mapTool.progressChanged.connect(self.wIdentifyResults.progressShow)
    self.mapTool.identifyStarted.connect(self.wIdentifyResults.identifyProcessStart)
    self.mapTool.identifyFinished.connect(self.wIdentifyResults.identifyProcessFinish)
    self.mapTool.identifyStarted.connect(self.dockWidget.show)
     
    settings = QSettings();
    self.iface.addDockWidget( settings.value("identifyplus/dockWidgetArea", Qt.RightDockWidgetArea,  type=int), self.dockWidget)
    self.dockWidget.setFloating( settings.value("identifyplus/dockIsFloating", False, type=bool))
    self.dockWidget.resize( settings.value("identifyplus/dockWidgetSize", QSize(150, 300), type=QSize) )
    self.dockWidget.move( settings.value("identifyplus/dockWidgetPos", QPoint(500, 500), type=QPoint) )
    self.dockWidget.setVisible( settings.value("identifyplus/dockWidgetIsVisible", True, type=bool))
     
  def unload(self):
    self.iface.attributesToolBar().removeAction(self.actionRun)
    self.iface.removePluginMenu(QCoreApplication.translate("IdentifyPlus", "IdentifyPlus"), self.actionRun)
    self.iface.removePluginMenu(QCoreApplication.translate("IdentifyPlus", "IdentifyPlus"), self.actionAbout)
    
    if self.iface.mapCanvas().mapTool() == self.mapTool:
      self.iface.mapCanvas().unsetMapTool(self.mapTool)
    
    settings = QSettings();
    settings.setValue("identifyplus/dockIsFloating", self.dockWidget.isFloating())
    mw = self.iface.mainWindow()
    settings.setValue("identifyplus/dockWidgetArea", mw.dockWidgetArea(self.dockWidget))
    settings.setValue("identifyplus/dockWidgetSize", self.dockWidget.size())
    settings.setValue("identifyplus/dockWidgetPos", self.dockWidget.pos())
    settings.setValue("identifyplus/dockWidgetIsVisible", self.dockWidget.isVisible())
    
    self.iface.mapCanvas().mapToolSet.disconnect(self.mapToolChanged)
    
    del self.dockWidget
    del self.mapTool

  def run(self):
    self.iface.mapCanvas().setMapTool(self.mapTool)
    self.actionRun.setChecked(True)

  def mapToolChanged(self, tool):
    if tool != self.mapTool:
      self.actionRun.setChecked(False)
        
  def about(self):
    dlg = aboutdialog.AboutDialog()
    dlg.exec_()
