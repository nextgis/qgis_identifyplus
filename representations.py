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

from qgis.PyQt.QtWidgets import QTabWidget

from qgis.core import *
from qgis.gui import *

from .qgis_plugin_base import Plugin


class RepresentationsCache:
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
