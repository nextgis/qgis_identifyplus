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

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from ui_identifyplusresultsbase import Ui_IdentifyPlusResults

API_PORT = ":8888"

DISABLED_FIELDS = ["FID", "ogc_fid", "gid", "osm_id"]

class IdentifyPlusResults(QDialog, Ui_IdentifyPlusResults):
  def __init__(self, canvas, parent):
    QDialog.__init__(self, parent)
    self.setupUi(self)

    self.canvas = canvas
    self.currentFeature = 0
    self.currentPhoto = 0
    self.features = []
    self.photos = None
    self.proxy = None
    self.host = None
    self.requestPhotos = True

    self.tabWidget.setCurrentIndex(0)

    self.btnFirstRecord.clicked.connect(self.firstRecord)
    self.btnLastRecord.clicked.connect(self.lastRecord)
    self.btnNextRecord.clicked.connect(self.nextRecord)
    self.btnPrevRecord.clicked.connect(self.prevRecord)

    self.btnFirstPhoto.clicked.connect(self.firstPhoto)
    self.btnLastPhoto.clicked.connect(self.lastPhoto)
    self.btnNextPhoto.clicked.connect(self.nextPhoto)
    self.btnPrevPhoto.clicked.connect(self.prevPhoto)

    self.btnLoadPhoto.clicked.connect(self.loadPhoto)
    self.btnSavePhoto.clicked.connect(self.savePhoto)
    self.btnSaveAllPhotos.clicked.connect(self.saveAllPhotos)
    self.btnDeletePhoto.clicked.connect(self.deletePhoto)

    self.__setupProxy()

  def addFeature(self, feature):
    self.features.append(feature)

  def loadAttributes(self, fid):
    f = self.features[fid]
    attrs = f.attributes()

    derived = self.getDerivedAttrs(f)

    self.tblAttributes.clear()
    self.tblAttributes.setHorizontalHeaderLabels([self.tr("Name"), self.tr("Value")])
    self.tblAttributes.setRowCount(len(attrs) + len(derived))
    self.tblAttributes.setColumnCount(2)

    row = 0
    for k, v in derived.iteritems():
      item = QTableWidgetItem(k)
      self.tblAttributes.setItem(row, 0, item )

      item = QTableWidgetItem(unicode(v))
      self.tblAttributes.setItem(row, 1, item )
      row += 1

    for i in xrange(len(attrs)):
      fieldName = self.layer.attributeDisplayName(i)

      if fieldName in DISABLED_FIELDS:
        self.tblAttributes.removeRow(self.tblAttributes.rowCount() - 1)
        continue

      item = QTableWidgetItem(fieldName)
      self.tblAttributes.setItem(row, 0, item )

      item = QTableWidgetItem(attrs[i])
      self.tblAttributes.setItem(row, 1, item )
      row += 1

    self.tblAttributes.resizeRowsToContents()
    self.tblAttributes.resizeColumnsToContents()
    self.tblAttributes.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

    self.lblFeatures.setText(self.tr("Feature %s from %s") % (fid + 1, len(self.features)))

    # load photo
    if self.requestPhotos:
      self.getPhotos(fid)

  def firstRecord(self):
    self.currentFeature = 0
    self.currentPhoto = 0
    self.loadAttributes(self.currentFeature)

  def lastRecord(self):
    self.currentFeature = len(self.features) - 1
    self.currentPhoto = 0
    self.loadAttributes(self.currentFeature)

  def nextRecord(self):
    self.currentFeature += 1
    if self.currentFeature >= len(self.features):
      self.currentFeature = 0

    self.currentPhoto = 0
    self.loadAttributes(self.currentFeature)

  def prevRecord(self):
    self.currentFeature = self.currentFeature - 1
    if self.currentFeature < 0:
      self.currentFeature = len(self.features) - 1

    self.currentPhoto = 0
    self.loadAttributes(self.currentFeature)

  def getPhotos(self, fid):
    featureId = self.features[fid].id()
    layerName = self.__getLayerName()

    url = self.host + "/api/%s/%s/images/" % (str(layerName), str(featureId))

    try:
      res = requests.get(url, proxies=self.proxy)
    except:
      print "requests exception", sys.exc_info()
      return

    if res.status_code != 200:
      self.showMessage(res.text)
      return

    if res.json is not None:
      self.photos = res.json["images"]

    self.currentPhoto = 0
    self.lblImage.setText(self.tr("No photo"))
    self.showPhoto(self.currentPhoto)

  def showPhoto(self, pid):
    if self.photos is None or len(self.photos) == 0:
      self.lblPhotos.setText(self.tr("No photos found"))
      self.lblImage.setText(self.tr("No photo"))
      return

    self.lblPhotos.setText(self.tr("Photo %s from %s") % (pid + 1, len(self.photos)))

    photoURL = self.photos[pid]["url"]
    url = self.host + photoURL + "?type=preview"

    try:
      res = requests.get(url, proxies=self.proxy)
    except:
      print "requests exception", sys.exc_info()

    if res.content is None or res.content == "":
      self.lblImage.setText(self.tr("No photo"))
      return

    img = QPixmap()
    img.loadFromData(QByteArray(res.content))
    self.lblImage.setPixmap(img)

  def firstPhoto(self):
    self.currentPhoto = 0
    self.showPhoto(self.currentPhoto)

  def lastPhoto(self):
    self.currentPhoto = len(self.photos) - 1
    self.showPhoto(self.currentPhoto)

  def nextPhoto(self):
    self.currentPhoto += 1
    if self.currentPhoto >= len(self.photos):
      self.currentPhoto = 0

    self.showPhoto(self.currentPhoto)

  def prevPhoto(self):
    self.currentPhoto = self.currentPhoto - 1
    if self.currentPhoto < 0:
      self.currentPhoto = len(self.photos) - 1

    self.showPhoto(self.currentPhoto)

  def loadPhoto(self):
    settings = QSettings("Krasnogorsk", "identifyplus")
    lastDir = settings.value( "/lastPhotoDir", "." )

    formats = ["*.%s" % unicode( format ).lower() for format in QImageReader.supportedImageFormats()]
    fName = QFileDialog.getOpenFileName(self,
                                        self.tr("Open image"),
                                        lastDir,
                                        self.tr("Image files (%s)" % " ".join(formats))
                                       )

    if not fName == "":
      featureId = self.features[self.currentFeature].id()
      layerName = self.__getLayerName()

      url = self.host + "/api/%s/%s/images/" % (str(layerName), str(featureId))
      files = {"data" : open(unicode(QFileInfo(fName).absoluteFilePath()), "rb")}

      try:
        res = requests.post(url, proxies=self.proxy, files=files, headers=self.header)
      except:
        print "requests exception", sys.exc_info()

      if res.status_code != 200:
        self.showMessage(res.text)
        return

      settings.setValue("/lastPhotoDir", QFileInfo(fName).absolutePath())

    self.getPhotos(self.currentFeature)

  def savePhoto(self):
    if self.photos is None or len(self.photos) == 0:
      return

    settings = QSettings("Krasnogorsk", "identifyplus")
    lastDir = settings.value( "/lastPhotoDir", "." )


    fName = QFileDialog.getSaveFileName(self,
                                        self.tr("Save image"),
                                        lastDir,
                                        self.tr("PNG files (*.png)")
                                       )
    if fName == "":
      return

    if not fName.lower().endswith(".png"):
      fName += ".png"

    # get fullsize image
    photoURL = self.photos[self.currentPhoto]["url"]
    url = self.host + photoURL

    try:
      res = requests.get(url, proxies=self.proxy)
    except:
      print "requests exception", sys.exc_info()

    if res.content is None or res.content == "":
      msg = self.tr("<h1>Error: image not found</h1><p>Photo with ID %s not found using URL %s</p>") % (self.photos[self.currentPhoto]["id"], self.photos[self.currentPhoto]["url"])
      self.showMessage(msg)
      return

    img = QPixmap()
    img.loadFromData(QByteArray(res.content))
    img.save(fName)

    settings.setValue("/lastPhotoDir", QFileInfo(fName).absolutePath())

  def saveAllPhotos(self):
    if self.photos is None or len(self.photos) == 0:
      return

    settings = QSettings("Krasnogorsk", "identifyplus")
    lastDir = settings.value( "/lastPhotoDir", "." )


    dirName = QFileDialog.getExistingDirectory(self,
                                               self.tr("Select directory"),
                                               lastDir,
                                               QFileDialog.ShowDirsOnly
                                              )
    if dirName == "":
      return

    # iterate over photos
    i = 0
    img = QPixmap()
    for p in self.photos:
      photoURL = p["url"]
      url = self.host + photoURL

      try:
        res = requests.get(url, proxies=self.proxy)
      except:
        print "requests exception", sys.exc_info()

      if res.content is None or res.content == "":
        print "Corresponding image not found"
        continue

      img.loadFromData(QByteArray(res.content))
      img.save("%s/%s.png" % (dirName, i))
      i += 1

    settings.setValue("/lastPhotoDir", QFileInfo(dirName).absolutePath())

  def deletePhoto(self):
    if self.photos is None or len(self.photos) == 0:
      self.lblPhotos.setText(self.tr("No photos found"))
      return

    photoID = self.photos[self.currentPhoto]["id"]
    url = self.host + "/api/images/" + str(photoID)

    try:
      res = requests.delete(url, proxies=self.proxy, headers=self.header)
    except:
      print "requests exception", sys.exc_info()

    if res.status_code != 204:
      self.showMessage(res.text)
      return

    self.getPhotos(self.currentFeature)

  def clear(self):
    self.features = []
    self.photos = None
    self.currentFeature = 0
    self.currentPhoto = 0
    self.tblAttributes.clear()

  def show(self, layer):
    self.layer = layer

    self.ellipsoid = QgsProject.instance().readEntry("Measure", "/Ellipsoid", GEO_NONE)[0]

    if self.layer.providerType() not in ["postgres"]:
      self.togglePhotoTab(False)
    else:
      self.togglePhotoTab(True)

    if not self.__canEditLayer():
      self.toggleEditButtons(False)
    else:
      self.toggleEditButtons(True)

    self.host = "http://" + unicode(self.__getDBHost()) + API_PORT

    userName, password = self.__getCredentials()
    if userName is not None and password is not None:
      self.header = {"X-Role" : unicode(userName), "X-Password" : unicode(password)}
    else:
      self.header = None
      self.toggleEditButtons(False)

    self.loadAttributes(self.currentFeature)
    QDialog.show(self)
    self.raise_()

  def togglePhotoTab(self, enable):
    self.requestPhotos = enable
    self.tabWidget.setTabEnabled(1, enable)

  def toggleEditButtons(self, enable):
    self.btnLoadPhoto.setEnabled(enable)
    self.btnDeletePhoto.setEnabled(enable)

  def showMessage(self, message):
    msgViewer = QgsMessageViewer(self)
    msgViewer.setCheckBoxVisible(False)
    msgViewer.setMessageAsHtml(message)
    msgViewer.showMessage()

  def getDerivedAttrs(self, feature):
    if self.layer is None:
      return None

    calc = QgsDistanceArea()

    calc.setEllipsoidalMode(self.canvas.hasCrsTransformEnabled())
    calc.setEllipsoid(self.ellipsoid)
    calc.setSourceCrs(self.layer.crs().srsid())

    attrs = dict()

    if self.layer.geometryType() == QGis.Line:
      dist = calc.measure(feature.geometry())
      dist, myDisplayUnits = self.__convertUnits(calc, dist, False)
      res = calc.textUnit(dist, 3, myDisplayUnits, False)
      attrs[self.tr("Length")] = res

      if feature.geometry().wkbType() in [QGis.WKBLineString, QGis.WKBLineString25D]:
        pnt = self.canvas.mapRenderer().layerToMapCoordinates(self.layer, feature.geometry().asPolyline()[0])
        res = QLocale.system().toString(pnt.x(), 'g', 10)
        attrs[self.tr("firstX")] = res
        res = QLocale.system().toString(pnt.y(), 'g', 10)
        attrs[self.tr("firstY")] = res

        pnt = self.canvas.mapRenderer().layerToMapCoordinates(self.layer, feature.geometry().asPolyline()[len(feature.geometry().asPolyline())])
        res = QLocale.system().toString(pnt.x(), 'g', 10)
        attrs[self.tr("lastX")] = res
        res = QLocale.system().toString(pnt.y(), 'g', 10)
        attrs[self.tr("lastY")] = res
    elif self.layer.geometryType() == QGis.Polygon:
      area = calc.measure(feature.geometry())
      perimeter = calc.measurePerimeter(feature.geometry())
      area, myDisplayUnits = self.__convertUnits(calc, area, True)
      res = calc.textUnit(area, 3, myDisplayUnits, True)
      attrs[self.tr("Area")] = res

      perimeter, myDisplayUnits = self.__convertUnits(calc, perimeter, False)
      res = calc.textUnit(perimeter, 3, myDisplayUnits, False)
      attrs[self.tr("Perimeter")] = res
    elif self.layer.geometryType() == QGis.Point and feature.geometry().wkbType() in [QGis.WKBPoint, QGis.WKBPoint25D]:
      pnt = self.canvas.mapRenderer().layerToMapCoordinates(self.layer, feature.geometry().asPoint())
      res = QLocale.system().toString(pnt.x(), 'g', 10)
      attrs[self.tr("X")] = res
      res = QLocale.system().toString(pnt.y(), 'g', 10)
      attrs[self.tr("Y")] = res

    return attrs

  def __setupProxy(self):
    settings = QSettings()
    if bool(settings.value("/proxyEnabled", False)):
      proxyType = settings.value("/proxyType", "Default proxy")
      proxyHost = settings.value("/proxyHost", "")
      proxyPost = int(settings.value("/proxyPort", 0))
      proxyUser = settings.value("/proxyUser", "")
      proxyPass = settings.value("/proxyPassword", "")

      # setup proxy
      connectionString = "http://%s:%s@%s:%s" % (proxyUser, proxyPass, proxyHost, proxyPort)
      self.proxy = {"http" : conectionString}

  def __getLayerName(self):
    if self.layer is None:
      return ""

    metadata = self.layer.source().split(" ")
    regex = re.compile("^table=.*")
    pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
    tmp = metadata[pos]
    pos = tmp.find(".")
    return tmp[pos + 2:-1]

  def __getDBHost(self):
    if self.layer is None:
      return ""

    metadata = self.layer.source().split(" ")
    regex = re.compile("^host=.*")
    pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
    tmp = metadata[pos]
    pos = tmp.find("=")
    return tmp[pos + 1:]

  def __getCredentials(self):
    if self.layer is None:
      return (None, None)

    metadata = self.layer.source().split(" ")
    regex = re.compile("^user=.*")
    pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
    tmp = metadata[pos]
    pos = tmp.find("=")
    userName = tmp[pos + 2:-1]

    regex = re.compile("^password=.*")
    pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
    tmp = metadata[pos]
    pos = tmp.find("=")
    password = tmp[pos + 2:-1]

    if userName == "" or password == "":
      regex = re.compile("^dbname=.*")
      pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
      dbname = metadata[pos]

      regex = re.compile("^host=.*")
      pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
      host = metadata[pos]

      regex = re.compile("^port=.*")
      pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
      port = metadata[pos]

      regex = re.compile("^sslmode=.*")
      pos = metadata.index([m.group(0) for l in metadata for m in [regex.search(l)] if m][0])
      ssl = metadata[pos]

      realm = "%s %s %s %s" % (dbname, host, port, sslmode)

      res, userName, password = QgsCredentials.instance().get(realm, userName, password)
      if userName == "" or password == "":
        print "Can't get user credentials"
        return (None, None)

      QgsCredentials.instance().put(realm, userName, password)

    return (userName, password)

  def __canEditLayer(self):
    if self.layer is None:
      return False

    canChangeAttributes = self.layer.dataProvider().capabilities() & QgsVectorDataProvider.ChangeAttributeValues

    return canChangeAttributes and not self.layer.isReadOnly()

  def __convertUnits(self, calc, measure, isArea):
    myUnits = self.canvas.mapUnits()
    settings = QSettings("QGIS", "QGIS")
    displayUnits = QGis.fromLiteral(settings.value("/qgis/measure/displayunits", QGis.toLiteral(QGis.Meters)))
    measure, myUnits = calc.convertMeasurement(measure, myUnits, displayUnits, isArea)
    return (measure, myUnits)
