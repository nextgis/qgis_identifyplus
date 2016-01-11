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

import abc

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from qgis_plugin_base import Plugin

import resources_rc

class IdentifyPlusTool(QgsMapTool):
  used = pyqtSignal(QgsPoint)
  def __init__(self, canvas):
    QgsMapTool.__init__(self, canvas)
    self.canvas = canvas
    self.cursor = QCursor(QPixmap(":/plugins/identifyplus/icons/cursor.png"), 1, 1)
  
  def activate(self):
    self.canvas.setCursor(self.cursor)

  def canvasReleaseEvent(self, event):
    QApplication.setOverrideCursor(Qt.WaitCursor)
    self.used.emit( QgsPoint(event.x(), event.y()) )
    QApplication.restoreOverrideCursor()

  def isAvalable(self):
      return len(self.canvas.layers()) != 0


class QGISIdentResult(object):
    def __init__(self, qgsPoint):
        self.__qgsPoint = qgsPoint


class QGISIdentResultOnLayer(QGISIdentResult):
    def __init__(self, qgsPoint, qgsMapLayer):
        QGISIdentResult.__init__(self, qgsPoint)
        self._qgsMapLayer = qgsMapLayer

    @staticmethod
    @abc.abstractmethod
    def generateFromQgsMapLayer(qgsPoint, qgsMapLayer, qgsMapCanvas):
        return

class QGISIdentResultRaster(QGISIdentResultOnLayer):
    def __init__(self, qgsPoint, qgsMapLayer):
        QGISIdentResultOnLayer.__init__(self, qgsPoint, qgsMapLayer)

    @staticmethod
    def generateFromQgsMapLayer(qgsPoint, qgsMapLayer, qgsMapCanvas):
        yield QGISIdentResultRaster(qgsPoint, qgsMapLayer)

class QGISIdentResultVector(QGISIdentResultOnLayer):
    def __init__(self, qgsPoint, qgsFeature, qgsMapLayer):
        QGISIdentResultOnLayer.__init__(self, qgsPoint, qgsMapLayer)
        self.__qgsFeature = qgsFeature

    def getFeature(self):
        return self.__qgsFeature

    @staticmethod
    def generateFromQgsMapLayer(qgsPoint, qgsMapLayer, qgsMapCanvas):
        settings = QSettings()
        identifyValue = float(settings.value("/Map/searchRadiusMM", QGis.DEFAULT_IDENTIFY_RADIUS))
    
        if identifyValue <= 0.0:
            identifyValue = QGis.DEFAULT_IDENTIFY_RADIUS

        pointFrom = qgsMapCanvas.getCoordinateTransform().toMapCoordinates(
            qgsPoint.x() - identifyValue * qgsMapCanvas.PdmWidthMM, 
            qgsPoint.y() + identifyValue * qgsMapCanvas.PdmHeightMM)
            
        pointTo = qgsMapCanvas.getCoordinateTransform().toMapCoordinates(
            qgsPoint.x() + identifyValue * qgsMapCanvas.PdmWidthMM, 
            qgsPoint.y() - identifyValue * qgsMapCanvas.PdmHeightMM)
        
        try:
            #searchRadius = qgsMapCanvas.extent().width() * (identifyValue / 100.0)
            r = QgsRectangle()
            r.setXMinimum(pointFrom.x())
            r.setXMaximum(pointTo.x())
            r.setYMinimum(pointFrom.y())
            r.setYMaximum(pointTo.y())

            r = qgsMapCanvas.mapTool().toLayerCoordinates(qgsMapLayer, r)

            rq = QgsFeatureRequest()
            rq.setFilterRect(r)
            rq.setFlags(QgsFeatureRequest.ExactIntersect)
            for f in qgsMapLayer.getFeatures(rq):
                yield QGISIdentResultVector(qgsPoint, f, qgsMapLayer)
        
        except QgsCsException as cse:
            QgsMessageLog.logMessage(self.tr("Caught CRS exception") + ":\n" + cse.what(), u'IdentifyPlus', QgsMessageLog.CRITICAL)
        

def getQGISIdentResultClsForQgsLayer(qgsMapLayer):
    if qgsMapLayer.type() == QgsMapLayer.VectorLayer:
        return QGISIdentResultVector
    elif qgsMapLayer.type() == QgsMapLayer.RasterLayer:
        return QGISIdentResultRaster


