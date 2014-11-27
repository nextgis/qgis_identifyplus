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
import re, requests, json
from urlparse import urlparse, parse_qs, urljoin

class NGWResource(object):
    def __init__(self, ngwBaseURL, jsonDescription):
        self._ngwBaseURL = ngwBaseURL
        self._model = None
        
        if isinstance(jsonDescription, dict):
            self._model = jsonDescription
            
    def __str__(self):
        return "NGWResource(base_url: %s, resource_id: %d)" %(self._ngwBaseURL, self.resourceId)
    
    @property
    def baseURL(self):
        return self._ngwBaseURL
    
    @property
    def resourceId(self):
        return self._model[u'resource'][u'id']
    
    @property
    def type(self):
        return self._model[u'resource'][u'cls']
    
class NGWResourceWFS(NGWResource):
    def __init__(self, ngwBaseURL, jsonDescription):
        NGWResource.__init__(self, ngwBaseURL, jsonDescription)
    
    def getLayerResourceIDByKeyname(self, keyname):
        for layerJson in self._model[u'wfsserver_service'][u'layers']:
            if layerJson[u'keyname'] == keyname:
                return int(layerJson['resource_id'])

class NGWResourceVectorLayer(NGWResource):
    def __init__(self, ngwBaseURL, jsonDescription):
        NGWResource.__init__(self, ngwBaseURL, jsonDescription)
        
    def getURLForIdentification(self, fid):
        return self.baseURL + u'/resource/%s/store/%d' % (self.resourceId, fid)
    def getURLForGetFeatureImage(self, fid, imageId):
        return self.baseURL + u'/layer/%d/feature/%d/photo/%d' % (self.resourceId, fid, imageId)

def _createNGWResource(ngwBaseURL, jsonDescription):
    if not isinstance(jsonDescription, dict):
        return None
        
    if jsonDescription[u'resource'][u'cls'] == "wfsserver_service":
        return NGWResourceWFS(ngwBaseURL, jsonDescription)
    elif jsonDescription[u'resource'][u'cls'] == "vector_layer":
        return NGWResourceVectorLayer(ngwBaseURL, jsonDescription)
    else:
        return None

def getNGWResource(ngwBaseURL, resourceId, (userName, userPassword)):
    jsonRequestURL = u'%s/api/resource/%d' %(ngwBaseURL, resourceId) 
    try:
        r = requests.get(jsonRequestURL, auth=(userName, userPassword))
        if r.status_code != 200:
            return None

        return _createNGWResource( ngwBaseURL, r.json())

    except requests.exceptions.RequestException as err:
        print err.msg()
        return None

def getNGWResourceFromQGSLayerSource(qgsLayerSource, (userName, userPassword)):
    baseURL = ""
    resourceID = 0
    
    if not isinstance(qgsLayerSource,unicode):
        return (None,None)
    
    o = urlparse(qgsLayerSource)
    m = re.search('^/\w+/resource/\d+/',o.path)
    if m is None:
        return (None,None)
    
    # o.path is '/<ngw service name>/resource/<resource id>/.......'
    # m.group() is '/<ngw service name>/resource/<resource id>/'
    basePathStructure = m.group().strip('/').split('/')
    baseURL = o.scheme + '://' + o.netloc + '/' + basePathStructure[0]
    resourceID = int(basePathStructure[2])
    
    additionAttrs = {}
    requestAttrs = parse_qs(o.query)
    if requestAttrs.get(u'TYPENAME') is not None:
        additionAttrs.update({u'LayerName': requestAttrs[u'TYPENAME'][0]})
    
    return (getNGWResource(baseURL, resourceID, (userName, userPassword)), additionAttrs)


class NGWIdentificationInfo(object):
    def __init__(self, jsonDescription):
        self._model = jsonDescription
    
    @property
    def imagesIds(self):
        if self._model["ext"]["feature_photo"] is None:
            return []
        return self._model["ext"]["feature_photo"]
    
def ngwIdentification(ngwResourceVectorLayer, fid):
    if not isinstance(ngwResourceVectorLayer, NGWResourceVectorLayer):
        return None
    
    request_url = ngwResourceVectorLayer.getURLForIdentification(fid)
    print "request_url: ", request_url
    try:
        response = requests.get(request_url, proxies=None, timeout=1.0, headers={"X-Feature-Ext":"*", "X-Requested-With":"XMLHttpRequest"})
        
        if response.status_code != 200:
            print "RequestException: %s" %(response.text)
            return None
        
        if response.json() is None:
            print "RequestException: %s"%("Response is empty")
            return None
        
        return NGWIdentificationInfo(response.json())
    
    except requests.exceptions.RequestException as err:
      print err.message
    
    return None


def main():
    wfsLayer = QgsVectorLayer(u'http://demo.nextgis.ru/ngw/resource/1311/wfs?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&TYPENAME=rukluobninsk4wfs&SRSNAME=EPSG:3857')
    geoJSONLayer = QgsVectorLayer(u'http://demo.nextgis.ru/ngw1/resource/1316/geojson/')
    
    auth = (u'administrator', u'admin')
    
    (ngwResource, addAttrs) = getNGWResourceFromQGSLayerSource(wfsLayer.source(), auth)
    if ngwResource is None:
        print "ngwResource unavailable"
        return
    
    ngwBaseURL = ngwResource.baseURL
    
    ngwResource4Identification = getNGWResource(ngwBaseURL, ngwResource.getLayerResourceIDByKeyname(addAttrs[u'LayerName']), auth)
    print "ngwResource4Identification: ", ngwResource4Identification
    
    imagesIds = ngwIdentification(ngwResource4Identification, 4).imagesIds
    print 'identyfication images: ', imagesIds
    for imageId in imagesIds:
        print "    ", ngwResource4Identification.getURLForGetFeatureImage(4, imageId)
    
    print getNGWResourceFromQGSLayerSource(geoJSONLayer.source(), auth)

if __name__=="__main__":
    from qgis.core import *
    main()