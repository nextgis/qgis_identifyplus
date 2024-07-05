# -*- coding: utf-8 -*-

# ******************************************************************************
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
# ******************************************************************************

from qgis.PyQt.QtCore import QAbstractTableModel, QModelIndex, Qt
from qgis.PyQt.QtWidgets import QTableView, QHeaderView

from qgis.core import *
from qgis.gui import *


class QGISAttributesModel(QAbstractTableModel):
    # def __init__(self, qgsFeature, parent = None):
    def __init__(self, identificationObject, parent=None):
        QAbstractTableModel.__init__(self, parent)

        self.__header = [self.tr("key"), self.tr("value")]

        self.__data = []

        # self.__data.extend( qgsIdentifyResult.mAttributes.items() )
        # QgsMessageLog.logMessage( str(qgsIdentifyResult.mAttributes.items()) , u'IdentifyPlus', QgsMessageLog.CRITICAL)
        # self.__data.extend( qgsIdentifyResult.mDerivedAttributes.items() )
        # QgsMessageLog.logMessage( str(qgsIdentifyResult.mDerivedAttributes.items()) , u'IdentifyPlus', QgsMessageLog.CRITICAL)
        # self.__data.extend( qgsIdentifyResult.mParams.items() )
        # QgsMessageLog.logMessage( str(qgsIdentifyResult.mParams.items()) , u'IdentifyPlus', QgsMessageLog.CRITICAL)
        self.__data.extend(list(identificationObject.attributes.items()))

        # qgsFeature = qgsIdentifyResult.mFeature
        # if qgsFeature is not None:
        #    qgsAttrs = qgsFeature.attributes()
        #    fields = qgsFeature.fields().toList()
        #    for i in xrange(len(qgsAttrs)):
        #        self.__data.extend( [(fields[i].name(), qgsAttrs[i])] )

    def rowCount(self, parent=QModelIndex()):
        return len(self.__data)

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        elif role != Qt.DisplayRole:
            return None

        return self.__data[index.row()][index.column()]

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.__header[section]
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return section + 1

        return None


class QGISAttributesView(QTableView):
    def __init__(self, parent=None):
        QTableView.__init__(self, parent)
        self.setWordWrap(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setResizeMode(QHeaderView.ResizeToContents)
        # QgsMessageLog.logMessage(
        #    "QGISAttributesView sizeHintForColumn: %s"%str(size),
        #    u'IdentifyPlus',
        #    QgsMessageLog.Info)

    def setModel(self, model):
        QTableView.setModel(self, model)
        # self.horizontalHeader().setDefaultSectionSize(10)
        # self.horizontalHeader().setMinimumSectionSize ( 10 )
        # self.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
