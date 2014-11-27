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
    
    self.results = identifyplusresults.IdentifyPlusResultsNew(self, self.canvas, self.canvas.window())
  
  def activate(self):
    self.canvas.setCursor(self.cursor)

  def canvasReleaseEvent(self, event):
    layer = self.canvas.currentLayer()
    if layer is None:
      QMessageBox.warning(self.canvas,
                          self.tr("No active layer"),
                          self.tr("To identify features, you must choose an active layer by clicking on its name in the legend")
                         )
      return
    
    QApplication.setOverrideCursor(Qt.WaitCursor)
    
    res = self.results.identify(layer, event.x(), event.y())
    
    QApplication.restoreOverrideCursor()
    
    if res:
      self.results.show()
    else:
      self.results.hide()
      if self.results.lastIdentifyErrorMsg is None:
          QMessageBox.information(self.canvas,
                              self.tr("There is no appropriate objects"),
                              self.tr("Unable to locate objects on the specified coordinates")
                              )
      else:
          QMessageBox.information(self.canvas,
                              self.tr("There is no appropriate objects"),
                              self.tr("Unable to locate objects on the specified coordinates")
                                + "<br/>" + self.tr("By reason of:") + "<br/>" + self.results.lastIdentifyErrorMsg
                              )

  def isAvalable(self, qgsMapLayer):
      return qgsMapLayer is not None