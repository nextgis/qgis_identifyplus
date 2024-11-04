# *****************************************************************************
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
# *****************************************************************************

from qgis.gui import QgsDockWidget
from qgis.PyQt.QtWidgets import QWidget

from .qgis_plugin_base import Plugin
from .representations import RepresentationContainer
from .ui.identifyplusresultsbase import Ui_IdentifyPlusResults


class IdentifyPlusResults(QWidget, Ui_IdentifyPlusResults):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.setupUi(self)

        self._objects = list()
        self._identifyTools = list()

        self.currentObjectIndex = -1

        self.btnFirstRecord.clicked.connect(self.firstRecord)
        self.btnLastRecord.clicked.connect(self.lastRecord)
        self.btnNextRecord.clicked.connect(self.nextRecord)
        self.btnPrevRecord.clicked.connect(self.prevRecord)

        self.lblFeatures.setText(self.tr("No features"))

        self.btnFirstRecord.setEnabled(False)
        self.btnLastRecord.setEnabled(False)
        self.btnNextRecord.setEnabled(False)
        self.btnPrevRecord.setEnabled(False)

        self.representations = RepresentationContainer(self)
        self.loObjectContainer.addWidget(self.representations)

        self.progressBar.setVisible(False)
        self.progressBar.setFormat("%p%")
        self.progressBar.setTextVisible(True)

        self.pushButton.setVisible(False)
        self.lblIdentifyStatus.setVisible(False)

    def progressShow(self, cur, max):
        self.progressBar.setMaximum(max)
        self.progressBar.setValue(cur)

    def identifyProcessStart(self):
        self.lblFeatures.setText(self.tr("Identification..."))
        self._objects = list()
        self._identifyTools = list()
        self.currentObjectIndex = -1

        self.btnFirstRecord.setEnabled(False)
        self.btnLastRecord.setEnabled(False)
        self.btnNextRecord.setEnabled(False)
        self.btnPrevRecord.setEnabled(False)

        self.progressBar.show()

    def identifyProcessFinish(self):
        self.updateInterface()
        self.progressBar.setVisible(False)

    def appendIdentifyRes(self, res, identifyTools):
        Plugin().plPrint("appendIdentifyRes: " + str(res))
        self._objects.append(res)
        self._identifyTools.append(identifyTools)

        self.updateInterface()

        if len(self._objects) == 1:
            self.btnFirstRecord.setEnabled(True)
            self.btnLastRecord.setEnabled(True)
            self.btnNextRecord.setEnabled(True)
            self.btnPrevRecord.setEnabled(True)
            self.nextRecord()

    def firstRecord(self):
        self.currentObjectIndex = 0
        self._loadFeatureAttributes()

    def lastRecord(self):
        # self.currentObjectIndex = self.__model.objectsCount() - 1
        self.currentObjectIndex = len(self._objects) - 1
        self._loadFeatureAttributes()

    def nextRecord(self):
        self.currentObjectIndex += 1
        # if self.currentObjectIndex >= self.__model.objectsCount():
        if self.currentObjectIndex >= len(self._objects):
            self.currentObjectIndex = 0

        self._loadFeatureAttributes()

    def prevRecord(self):
        self.currentObjectIndex = self.currentObjectIndex - 1
        if self.currentObjectIndex < 0:
            self.currentObjectIndex = len(self._objects) - 1
            # self.currentObjectIndex = self.__model.objectsCount() - 1

        self._loadFeatureAttributes()

    def _loadFeatureAttributes(self):
        self.updateInterface()
        # obj = self.__model.data(self.currentObjectIndex)
        self.representations.takeControl(
            self._objects[self.currentObjectIndex],
            self._identifyTools[self.currentObjectIndex],
        )

    def updateInterface(self):
        if len(self._objects) > 0:
            self.lblFeatures.setText(
                self.tr("Feature %s from %s (%s)")
                % (
                    self.currentObjectIndex + 1,
                    # self.__model.objectsCount(),
                    len(self._objects),
                    # self.__model.data(self.currentObjectIndex).qgsMapLayer.name()
                    self._objects[self.currentObjectIndex]._qgsMapLayer.name(),
                )
            )
        else:
            self.lblFeatures.setText(self.tr("No features"))
            self.representations.clear()


class IdentifyPlusResultsDock(QgsDockWidget):
    def __init__(self):
        super().__init__(None)
        self.setWindowTitle(self.tr("IdentifyPlus"))
        self.setObjectName("IdentifyPlusResultsDock")
