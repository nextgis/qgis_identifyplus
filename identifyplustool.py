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
from qgis.gui import *

import identifyplusresults

import resources_rc

class IdentifyPlusTool(QgsMapTool):
  def __init__(self, canvas):
    QgsMapTool.__init__(self, canvas)

    self.canvas = canvas
    self.cursor = QCursor(QPixmap(":/icons/cursor.png"), 1, 1)
    self.results = identifyplusresults.IdentifyPlusResults(self.canvas, self.canvas.window())

  def activate(self):
    self.canvas.setCursor(self.cursor)

  def canvasReleaseEvent(self, event):
    self.results.clear()
    res = False

    layer = self.canvas.currentLayer()

    if layer is None:
      QMessageBox.warning(self.canvas,
                          self.tr("No active layer"),
                          self.tr("To identify features, you must choose an active layer by clicking on its name in the legend")
                         )
      return

    if layer.type() != QgsMapLayer.VectorLayer:
      QMessageBox.warning(self.canvas,
                          self.tr("Wrong layer type"),
                          self.tr("This tool works only for vector layers. Please select another layer in legend and try again")
                         )
      return
    '''
    if layer.providerType() != u"postgres":
      QMessageBox.warning(self.canvas,
                          self.tr("Wrong layer provider"),
                          self.tr("This tool works only for postgres layers. Please select another layer in legend and try again")
                         )
      return
    '''
    QApplication.setOverrideCursor(Qt.WaitCursor)
    res = self.identifyLayer(layer, event.x(), event.y())
    QApplication.restoreOverrideCursor()

    if res:
      self.results.show(layer)
    else:
      self.results.hide()
      QMessageBox.information(self.canvas,
                              self.tr("There is no appropriate objects"),
                              self.tr("To identify features, you must choose any object in an active layer"))

  def identifyLayer(self, layer, x, y):
    if layer.hasScaleBasedVisibility() and (layer.minimumScale() > self.canvas.mapRenderer().scale() or layer.maximumScale() <= self.canvas.mapRenderer().scale()):
      print "Out of scale"
      return False

    point = self.canvas.getCoordinateTransform().toMapCoordinates(x, y)

    # load identify radius from settings
    settings = QSettings()
    identifyValue = float(settings.value("/Map/identifyRadius", QGis.DEFAULT_IDENTIFY_RADIUS)) # в чем измеряется?
    ellipsoid = settings.value("/qgis/measure/ellipsoid", GEO_NONE) # неиспользуемая переменная

    if identifyValue <= 0.0: # а нужно ли если есть выше settings.value("/Map/identifyRadius", QGis.DEFAULT_IDENTIFY_RADIUS)
      identifyValue = QGis.DEFAULT_IDENTIFY_RADIUS

    featureCount = 0
    featureList = []

    try:
      searchRadius = self.canvas.extent().width() * (identifyValue / 100.0) # почему деление на 100?
      r = QgsRectangle()
      r.setXMinimum(point.x() - searchRadius)
      r.setXMaximum(point.x() + searchRadius)
      r.setYMinimum(point.y() - searchRadius)
      r.setYMaximum(point.y() + searchRadius)

      r = self.toLayerCoordinates(layer, r)

      rq = QgsFeatureRequest()
      rq.setFilterRect(r)
      rq.setFlags(QgsFeatureRequest.ExactIntersect)
      for f in layer.getFeatures(rq):
        featureList.append(QgsFeature(f))
    except QgsCsException as cse:
      print "Caught CRS exception", cse.what()

    myFilter = False

    renderer = layer.rendererV2() # неизвестность

    qgsVersion = int(unicode(QGis.QGIS_VERSION_INT))
    
    if renderer is not None and (renderer.capabilities() | QgsFeatureRendererV2.ScaleDependent):
      if qgsVersion < 20200 and qgsVersion > 10900:
        renderer.startRender( self.canvas.mapRenderer().rendererContext(), layer)
      elif qgsVersion >= 20300:
        renderer.startRender( self.canvas.mapRenderer().rendererContext(), layer.pendingFields())
      else:
        renderer.startRender( self.canvas.mapRenderer().rendererContext(), layer)
        
      myFilter = renderer.capabilities() and QgsFeatureRendererV2.Filter

    for f in featureList:
      if myFilter and not renderer.willRenderFeature(f): # какие-то фичи отсеивают
        continue

      featureCount += 1

      self.results.addFeature(f)

    if renderer is not None and (renderer.capabilities() | QgsFeatureRendererV2.ScaleDependent):
      renderer.stopRender(self.canvas.mapRenderer().rendererContext())

    return featureCount > 0