class Worker(QObject):
    identifyStarted = pyqtSignal()
    identifyFinished = pyqtSignal()
    identified = pyqtSignal(QGISIdentResult, list)
    progressChanged = pyqtSignal(int, int)

    def __init__(self, qgsPoint, targetLayers, targetIdentTools, canvas):
        QObject.__init__(self)
        self.qgsPoint = qgsPoint
        self.targetLayers = targetLayers
        self.targetIdentTools = targetIdentTools
        self.canvas = canvas

        self.progressMax = len(self.targetLayers) + 1
        self.progress = -1

    def run(self):
        self.identifyStarted.emit()
        
        self.__progressUp()
        
        if len(self.targetLayers) == 0:
            resType = QGISIdentResult
            availableTools = [tool for tool in self.targetIdentTools if tool.isAvailable(resType)]

            if len(availableTools) != 0:
                self.identified.emit(resType(self.qgsPoint), availableTools)
        self.__progressUp()

        if len(self.targetLayers) > 0:
            for qgsLayer in self.targetLayers:
                availableTools = [tool for tool in self.targetIdentTools if tool.isAvailable(qgsLayer)]
                if len(availableTools) == 0:
                    continue    

                resType = getQGISIdentResultClsForQgsLayer(qgsLayer)
                for res in resType.generateFromQgsMapLayer(self.qgsPoint, qgsLayer, self.canvas):
                    self.identified.emit(res, availableTools)

                self.__progressUp()

        self.identifyFinished.emit()

    def __progressUp(self):
        self.progress += 1
        self.progressChanged.emit(self.progress, self.progressMax)


class IdentifyPlusMapTool(QgsMapTool):
    identifyStarted = pyqtSignal()
    identifyFinished = pyqtSignal()
    identified = pyqtSignal(QGISIdentResult, list)
    progressChanged = pyqtSignal(int, int)

    avalableChanged = pyqtSignal(bool)

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.cursor = QCursor(QPixmap(":/plugins/identifyplus/icons/cursor.png"), 1, 1)

        self.canvas().layersChanged.connect(self.checkAvalable)
        self.canvas().currentLayerChanged.connect(self.checkAvalable)

    def activate(self):
        self.canvas().setCursor(self.cursor)

    def canvasReleaseEvent(self, event):       
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        qgsPoint = QgsPoint(event.x(), event.y())
        targetIdentTools = Plugin().getTargetIdentTools()
        targetLayers = self.getTargetLayers()

        worker = Worker(qgsPoint, targetLayers, targetIdentTools, self.canvas())
        thread = QThread(self)
        worker.moveToThread(thread)

        worker.identifyStarted.connect(self.identifyStarted.emit)
        worker.identified.connect(self.identified.emit)
        worker.progressChanged.connect(self.progressChanged.emit)
        worker.identifyFinished.connect(self.identifyFinished.emit)
        worker.identifyFinished.connect(thread.quit)
        worker.identifyFinished.connect(thread.deleteLater)

        thread.started.connect(worker.run)

        thread.start()
        self.worker = worker
        self.thread = thread

        QApplication.restoreOverrideCursor()

    def isAvalable(self):
        # targetIdentTools = Plugin().getTargetIdentTools()
        # targetLayers = self.getTargetLayers()

        # Plugin().plPrint("targetLayers: " + str(targetLayers))

        # if len(targetLayers) == 0:
        #     resType = QGISIdentResult
        #     availableTools = [tool for tool in targetIdentTools if tool.isAvailable(resType)]
        #     if len(availableTools) != 0:
        #         return True

        # else:
        #     for qgsLayer in targetLayers:
        #         availableTools = [tool for tool in targetIdentTools if tool.isAvailable(qgsLayer)]
        #         if len(availableTools) != 0:
        #             return True                

        # return False

        return True

    def checkAvalable(self):
        self.avalableChanged.emit(self.isAvalable())

    def getTargetLayers(self):
        return self.canvas().layers()

    def getResultsTypes(self, targetLayers):
        resTypes =  []

        for qgsMapLayer in targetLayers:
            resType = getQGISIdentResultClsForQgsLayer(qgsMapLayer)
            resTypes.append(resType)

        if len(resTypes) == 0:
            resTypes.append(QGISIdentResult)

