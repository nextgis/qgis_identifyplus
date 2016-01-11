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
#******************************************************************************e

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from qgis_plugin_base import Plugin

# from ngw_external_api_python.core.ngw_utils import ngw_resource_from_qgs_map_layer


class RepresentationsCache(object):
    def __init__(self):
        self.repr_variants = list()
        self.indexes = list()
        self.correspondences = dict()
        
    def save(self, representations, index):
        if representations not in self.repr_variants:
            self.repr_variants.append(representations)
        
        reprs_index = self.repr_variants.index(representations)
        self.correspondences.update({reprs_index:index})
    
    def getIndex(self, representations):
        if representations in self.repr_variants:
            return self.correspondences[self.repr_variants.index(representations)]
        else:
            return 0


class RepresentationContainer(QTabWidget):
    def __init__(self, parent = None):
        QTabWidget.__init__(self, parent)
        self.threades = list()
        
        self.reprs_cashe = RepresentationsCache()
    
        self.currentChanged.connect(self.tabChangedHandle)
        
        self.__tools = list()

    def allReprs(self):
        reprs = []
        for i in range( 0, self.count() ):
            reprs.append(type(self.widget(i)))
        return reprs
    
    def tabChangedHandle(self, index):
        self.reprs_cashe.save(self.allReprs(), index) 
    
    def takeControl(self, obj, identifyTools):
        self.clear()
        # for provider in obj.providers:
        #     if isinstance(provider, QGISIdentificationTool):
        #         repr_widget = QGISAttributesView(self)                
        #         repr_widget.setModel(QGISAttributesModel(obj))
        #         tab_index = self.addTab(repr_widget, self.tr("Attributes"))
            
        #     if isinstance(provider, NGWIdentificationTool):
        #         #startTime = time.time()
                
        #         repr_widget = NGWImagesView(self)
        #         tab_index = self.addTab(repr_widget, self.tr("Photos") + " (ngw)")
        #         model = NGWImagesModel(obj, provider.ngw_resource)                                  
        #         repr_widget.setModel( model )
            
        #     if provider == SQLiteProvider:
        #         # repr_view = SQLiteAttributesView(self)
        #         # tab_index = self.addTab(repr_view, self.tr("SQLite"))
        #         # repr_view.setModel( SQLiteAttributesModel(obj, provider) )
        #         self.providerInst = provider()
        #         self.providerInst.identify(obj, self)
                
        # self.setCurrentIndex(self.reprs_cashe.getIndex(self.allReprs()))

        for toolCls in identifyTools:
            tool = toolCls()
            tool.identify(obj, self)
            self.__tools.append(tool)

    def addResult(self, widget, name):
        # Plugin().plPrint("addResult: " + name)
        widget.setParent(self)
        self.addTab(widget, name)

    def clear(self):
        self.__tools = list()
        for i in range( 0, self.count() ):
            self.widget(0).hide()
            self.widget(0).close()
            self.removeTab(0)

# class IdentificationTool(object):
#     def __init__(self, name, priority):
#         self.__name = name
#         self.__priority = priority
    
#     def __str__(self):
#         return self.__name + " data provider"
#     def __repr__(self):
#         return self.__name + " data provider"
    
#     @property
#     def name(self):
#         return self.__name
    
#     @property
#     def priority(self):
#         return self.__priority

#     @staticmethod
#     def isAvailable(qgsMapLayer):
#         return False
    
# class QGISIdentificationTool(IdentificationTool):
#     def __init__(self):
#         IdentificationTool.__init__(self, "qgis", 0)

#     @staticmethod
#     def isAvailable(identifyResultCls):
#         return True

# class NGWIdentificationTool(IdentificationTool):
#     def __init__(self, ngw_resource):
#         IdentificationTool.__init__(self, "ngw", 1)
#         self.__ngw_resource = ngw_resource
        
#     @property
#     def ngw_resource(self):
#         return self.__ngw_resource

#     @staticmethod
#     def isAvailable(qgsMapLayer):
#         if qgsMapLayer.type() != QgsMapLayer.VectorLayer:
#             return False

