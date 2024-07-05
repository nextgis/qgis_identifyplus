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

import sqlite3

from qgis.PyQt.QtCore import QObject, QThread, pyqtSignal
from qgis.PyQt.QtGui import QStandardItem, QStandardItemModel
from qgis.PyQt.QtWidgets import QTreeView

from .qgis_plugin_base import Plugin


class Worker(QObject):
    refTableProcessed = pyqtSignal(dict)

    def __init__(self, fid, sqliteFilename, tableName, parent=None):
        QObject.__init__(self, parent)
        self.sqliteFilename = sqliteFilename
        self.tableName = tableName
        self.fid = fid

        Plugin().plPrint(
            f"Init sqlite worker: {self.sqliteFilename} ({self.tableName}) {self.fid}"
        )

    def run(self):
        Plugin().plPrint("Run sqlite worker")

        conn = sqlite3.connect(self.sqliteFilename)
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [v[0] for v in cur.fetchall()]
        tables.remove(self.tableName)
        Plugin().plPrint("tables: " + str(tables))

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
        Plugin().plPrint("refTables: " + str(refTables))

        for table in refTables:
            data = []
            cur.execute(
                f"select * from {table[0]} where {table[1]}=={self.fid}"
            )

            rowIndex = 1
            for row in cur.fetchall():
                rowData = []
                for idx, col in enumerate(cur.description):
                    rowData.append((col[0], row[idx]))

                data.append((str(rowIndex), rowData))
                rowIndex += 1

            self.refTableProcessed.emit({table[0]: data})


class SQLiteAttributesModel(QStandardItemModel):
    def __init__(self, fid, sqlite_filename, table_name, parent=None):
        QStandardItemModel.__init__(self, parent)

        # self.__header = [self.tr("key"), self.tr("value")]
        self.setHorizontalHeaderLabels(["key", "value"])

        # self.__data = [["a",1],["b",2],["c",3]]
        # self.__data.extend(identificationObject.attributes.items())

        # self.addItems(self, self.__data)

        thread = QThread(self)
        worker = Worker(fid, sqlite_filename, table_name)
        worker.moveToThread(thread)
        worker.refTableProcessed.connect(self.addReferencedInfo)

        thread.started.connect(worker.run)
        thread.start()

        self.worker = worker
        self.thread = thread

    def addReferencedInfo(self, data):
        for key, value in list(data.items()):
            item = QStandardItem(key)
            self.appendRow([item, QStandardItem()])

            self.addItems(item, value)

    def addItems(self, parent, elements):
        for text, children in elements:
            item = QStandardItem(text)
            if isinstance(children, list):
                parent.appendRow([item, QStandardItem()])
                if children:
                    self.addItems(item, children)
            else:
                parent.appendRow([item, QStandardItem(str(children))])

    # def index(self, row, column, parent=QtCore.QModelIndex()):
    #     return self.createIndex(row, column)

    # def rowCount(self, parent=QtCore.QModelIndex()):
    #     return len(self.__data)

    # def columnCount(self, parent=QtCore.QModelIndex()):
    #     return 2

    # def data(self, index, role=QtCore.Qt.DisplayRole):
    #     if not index.isValid():
    #         return None
    #     elif role != QtCore.Qt.DisplayRole:
    #         return None

    #     return self.__data[index.row()][index.column()]

    # def headerData(self, section, orientation, role):
    #     if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
    #         return self.__header[section]
    #     elif orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
    #         return section+1

    #     return None


class SQLiteAttributesView(QTreeView):
    def __init__(self, parent=None):
        QTreeView.__init__(self, parent)
        self.setWordWrap(True)
        # self.horizontalHeader().setStretchLastSection(True)
        # self.verticalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)

    # def setModel(self, model):
    #     QtGui.QTableView.setModel(self, model)
    #     #self.horizontalHeader().setDefaultSectionSize(10)
    #     #self.horizontalHeader().setMinimumSectionSize ( 10 )
    #     #self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)
    #     self.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
    #     self.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
