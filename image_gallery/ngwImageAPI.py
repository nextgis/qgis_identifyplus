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

import sys
import re
import requests
import abc
import numbers

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from PyQt4 import QtCore, QtGui, Qt, QtDeclarative

from qgis.core import *
from qgis.gui import *

import ImageGallery
from identifyplus.ngwapi import ngwapi

class KrasnogorskImageAPIError(ImageGallery.ImageGalleryError):
  def __init__(self, msg):
    self.msg = msg
  def __str__(self):
      return self.msg
      
class NGWImageAPIError(ImageGallery.ImageGalleryError):
    def __init__(self, msg):
        self.msg= msg
        
class KrasnogorskImageAPI(object):
  def __init__(self, host, proxy = None, header = None):
    self.host = host
    self.proxy = proxy
    self.header = header
    
  def getImages(self, **args):
    """
      layer_name
      feature_id
    """
    layer_name = args.get("layer_name")
    feature_id = args.get("feature_id")
    
    if (layer_name == None or feature_id == None):
      KrasnogorskImageAPIError("Not set layer_name or feature_id parameter")

    request_url = self.host + "/api/%s/%s/images/" % (str(layer_name), str(feature_id))
    
    
    try:
      response = requests.get(request_url, proxies=self.proxy, timeout=1.0)
    except requests.exceptions.RequestException as err:
      raise KrasnogorskImageAPIError( "RequestException: %s"%(err.message) )
    except:
      raise KrasnogorskImageAPIError( "Common Exception: %s"%( str(sys.exc_info())) )
    
    if response.status_code != 200:
      raise KrasnogorskImageAPIError( "RequestException: %s"%(res.text) )

    if response.json is None:
      raise KrasnogorskImageAPIError( "RequestException: %s"%("Response is empty") )
    
    images = []
    for image_info in response.json["images"]:
      image_url = image_info["url"]
      url = self.host + image_url
      url_preview = url + "?type=preview"
      images.append(ImageGallery.Image(image_info["id"], url, url_preview)) 
    
    return images

  def addImage(self, **args):
    """
      image_path
      layer_name
      feature_id
    """
    layer_name = args.get("layer_name")
    feature_id = args.get("feature_id")
    image_path = args.get("image_path")
    
    if (layer_name == None or feature_id == None or image_path == None):
      KrasnogorskImageAPIError("Not set layer_name or feature_id or image_path parameter")
      
    request_url = self.host + "/api/%s/%s/images/" % (str(layer_name), str(feature_id))
    file = {"data" : open(image_path, "rb")}

    try:
      response = requests.post(request_url, proxies=self.proxy, files=file, headers=self.header)
    except requests.exceptions.RequestException as err:
      raise KrasnogorskImageAPIError( "RequestException: %s"%(err.message) )
    except:
      raise KrasnogorskImageAPIError( "Common Exception: %s"%( str(sys.exc_info())) )
    
    if response.status_code != 200:
      raise KrasnogorskImageAPIError( "RequestException: %s"%(res.text) )
    
    added_image_info = response.json
    if added_image_info == None:
      raise KrasnogorskImageAPIError( "RequestException: %s"%("Response is empty") )
    
    # check addition
    images = self.getImages(**args)
    
    for image in images:
      if (image.url == self.host + added_image_info["url"]):
        return image
      
    raise KrasnogorskImageAPIError( "Image has not be added: %s"%(res.text) )
  
  def deleteImage(self, image):
    request_url = self.host + "/api/images/" + str(image.id)
    try:
      response = requests.delete(request_url, proxies=self.proxy, headers=self.header)
    except requests.exceptions.RequestException as err:
      raise KrasnogorskImageAPIError( "RequestException: %s"%(err.message) )
    except:
      raise KrasnogorskImageAPIError( "Common Exception: %s"%( str(sys.exc_info())) )

    if response.status_code != 204:
      raise KrasnogorskImageAPIError( "RequestException: %s"%(response.text) )
      return

class NGWImageAPI(object):
    def __init__(self):
        pass
        
    def getImages(self, **args):
        ngwResource = args.get("ngw_resource")
        featureId = args.get("feature_id")
        auth = args.get("auth")
        if (ngwResource == None or featureId == None):
            KrasnogorskImageAPIError("Not set ngwResource or feature_id parameter")
        
        try:
          imagesIds = ngwapi.ngwIdentification(ngwResource, featureId, auth).imagesIds
          
          if imagesIds is None:
            return []
            
          images = []
          for imageId in imagesIds:
            url = ngwResource.getURLForGetFeatureImage(featureId, imageId)
            url4preview = url + "?size=150x150"
            
            images.append(ImageGallery.Image(imageId, url, url4preview)) 
          
          return images
          
        except NGWAPIError as err:
          print "raise NGWImageAPIError(str(err))"
          raise NGWImageAPIError(str(err))
          

    def addImage(self, **args):
        pass
    def deleteImage(self, image):
        pass