#         ngw_resource = ngw_resource_from_qgs_map_layer(qgsMapLayer)        
#         if ngw_resource is not None:
#             return True
#         return False

# class QGISVectorProvider(IdentificationTool, QObject):
#     def __init__(self):
#         IdentificationTool.__init__(self, "Base attributes", 1)
#         QObject.__init__(self)

#     @staticmethod
#     def isAvailable(qgsMapLayer):
#         if qgsMapLayer.type() == QgsMapLayer.VectorLayer:
#             return True

#         return False

# class SQLiteProvider(IdentificationTool, QObject):
#     def __init__(self):
#         IdentificationTool.__init__(self, "sqlite", 1)
#         QObject.__init__(self)

#     @property
#     def table_name(self):
#         return self.__table_name

#     @property
#     def sqlite_filename(self):
#         return self.__sqlite_filename

#     @staticmethod
#     def isAvailable(qgsMapLayer):
#         if qgsMapLayer.type() != QgsMapLayer.VectorLayer:
#             return False

#         if qgsMapLayer.dataProvider().name() != u"ogr":
#             return False

#         if qgsMapLayer.storageType() != u"SQLite":
#             return False

#         parts = qgsMapLayer.source().split('|')
#         for part in parts[1:]:
#             if part.startswith(u"layername"):
#                 return True

#         return False

#     def identify(self, obj, resultsContainer):
#         if not self.isAvailable(obj.qgsMapLayer):
#             return
        
#         self.__resultsContainer = resultsContainer

#         parts = obj.qgsMapLayer.source().split('|')
#         sqlite_filename = parts[0]

#         for part in parts[1:]:
#             if part.startswith(u"layername"):
#                 table_name = part.split('=')[1]

#         # model = SQLiteAttributesModel(obj.fid, sqlite_filename, table_name)
#         # view = SQLiteAttributesView()
#         # view.setModel(model)
#         # self.__resultsContainer.addResult(view, key)

#         thread = QThread(self)
#         worker = Worker(obj.fid, sqlite_filename, table_name)
#         worker.moveToThread(thread)
#         worker.refTableProcessed.connect(self.__addRefTableInfo)

#         thread.started.connect(worker.run)
#         thread.start()

#         self.worker = worker
#         self.thread = thread

#     def __addRefTableInfo(self, data):
#         # Plugin().plPrint("__addRefTableInfo: " + str(data))
#         model = QStandardItemModel()
#         model.setHorizontalHeaderLabels(["key", "value"])

#         for key, value in data.items():
#             Plugin().plPrint("key: " + str(key))
#             Plugin().plPrint("value: " + str(value))
        
#             view = SQLiteAttributesView()
        
#             view.setModel(model)
#             self.__resultsContainer.addResult(view, key)

#             #item = QStandardItem(key)
#             #self.model.appendRow([item, QStandardItem()])

#             self.__addItems(model, value)

#     def __addItems(self, parent, elements):
#         for text, children in elements:
#             item = QStandardItem(text)
#             if isinstance(children, list):
#                 parent.appendRow([item, QStandardItem()])
#                 if children:
#                     self.__addItems(item, children)
#             else:
#                 parent.appendRow([item, QStandardItem(unicode(children))])


# def provider_definition(qgsMapLayer):
#     provides = [ QGISIdentificationTool() ]
    
#     #if qgsMapLayer.type() == QgsMapLayer.RasterLayer:
#     #    provides.append(GDALIdentificationTool())
        
#     if qgsMapLayer.type() == QgsMapLayer.VectorLayer:
        
#         ngw_resource = ngw_resource_from_qgs_map_layer(qgsMapLayer)        
#         if ngw_resource is not None:            
#             provides.append(NGWIdentificationTool(ngw_resource))

#     if SQLiteProvider.isAvailable(qgsMapLayer):
#         provides.append(SQLiteProvider)        

#     Plugin().plPrint("providers: " + str(provides))
#     return provides

