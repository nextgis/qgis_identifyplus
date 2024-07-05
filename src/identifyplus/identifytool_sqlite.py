# ******************************************************************************
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
# ******************************************************************************

import sqlite3

from qgis.core import QgsMapLayer, QgsMessageLog
from qgis.PyQt import QtCore, QtGui
from qgis.PyQt.QtCore import QCoreApplication

from .identifytool import IdentifyTool
from .qgis_plugin_base import Plugin


class Worker(QtCore.QObject):
    refTableProcessed = QtCore.pyqtSignal(dict)

    def __init__(self, fid, sqliteFilename, tableName, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.sqliteFilename = sqliteFilename
        self.tableName = tableName
        self.fid = fid

        # Plugin().plPrint("Init sqlite worker: %s (%s) %s" % (self.sqliteFilename, self.tableName, self.fid))

    def run(self):
        # Plugin().plPrint("Run sqlite worker")

        conn = sqlite3.connect(self.sqliteFilename)
        cur = conn.cursor()

        aliases = self.__getAliases(cur)

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [v[0] for v in cur.fetchall()]
        tables.remove(self.tableName)
        # Plugin().plPrint("tables: " + str(tables))

        pkFieldName = None
        cur.execute(f"PRAGMA table_info({self.tableName})")
        for field in cur.fetchall():
            if field[5] == 1:
                pkFieldName = field[1]
                break

        refTables = []
        for table in tables:
            cur.execute(f"PRAGMA foreign_key_list({table})")
            for field in cur.fetchall():
                if field[2] == self.tableName and field[4] == pkFieldName:
                    refTables.append([table, field[3]])
        # Plugin().plPrint("refTables: " + str(refTables))

        for table in refTables:
            data = []
            cur.execute(
                f"select * from {table[0]} where {table[1]}=={self.fid}"
            )

            rowIndex = 1
            for row in cur.fetchall():
                rowData = []
                for idx, col in enumerate(cur.description):
                    rowData.append(
                        (aliases.get(table[0]).get(col[0], col[0]), row[idx])
                    )

                data.append((str(rowIndex), rowData))
                rowIndex += 1

            self.refTableProcessed.emit(
                {aliases.get(table[0]).get(None, table[0]): data}
            )

    def __getAliases(self, cur):
        res = {}
        try:
            cur.execute("SELECT * FROM aliases")
            aliases = cur.fetchall()

            for alias in aliases:
                if alias[0] not in res:
                    res[alias[0]] = {}

                res[alias[0]][alias[1]] = alias[2]

        except Exception as err:
            Plugin().plPrint(
                "Find aliases in BD error: " + str(err), QgsMessageLog.WARNING
            )

        return res


class SQLiteTool(IdentifyTool):
    def __init__(self):
        IdentifyTool.__init__(self, "sqlite", "sqlite identification")

        self.__aliases = {}

    def identify(self, qgisIdentResultVector, resultsContainer):
        if not self.isAvailable(qgisIdentResultVector._qgsMapLayer):
            return

        self.__resultsContainer = resultsContainer

        parts = qgisIdentResultVector._qgsMapLayer.source().split("|")
        sqlite_filename = parts[0]

        for part in parts[1:]:
            if part.startswith("layername"):
                table_name = part.split("=")[1]

        # model = SQLiteAttributesModel(obj.fid, sqlite_filename, table_name)
        # view = SQLiteAttributesView()
        # view.setModel(model)
        # self.__resultsContainer.addResult(view, key)

        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels(
            [
                QCoreApplication.translate("QGISTool", "attribute"),
                QCoreApplication.translate("QGISTool", "value"),
            ]
        )
        self.view = QtGui.QTreeView()
        self.view.setModel(self.model)
        self.__is_added_to_container = False

        thread = QtCore.QThread(self.__resultsContainer)
        worker = Worker(
            qgisIdentResultVector.getFeature().id(),
            sqlite_filename,
            table_name,
        )
        worker.moveToThread(thread)
        worker.refTableProcessed.connect(self.__addRefTableInfo)

        thread.started.connect(worker.run)
        thread.start()

        self.worker = worker
        self.thread = thread

    def __addRefTableInfo(self, data):
        if self.__is_added_to_container is False:
            self.__resultsContainer.addResult(
                self.view,
                QCoreApplication.translate("QGISTool", "Reference tables"),
            )
            self.__is_added_to_container = True

        for key, value in list(data.items()):
            item = QtGui.QStandardItem(key)
            self.model.appendRow([item, QtGui.QStandardItem()])

            self.__addItems(item, value)

    def __addItems(self, parent, elements):
        for text, children in elements:
            item = QtGui.QStandardItem(text)
            if isinstance(children, list):
                parent.appendRow([item, QtGui.QStandardItem()])
                if children:
                    self.__addItems(item, children)
            else:
                parent.appendRow([item, QtGui.QStandardItem(str(children))])

    def __setAliases(self, aliases):
        self.__aliases = aliases

    @staticmethod
    def isAvailable(qgsMapLayer):
        if isinstance(qgsMapLayer, QgsMapLayer):
            if qgsMapLayer.type() != QgsMapLayer.VectorLayer:
                return False

            if qgsMapLayer.dataProvider().name() != "ogr":
                return False

            if qgsMapLayer.storageType() != "SQLite":
                return False

            parts = qgsMapLayer.source().split("|")
            for part in parts[1:]:
                if part.startswith("layername"):
                    return True

            return False

        return False
