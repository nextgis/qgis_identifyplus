# -*- coding: utf-8 -*-

#******************************************************************************
#
# IdentifyPlus
# ---------------------------------------------------------
# Extended identify tool. Supports displaying and modifying photos
#
# Copyright (C) 2012-2014 NextGIS (info@nextgis.org)
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

import xml.etree.ElementTree as ET
import json

from image_gallery.ngwImageAPI import *

def gdallocationinfoXMLOutputProcessing(outputXMLString):
    """
    return: [ErrCode, Data]
    """
    rootNode = None
    
    try:
        rootNode = ET.fromstring(outputXMLString)
    except ET.ParseError as err:
        return [1,"Input data error: " + err.msg]
        
    alert_node = rootNode.find('Alert')
    if (alert_node != None):
        return [2, alert_node.text]
    
    location_info_node = rootNode.find('BandReport').find('LocationInfo')
    if (location_info_node == None):
        return [3, "Not found LocationInfo tag"]
    
    try:
        jsonLocationInfo = json.JSONDecoder().decode(location_info_node.text.encode("utf-8"))
        
        if jsonLocationInfo.has_key("error"):
            err_msg = "Error code: " + str(jsonLocationInfo["error"]["code"]) + " message: \n" + jsonLocationInfo["error"]["message"]
            return [4, err_msg]
        else:
            results = []
            for r in jsonLocationInfo["results"]:
                results.append(r[u'attributes'])
            
            return [None, results]
    except ValueError as err:
        pass
    
    try:
        data = location_info_node.text.encode("utf-8")
        xmlLocationInfo = ET.fromstring(data)
        
        features = []
        for child in xmlLocationInfo:
            attrs = {}
            for k in child.attrib.keys():
                attrs.update({k: child.attrib[k]})
            
            features.append(attrs)
        
        return [None, features]
    except ValueError as err:
        pass
    except ET.ParseError as err:
        pass
    
    return [10, "Cann't parse input data"]

def getImageByURL(url, proxy):
    try:
      response = requests.get(url, proxies=proxy)
    except requests.exceptions.RequestException as err:
      raise KrasnogorskImageAPIError( "RequestException: %s"%(err.message) )
    except:
      raise KrasnogorskImageAPIError( "Common Exception: %s"%( str(sys.exc_info())) )

    if response.content is None or response.content == "":
      raise KrasnogorskImageAPIError( "<h1>Error: image not found</h1><p>Photo with ID %s not found using URL %s</p>" % (image.id, image.url) )
    
    img = QPixmap()
    img.loadFromData(QByteArray(response.content))
    
    return img