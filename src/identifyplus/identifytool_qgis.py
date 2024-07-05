# -*- coding: utf-8 -*-

#******************************************************************************
#
# IdentifyPlus
# ---------------------------------------------------------
# Extended identify tool. Supports displaying and modifying photos.
#
# Copyright (C) 2012-2016 NextGIS (info@nextgis.com)
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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem
from qgis.PyQt.QtWidgets import QTableView, QHeaderView

from qgis.core import *

from .identifytool import *


class QGISTool(IdentifyTool):
    def __init__(self):
        IdentifyTool.__init__(self, "qgis", "simple qgis identification")

    def identify(self, qgisIdentResultVector, resultContainer):
        qgsFeature = qgisIdentResultVector.getFeature()
        aliases = qgisIdentResultVector._qgsMapLayer.attributeAliases()
        
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels([
            QCoreApplication.translate("QGISTool", "attribute"),
            QCoreApplication.translate("QGISTool", "value")
        ])

        view = QTableView()
        view.setModel(model)
        view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        view.setWordWrap(True)
        view.horizontalHeader().setStretchLastSection(True)
        view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        resultContainer.addResult(view, QCoreApplication.translate("QGISTool", "Base options"))

        qgsAttrs = qgsFeature.attributes()
        fields = qgsFeature.fields().toList()
        for i in range(len(qgsAttrs)):
            model.appendRow(
                [
                    QStandardItem(aliases.get(fields[i].name(), fields[i].name())),
                    QStandardItem(str(qgsAttrs[i]))
                ]
            )

    @staticmethod
    def isAvailable(qgsMapLayer):
        if isinstance(qgsMapLayer, QgsMapLayer):
            if qgsMapLayer.type() == QgsMapLayer.VectorLayer:
                return True

        return False