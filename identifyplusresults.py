# -*- coding: utf-8 -*-

#******************************************************************************
#
# IdentifyPlus
# ---------------------------------------------------------
# Extended identify tool. Supports displaying and modifying photos
#
# Copyright (C) 2012 NextGIS (info@nextgis.org)
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
import requests

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

from ui_identifyplusresultsbase import Ui_IdentifyPlusResults

API_SERVER = "http://gis-lab.info:8888"

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
    self.btnDeletePhoto.clicked.connect(self.deletePhoto)

    self.__setupProxy()

  def addFeature(self, feature):
    self.features.append(feature)

  def loadAttributes(self, fid):
    f = self.features[fid]
    attrMap = f.attributeMap()

    self.tblAttributes.clear()
    self.tblAttributes.setHorizontalHeaderLabels([self.tr("Name"), self.tr("Value")])
    self.tblAttributes.setRowCount(len(attrMap))
    self.tblAttributes.setColumnCount(2)

    row = 0
    fields = self.layer.pendingFields()
    for k, v in f.attributeMap().iteritems():
      fieldName = self.layer.attributeDisplayName(k)

      item = QTableWidgetItem(fieldName)
      self.tblAttributes.setItem(row, 0, item )

      item = QTableWidgetItem(v.toString())
      self.tblAttributes.setItem(row, 1, item )
      row += 1

    self.tblAttributes.resizeRowsToContents()
    self.tblAttributes.resizeColumnsToContents()
    self.tblAttributes.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)

    self.lblFeatures.setText(self.tr("Feature %1 from %2").arg(fid + 1).arg(len(self.features)))

    # load photo
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

    url = API_SERVER + "/api/%s/%s/images/" % (str(layerName), str(featureId))

    try:
      res = requests.get(url, proxies=self.proxy)
    except:
      print "requsts exception", sys.exc_info()

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

    self.lblPhotos.setText(self.tr("Photo %1 from %2").arg(pid + 1).arg(len(self.photos)))

    photoURL = self.photos[pid]["url"]
    url = API_SERVER + photoURL + "?type=preview"

    try:
      res = requests.get(url, proxies=self.proxy)
    except:
      print "requsts exception", sys.exc_info()

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
    lastDir = settings.value( "/lastPhotoDir", "." ).toString()

    formats = [ "*.%s" % unicode( format ).lower() for format in QImageReader.supportedImageFormats() ]
    fName = QFileDialog.getOpenFileName(self,
                                        self.tr("Open image"),
                                        lastDir,
                                        self.tr("Image files (%s)" % " ".join(formats))
                                       )

    if not fName.isEmpty():
      featureId = self.features[self.currentFeature].id()
      layerName = self.__getLayerName()

      url = API_SERVER + "/api/%s/%s/images/" % (str(layerName), str(featureId))
      files = {"data" : open(unicode(QFileInfo(fName).absoluteFilePath()), "rb")}

      try:
        res = requests.post(url, proxies=self.proxy, files=files)
      except:
        print "requsts exception", sys.exc_info()

      settings.setValue("/lastPhotoDir", QVariant(QFileInfo(fName).absolutePath()))

    self.getPhotos(self.currentFeature)

  def savePhoto(self):
    if self.photos is None or len(self.photos) == 0:
      return

    settings = QSettings("Krasnogorsk", "identifyplus")
    lastDir = settings.value( "/lastPhotoDir", "." ).toString()


    fName = QFileDialog.getSaveFileName(self,
                                        self.tr("Save image"),
                                        lastDir,
                                        self.tr("PNG files (*.png)")
                                       )
    if fName.isEmpty():
      return

    if not fName.toLower().endsWith(".png"):
      fName += ".png"

    # get fullsize image
    photoURL = self.photos[self.currentPhoto]["url"]
    url = API_SERVER + photoURL

    try:
      res = requests.get(url, proxies=self.proxy)
    except:
      print "requsts exception", sys.exc_info()

    if res.content is None or res.content == "":
      QMessageBox.information(self,
                              self.tr("No image"),
                              self.tr("Corresponding image not found")
                             )
      return

    img = QPixmap()
    img.loadFromData(QByteArray(res.content))
    img.save(fName)

    settings.setValue("/lastPhotoDir", QVariant(QFileInfo(fName).absolutePath()))

  def deletePhoto(self):
    if self.photos is None or len(self.photos) == 0:
      self.lblPhotos.setText(self.tr("No photos found"))
      return

    photoID = self.photos[self.currentFeature]["id"]
    url = API_SERVER + "/api/images/" + str(photoID)

    try:
      res = requests.delete(url, proxies=self.proxy)
    except:
      print "requsts exception", sys.exc_info()

    self.getPhotos(self.currentFeature)

  def clear(self):
    self.features = []
    self.photos = None
    self.currentFeature = 0
    self.currentPhoto = 0
    self.tblAttributes.clear()

  def show(self, layer):
    self.layer = layer
    self.loadAttributes(self.currentFeature)
    QDialog.show(self)
    self.raise_()

  def __setupProxy(self):
    settings = QSettings()
    if settings.value("/proxyEnabled", False).toBool():
      proxyType = settings.value("/proxyType", "Default proxy").toString()
      proxyHost = settings.value("/proxyHost", "").toString()
      proxyPost = settings.value("/proxyPort", 0).toUInt()[0]
      proxyUser = settings.value("/proxyUser", "").toString()
      proxyPass = settings.value("/proxyPassword", "").toString()

      # setup proxy
      connectionString = "http://%s:%s@%s:%s" % (proxyUser, proxyPass, proxyHost, proxyPort)
      self.proxy = {"http" : conectionString}

  def __getLayerName(self):
    if self.layer is None:
      return ""

    metadata = self.layer.source().split(" ")
    pos = metadata.indexOf(QRegExp("^table=.*"))
    tmp = metadata[pos]
    pos = tmp.indexOf(".")
    return tmp.mid(pos + 2, tmp.size() - pos - 3)
