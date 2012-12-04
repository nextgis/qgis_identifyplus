# -*- coding: utf-8 -*-

#******************************************************************************
#
# IdentifyPlus
# ---------------------------------------------------------
# Extended identify tool. Supports displaying and modifying photos
#
# Copyright (C) 2012 NextGIS (info@nextgis.org)
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

from ui_identifyplusresultsbase import Ui_IdentifyPlusResults

class IdentifyPlusResults(QDialog, Ui_IdentifyPlusResults):
  def __init__(self, canvas, parent):
    QDialog.__init__(self, parent)
    self.setupUi(self)

    self.canvas = canvas
    #self.layer = self.canvas.currentLayer()
    self.currentFeature = 0
    self.currentPhoto = 0
    self.features = []

    self.btnFirstRecord.clicked.connect(self.firstRecord)
    self.btnLastRecord.clicked.connect(self.lastRecord)
    self.btnNextRecord.clicked.connect(self.nextRecord)
    self.btnPrevRecord.clicked.connect(self.prevRecord)

  def addFeature(self, feature):
    self.features.append(feature)

  def loadAttributes(self, fid):
    f = self.features[fid]
    attrMap = f.attributeMap()

    self.tblAttributes.clear()
    self.tblAttributes.setHorizontalHeaderLabels([self.tr("Name"), self.tr("Value")])
    self.tblAttributes.setRowCount(len(attrMap))
    self.tblAttributes.setColumnCount(2)

    row = 0
    fields = self.layer.pendingFields()
    for k, v in f.attributeMap().iteritems():
      fieldName = self.layer.attributeDisplayName(k)

      item = QTableWidgetItem(fieldName)
      self.tblAttributes.setItem(row, 0, item )

      item = QTableWidgetItem(v.toString())
      self.tblAttributes.setItem(row, 1, item )
      row += 1

    self.tblAttributes.resizeRowsToContents()
    self.tblAttributes.resizeColumnsToContents()
    self.tblAttributes.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

    #self.tblAttributes.resizeColumnToContents(0)
    #self.tblAttributes.resizeColumnToContents(1)

    # load photo

    # update info
    self.lblFeatures.setText(self.tr("Feature %1 from %2").arg(fid + 1).arg(len(self.features)))

  def firstRecord(self):
    self.currentFeature = 0
    self.loadAttributes(self.currentFeature)

  def lastRecord(self):
    self.currentFeature = len(self.features) - 1
    self.loadAttributes(self.currentFeature)

  def nextRecord(self):
    self.currentFeature += 1
    if self.currentFeature >= len(self.features):
      self.currentFeature = 0

    self.loadAttributes(self.currentFeature)

  def prevRecord(self):
    self.currentFeature = self.currentFeature - 1
    if self.currentFeature < 0:
      self.currentFeature = len(self.features) - 1

    self.loadAttributes(self.currentFeature)

  def loadPhoto(self, fid, pid):
    pass

  def clear(self):
    self.tblAttributes.clear()

  def show(self, layer):
    self.layer = layer
    self.loadAttributes(self.currentFeature)
    QDialog.show(self)
    self.raise_()
