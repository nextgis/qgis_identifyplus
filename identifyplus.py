# -*- coding: utf-8 -*-

#******************************************************************************
#
# IdentifyPlus
# ---------------------------------------------------------
# Extended identify tool. Supports displaying and modifying photos
#
# Copyright (C) 2012-2013 NextGIS (info@nextgis.org)
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

import identifyplustool
import aboutdialog

import resources_rc

class IdentifyPlus:
  def __init__(self, iface):
    self.iface = iface

    self.qgsVersion = unicode(QGis.QGIS_VERSION_INT)

    # For i18n support
    userPluginPath = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/identifyplus"
    systemPluginPath = QgsApplication.prefixPath() + "/python/plugins/identifyplus"

    overrideLocale = bool(QSettings().value("locale/overrideFlag", False))
    if not overrideLocale:
      localeFullName = QLocale.system().name()
    else:
      localeFullName = QSettings().value("locale/userLocale", "")

    if QFileInfo(userPluginPath).exists():
      translationPath = userPluginPath + "/i18n/identifyplus_" + localeFullName + ".qm"
    else:
      translationPath = systemPluginPath + "/i18n/identifyplus_" + localeFullName + ".qm"
    
    print "translationPath: ", translationPath
    
    self.localePath = translationPath
    if QFileInfo(self.localePath).exists():
      self.translator = QTranslator()
      self.translator.load(self.localePath)
      QCoreApplication.installTranslator(self.translator)

  def initGui(self):
    if int(self.qgsVersion) < 10900:
      qgisVersion = self.qgsVersion[0] + "." + self.qgsVersion[2] + "." + self.qgsVersion[3]
      QMessageBox.warning(self.iface.mainWindow(),
                           QCoreApplication.translate("IdentifyPlus", "Error"),
                           QCoreApplication.translate("IdentifyPlus", "QGIS %s detected.\n") % (qgisVersion) +
                           QCoreApplication.translate("IdentifyPlus", "This version of IdentifyPlus requires at least QGIS version 2.0.\nPlugin will not be enabled."))
      return None

    self.actionRun = QAction(QCoreApplication.translate("IdentifyPlus", "IdentifyPlus"), self.iface.mainWindow())
    self.actionRun.setIcon(QIcon(":/icons/identifyplus.png"))
    self.actionRun.setWhatsThis("Extended identify tool")
    self.actionRun.setCheckable(True)

    self.actionAbout = QAction(QCoreApplication.translate("IdentifyPlus", "About IdentifyPlus..."), self.iface.mainWindow())
    self.actionAbout.setIcon(QIcon(":/icons/about.png"))
    self.actionAbout.setWhatsThis("About IdentifyPlus")

    self.iface.addPluginToVectorMenu(QCoreApplication.translate("IdentifyPlus", "IdentifyPlus"), self.actionRun)
    self.iface.addPluginToVectorMenu(QCoreApplication.translate("IdentifyPlus", "IdentifyPlus"), self.actionAbout)
    self.iface.addVectorToolBarIcon(self.actionRun)

    self.actionRun.triggered.connect(self.run)
    self.actionAbout.triggered.connect(self.about)

    # prepare map tool
    self.mapTool = identifyplustool.IdentifyPlusTool(self.iface.mapCanvas())
    self.iface.mapCanvas().mapToolSet.connect(self.mapToolChanged)

    # handle layer changes
    self.iface.currentLayerChanged.connect(self.toggleTool)

  def unload(self):
    self.iface.removeVectorToolBarIcon(self.actionRun)
    self.iface.removePluginVectorMenu(QCoreApplication.translate("IdentifyPlus", "IdentifyPlus"), self.actionRun)
    self.iface.removePluginVectorMenu(QCoreApplication.translate("IdentifyPlus", "IdentifyPlus"), self.actionAbout)

    if self.iface.mapCanvas().mapTool() == self.mapTool:
      self.iface.mapCanvas().unsetMapTool(self.mapTool)

    del self.mapTool

  def mapToolChanged(self, tool):
    if tool != self.mapTool:
      self.actionRun.setChecked(False)

  def run(self):
    self.iface.mapCanvas().setMapTool(self.mapTool)
    self.actionRun.setChecked(True)

  def toggleTool(self, layer):
    if layer is None:
      return

    if layer.type() != QgsMapLayer.VectorLayer:
      self.actionRun.setEnabled(False)
      if self.iface.mapCanvas().mapTool() == self.mapTool:
        self.iface.mapCanvas().unsetMapTool(self.mapTool)
    else:
      self.actionRun.setEnabled(True)

  def about(self):
    dlg = aboutdialog.AboutDialog()
    dlg.exec_()
