# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, Qt, QtDeclarative

import sys

class ImageGalleryError(Exception):
  def __init__(self, msg):
    self.msg = msg
  def __str__(self):
    return repr(self.value)
  
class Image(object):
    def __init__(self, id, url, url_preview = None):
        self.id = id
        self.url = url
        if (url_preview is None):
          self.url_preview = url
        else:
          self.url_preview = url_preview
        
class ImageWrapper(QtCore.QObject):
    def __init__(self, image):
        QtCore.QObject.__init__(self)
        self._image = image
 
    def _url(self):
        return str(self._image.url)
    
    def _url_preview(self):
        return str(self._image.url_preview)
      
    def _id(self):
        return str(self._image.id)
 
    changed = QtCore.pyqtSignal()
 
    url_preview = QtCore.pyqtProperty(unicode, _url_preview, notify=changed)
    url = QtCore.pyqtProperty(unicode, _url, notify=changed)
    id = QtCore.pyqtProperty(unicode, _id, notify=changed)
    

class IamgeGalleryModel(QtCore.QAbstractListModel):
  COLUMNS = ('image',)
  
  updateGallery = QtCore.pyqtSignal()
  changed = QtCore.pyqtSignal()
  
  def __init__(self, data_provider):
    QtCore.QAbstractListModel.__init__(self)
    self.setRoleNames(dict(enumerate(IamgeGalleryModel.COLUMNS)))
    self.__data_provider = data_provider
    self.__images = []
  
  def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.__images)
      
  count = QtCore.pyqtProperty(int, rowCount, notify=changed)
  
  def data(self, index, role):
      if index.isValid() and role == IamgeGalleryModel.COLUMNS.index('image'):
          return self.__images[index.row()]
      return None
  
  def loadImages(self, **args):
    images = self.__data_provider.getImages(**args)
    del self.__images
    self.__images = []
    for image in images:
      self.__images.append( ImageWrapper(image) )

    self.modelReset.emit()
    self.updateGallery.emit()
  
  def addImage(self, **args):
    added_image = self.__data_provider.addImage(**args)
    self.__images.append( ImageWrapper(added_image) )
    self.modelReset.emit()
    self.updateGallery.emit()
  
  def deleteImage(self, image):
    self.__data_provider.deleteImage(image)
    self.__images.remove(image)
    self.modelReset.emit()
    self.updateGallery.emit()
    
  def getAllImagesInfo(self):
    images_info = []
    for image in self.__images:
      images_info.append({"id":image.id, "url":image.url})
    
    return images_info

class ImageGallery(QtDeclarative.QDeclarativeView):
  
  onDownloadImage = QtCore.pyqtSignal(QtCore.QObject)
  
  def __init__(self, qml, no_images_message, parent=None):
    QtDeclarative.QDeclarativeView.__init__(self, parent)
    self.setSource(qml)
    self.no_images_message = no_images_message;
  
  def setDataProvider(self, data_provider):
    self.data_model = IamgeGalleryModel(data_provider)
    ctxt = self.rootContext();
    ctxt.setContextProperty('photoGalleryModel', self.data_model)
    ctxt.setContextProperty('controller', self)
    ctxt.setContextProperty('no_images_message', self.no_images_message)
    
    root = self.rootObject()
    self.data_model.updateGallery.connect(root.updateGallery)
    
  def loadImages(self, **args):
    self.data_model.loadImages(**args)
  
  def addImage(self, **args):
    self.data_model.addImage(**args)
  
  @QtCore.pyqtSlot(QtCore.QObject)
  def deleteImage(self, image):
    self.data_model.deleteImage(image)
  
  def getAllImagesInfo(self):
    return self.data_model.getAllImagesInfo()
    
  @QtCore.pyqtSlot(QtCore.QObject)
  def downloadImage(self, image):
    self.onDownloadImage.emit(image)
  
  
    
def main():
  pass

if __name__=="__main__":
  main()