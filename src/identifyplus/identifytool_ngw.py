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

import os
import re
from urllib.parse import parse_qs, unquote, urlparse

from qgis.core import (
    QgsApplication,
    QgsAuthMethodConfig,
    QgsDataSourceUri,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsMapLayer,
)
from qgis.PyQt.QtCore import (
    QAbstractListModel,
    QFileInfo,
    QModelIndex,
    QObject,
    QSettings,
    Qt,
    QThread,
    pyqtSignal,
)
from qgis.PyQt.QtGui import QIcon, QImage, QPixmap
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from .identifytool import IdentifyTool
from .ngw_external_api_python.core.ngw_attachment import NGWAttachment
from .ngw_external_api_python.core.ngw_connection import NGWConnection
from .ngw_external_api_python.core.ngw_connection_settings import (
    NGWConnectionSettings,
)
from .ngw_external_api_python.core.ngw_error import NGWError
from .ngw_external_api_python.core.ngw_feature import NGWFeature
from .ngw_external_api_python.core.ngw_resource_factory import (
    NGWResourceFactory,
)
from .qgis_plugin_base import Plugin

HAS_CONNECT_2 = True
try:
    from nextgis_connect.ngw_connection import NgwConnectionsManager

except ImportError:
    HAS_CONNECT_2 = False


class NGWTool(IdentifyTool, QObject):
    def __init__(self):
        super().__init__("ngw", "ngw identification")
        QObject.__init__(self)

    def identify(self, qgisIdentResultVector, resultsContainer):
        ngw_resource = self.ngw_resource_from_qgs_map_layer(
            qgisIdentResultVector._qgsMapLayer
        )

        if ngw_resource is not None:
            Plugin().plPrint(f">>> ngw_resource: {ngw_resource}")
            view = NGWImagesView()
            model = NGWImagesModel(qgisIdentResultVector, ngw_resource)
            view.setModel(model)

            resultsContainer.addResult(view, self.tr("Photos (ngw)"))
        else:
            Plugin().plPrint(">>> No ngw_resource!")

    @staticmethod
    def isAvailable(qgsMapLayer):
        if not isinstance(qgsMapLayer, QgsMapLayer):
            return False

        if qgsMapLayer.type() != QgsMapLayer.VectorLayer:
            return False

        try:
            ngw_resource = NGWTool.ngw_resource_from_qgs_map_layer(qgsMapLayer)
            if ngw_resource is not None:
                return True
        except NGWError as err:
            Plugin().plPrint("NGWError: " + str(err))

        return False

    @staticmethod
    def ngw_resource_from_qgs_map_layer(qgs_map_layer):
        layer_source = qgs_map_layer.source()
        layer_name = None

        connection_id = qgs_map_layer.customProperty("ngw_connection_id")
        resource_id = qgs_map_layer.customProperty("ngw_resource_id")
        auth_config_id = None
        username = None
        password = None

        if (
            HAS_CONNECT_2
            and connection_id is not None
            and resource_id is not None
        ):
            connections_manager = NgwConnectionsManager()  # type: ignore
            connection = connections_manager.connection(connection_id)
            if connection is None:
                return None

            instance_url = connection.url

            if qgs_map_layer.providerType() == "WFS":
                datasource_uri = QgsDataSourceUri(layer_source)
                layer_name = datasource_uri.param("typename")

        else:
            if qgs_map_layer.providerType().lower() not in ("wfs", "ogr"):
                return None

            if qgs_map_layer.providerType() == "WFS":
                if "url=" in layer_source:
                    datasource_uri = QgsDataSourceUri(layer_source)
                    url = datasource_uri.param("url")
                    auth_config_id = datasource_uri.authConfigId()
                    if auth_config_id == "":
                        auth_config_id = None
                    layer_name = datasource_uri.param("typename")
                else:
                    url = layer_source

                url_components = urlparse(url)

                request_attributes = parse_qs(url_components.query)

                if auth_config_id is None:
                    username = request_attributes.get("username", [None])[0]
                    password = request_attributes.get("password", [None])[0]
                if layer_name is None:
                    layer_name = request_attributes.get(
                        "TYPENAME", request_attributes.get("typename", [None])
                    )[0]

            else:
                url = layer_source.lstrip("/vsicurl/")  # noqa: B005
                url_components = urlparse(url)

                if url_components.username and url_components.password:
                    username = unquote(url_components.username)
                    password = unquote(url_components.password)

            match = re.search(r"^.*/api/resource/(\d+)", url_components.path)
            if match is None:
                return None

            instance_url = "{scheme}://{domain}/".format(
                scheme=url_components.scheme,
                domain=url_components.netloc.split("@")[-1],
            )
            resource_id = int(match.group(1))

        if auth_config_id is not None:
            method = QgsApplication.authManager().configAuthMethodKey(
                auth_config_id
            )
            if method != "Basic":
                return None

            config = QgsAuthMethodConfig()

            is_loaded = QgsApplication.authManager().loadAuthenticationConfig(
                auth_config_id, config, full=True
            )[0]
            if not is_loaded:
                return None

            username = config.config("username")
            password = config.config("password")

        connection_settings = NGWConnectionSettings(
            "ngw", instance_url, username, password
        )
        ngwConnection = NGWConnection(connection_settings)

        resource_factory = NGWResourceFactory(ngwConnection)
        try:
            ngw_resource = resource_factory.get_resource(resource_id)
            if ngw_resource is None:
                return None

            if ngw_resource.type_id == "wfsserver_service":
                if layer_name is None:
                    return None

                layers = ngw_resource.get_layers()
                for layer in layers:
                    if layer["keyname"] == layer_name:
                        resource_id = layer["resource_id"]
                        break
                return resource_factory.get_resource(resource_id)

            return ngw_resource

        except NGWError:
            return None


class NGWImagesModel(QAbstractListModel):
    initEnded = pyqtSignal()

    def __init__(self, obj, ngw_resource, parent=None):
        super().__init__(parent)

        self.__obj = obj
        self.__ngw_resource = ngw_resource
        self.__images = []

        self.__thread = QThread(self)
        self.moveToThread(self.__thread)
        self.__thread.started.connect(self.initModel)
        self.initEnded.connect(self.__thread.quit)
        self.__thread.start()

    def initModel(self):
        Plugin().plPrint(">>> initModel")
        fid = self.__obj.getFeature().id()
        Plugin().plPrint(f">>> --- fid: {fid}")

        dataProvider = self.__obj._qgsMapLayer.dataProvider()
        if dataProvider.name() == "WFS":
            if hasattr(dataProvider, "idFromFid") and callable(
                dataProvider.idFromFid
            ):
                fid = dataProvider.idFromFid(fid)
                if type(fid) != "long":
                    fid = int(fid)

        elif (
            self.__obj._qgsMapLayer.storageType() == "GPKG"
            and "ngw_connection_id"
            in self.__obj._qgsMapLayer.customPropertyKeys()
        ):
            context = QgsExpressionContext()
            context.appendScopes(
                QgsExpressionContextUtils.globalProjectLayerScopes(
                    self.__obj._qgsMapLayer
                )
            )
            context.setFeature(self.__obj.getFeature())

            expression = QgsExpression("ngw_feature_id()")
            fid = expression.evaluate(context)

        self.__ngw_feature = NGWFeature({"id": fid}, self.__ngw_resource)
        self.__images_urls = []

        attachments = self.__ngw_feature.get_attachments()
        for attachment in attachments:
            if attachment["is_image"] is True:
                self.insertRow(
                    NGWAttachment(attachment["id"], self.__ngw_feature)
                )

        self.initEnded.emit()

    def rowCount(self, parent=QModelIndex()):  # noqa: B008
        return len(self.__images)

    def removeRows(self, row, count, parent=QModelIndex()):  # noqa: B008
        self.beginRemoveRows(parent, row, row + count)

        for _ in range(count):
            # self.__ngw_feature.unlink_attachment( self.__images_urls[row][1] )
            # self.__images_urls.remove(self.__images_urls[row])
            self.__images[row].unlink()
            self.__images.remove(self.__images[row])

        self.endRemoveRows()
        return True

    def addImage(self, image_filename):
        uploadDialog = ImageUploadDialog()
        uploaded_file_info = self.__ngw_feature.ngw_vector_layer._res_factory.connection.upload_file(
            image_filename, uploadDialog.uploadNext
        )
        id = self.__ngw_feature.link_attachment(uploaded_file_info)
        self.insertRow(NGWAttachment(id, self.__ngw_feature))

    def insertRow(self, ngw_attachment):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.__images.append(ngw_attachment)
        self.endInsertRows()

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DecorationRole:
            return None

        elif index.isValid() and role == Qt.DisplayRole:
            return self.__images[index.row()]

        elif index.isValid() and role == (Qt.UserRole + 1):
            return self.__images[index.row()]

        else:
            return None


class ImageLoader(QObject):
    finished = pyqtSignal(QImage)

    def __init__(self, ngw_attachment, parent=None):
        QObject.__init__(self, parent)
        self.__ngw_attachment = ngw_attachment

    def loadImage(self):
        img = QImage()
        img_info = self.__ngw_attachment.get_image()
        img.loadFromData(img_info[2])
        self.finished.emit(img)


class ImageLabel(QLabel):
    imageLoaded = pyqtSignal()

    def __init__(self, ngw_attachment, parent=None):
        QLabel.__init__(self, parent)
        self.pm = None
        self.setText(self.tr("Loading..."))
        self.__worker = ImageLoader(ngw_attachment)
        self.__thread = QThread(self.__worker)
        self.__worker.moveToThread(self.__thread)
        self.__thread.started.connect(self.__worker.loadImage)
        self.__worker.finished.connect(self.__thread.quit)
        self.__worker.finished.connect(self.load)
        self.__thread.start()

    def load(self, img):
        self.pm = QPixmap()
        self.pm.convertFromImage(img)
        self.clear()

        self._k = 1
        self.setScaledContents(True)
        sp = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sp.setHeightForWidth(True)
        self.setSizePolicy(sp)
        self.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.setMinimumSize(50, 50)

        self._k = 1.0 * self.pm.height() / self.pm.width()

        self.setPixmap(self.pm)

        self.imageLoaded.emit()

    def heightForWidth(self, width: int) -> int:
        if width < self.pm.size().width():
            return int(width * self._k)
        else:
            return self.pm.size().height()


class Image(QWidget):
    deleteImage = pyqtSignal(QWidget)
    downloadImage = pyqtSignal(QWidget)

    def __init__(self, ngw_attachment, parent=None):
        QWidget.__init__(self, parent)

        self.__vbl_layout = QVBoxLayout(self)
        self.__vbl_layout.setAlignment(Qt.AlignHCenter)
        self.__vbl_layout.setContentsMargins(5, 5, 5, 5)
        self.__vbl_layout.setSpacing(0)

        self.__image_container = ImageLabel(ngw_attachment, self)
        self.__image_container.imageLoaded.connect(self.imageLoadedHandle)
        self.__vbl_layout.addWidget(self.__image_container)

        self.__w_buttons_widget = QWidget()
        self.__hbl_buttons_layout = QHBoxLayout(self.__w_buttons_widget)
        self.__hbl_buttons_layout.setAlignment(Qt.AlignRight)
        self.__hbl_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.__hbl_buttons_layout.setSpacing(1)
        self.__vbl_layout.addWidget(self.__w_buttons_widget)

        self.__pb_download_image = QPushButton()
        self.__pb_download_image.setIcon(
            QIcon(":/plugins/identifyplus/icons/downloadImageBtn.png")
        )
        self.__pb_download_image.setToolTip(self.tr("Download photo"))
        self.__pb_download_image.setStatusTip(self.tr("Download photo"))
        # self.__pb_download_image.setVisible(False)
        self.__pb_download_image.hide()

        self.__pb_download_image.clicked.connect(self.emitDownloadImage)
        self.__hbl_buttons_layout.addWidget(self.__pb_download_image)

        self.__pb_delete_image = QPushButton()
        self.__pb_delete_image.setIcon(
            QIcon(":/plugins/identifyplus/icons/deleteImageBtn.png")
        )
        self.__pb_delete_image.setToolTip(self.tr("Delete photo"))
        self.__pb_delete_image.setStatusTip(self.tr("Delete photo"))
        # self.__pb_delete_image.setVisible(False)
        self.__pb_delete_image.hide()

        self.__pb_delete_image.clicked.connect(self.emitDeleteImage)
        self.__hbl_buttons_layout.addWidget(self.__pb_delete_image)

    def imageLoadedHandle(self):
        # self.__pb_download_image.setVisible(True)
        # self.__pb_delete_image.setVisible(True)
        self.__pb_download_image.show()
        self.__pb_delete_image.show()

    def emitDownloadImage(self):
        self.downloadImage.emit(self)

    def emitDeleteImage(self):
        self.deleteImage.emit(self)


class NGWImagesView(QWidget):
    images_load_finish = pyqtSignal()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.__model = None
        self.__images = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        s = QScrollArea()
        s.setWidgetResizable(True)
        # s.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sb = s.verticalScrollBar()
        stylesheet = """
            QScrollBar:vertical {
                  border: 2px solid transparent;
                  background: transparent;
                  width: 8px;
                  margin: 0px 0 0px 0;
              }
              QScrollBar::handle:vertical {
                  background: transparent;
                  border: 2px solid #2AACAC;
                  border-radius: 1px;
                  min-height: 20px;
              }

              QScrollBar::add-line:vertical {
                  height: 0px;
              }

              QScrollBar::sub-line:vertical {
                  height: 0px;
              }


              QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                  border: 0px solid grey;
                  width: 0px;
                  height: 0px;
                  background: white;
              }


              QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                  background: none;
              }

            """
        sb.setStyleSheet(stylesheet)

        s.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(s)

        self.__w_buttons_widget = QWidget()
        self.__hbl_buttons_layout = QHBoxLayout(self.__w_buttons_widget)
        self.__hbl_buttons_layout.setAlignment(Qt.AlignLeft)
        self.__hbl_buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.__hbl_buttons_layout.setSpacing(1)
        layout.addWidget(self.__w_buttons_widget)

        self.__pb_download_images = QPushButton()
        self.__pb_download_images.setIcon(
            QIcon(":/plugins/identifyplus/icons/downloadImageBtn.png")
        )
        self.__pb_download_images.setToolTip(self.tr("Download photos"))
        self.__pb_download_images.setStatusTip(self.tr("Download photos"))
        self.__pb_download_images.setEnabled(False)
        self.__pb_download_images.clicked.connect(self.downloadImages)
        self.__hbl_buttons_layout.addWidget(self.__pb_download_images)

        self.__pb_add_image = QPushButton()
        self.__pb_add_image.setIcon(
            QIcon(":/plugins/identifyplus/icons/addImageBtn.png")
        )
        self.__pb_add_image.setToolTip(self.tr("Add photo(s)"))
        self.__pb_add_image.setStatusTip(self.tr("Add photo(s)"))
        self.__pb_add_image.clicked.connect(self.addImage)
        self.__hbl_buttons_layout.addWidget(self.__pb_add_image)

        self.w = QWidget(self)

        self.vbox = QVBoxLayout(self.w)
        self.vbox.setSpacing(0)
        self.vbox.setContentsMargins(0, 0, 0, 0)

        self.__w_images_container = QWidget(self)
        self.__vbl_images_container = QVBoxLayout(self.__w_images_container)
        self.__vbl_images_container.setSpacing(5)
        self.__vbl_images_container.setContentsMargins(0, 0, 0, 0)

        self.vbox.addWidget(self.__w_images_container)

        self.vbox.addSpacerItem(
            QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )

        s.setWidget(self.w)

        self.__message = QLabel(self.tr("Loading..."))
        self.__message.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.__message.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.__vbl_images_container.addWidget(self.__message)

    def __updateMessage(self):
        if self.__model.rowCount() > 0:
            self.__pb_download_images.setEnabled(True)
            self.__message.clear()
        else:
            self.__pb_download_images.setEnabled(False)
            self.__message.setText(self.tr("No photos"))

    def setModel(self, model):
        self.__model = model
        self.__model.initEnded.connect(self.loadModelData)
        self.__model.rowsRemoved.connect(self.rowsRemovedProcess)
        self.__model.rowsInserted.connect(self.rowsInsertedProcess)

    def loadModelData(self):
        self.__updateMessage()

    def rowsRemovedProcess(self, parent, start, end):
        rem_ids = list(range(start, end))
        rem_ids.reverse()
        for i in rem_ids:
            self.__images[i].hide()
            self.__images[i].close()
            self.__images.remove(self.__images[i])

        self.__updateMessage()

    def rowsInsertedProcess(self, parent, start, end):
        for i in range(start, end + 1):
            index = self.__model.index(i, 0)
            data = self.__model.data(index)

            img = Image(data, self.w)
            img.deleteImage.connect(self.deleteImage)
            img.downloadImage.connect(self.downloadImage)
            self.__images.append(img)
            self.__vbl_images_container.addWidget(img)

        self.__updateMessage()

    def deleteImage(self, image):
        i = self.__images.index(image)
        self.__model.removeRow(i)

    def addImage(self):
        settings = QSettings()
        lastLoadPhotoDir = settings.value(
            "identifyplus/lastLoadPhotoDir", "", type=str
        )

        file_names, _ = QFileDialog.getOpenFileNames(
            self,
            self.tr("Choose photo(s)"),
            lastLoadPhotoDir,
            self.tr("Image Files (*.png *.jpg *.bmp)"),
        )

        for file_name in file_names:
            settings.setValue(
                "identifyplus/lastLoadPhotoDir",
                QFileInfo(file_name).absolutePath(),
            )
            self.__model.addImage(file_name)

    def downloadImage(self, image):
        i = self.__images.index(image)
        index = self.__model.index(i, 0)

        ngw_attachment = self.__model.data(index, Qt.UserRole + 1)

        settings = QSettings()
        lastDir = settings.value("identifyplus/lastSavePhotoDir", "")

        fName, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save photo"), lastDir
        )
        if fName == "":
            return

        file_info = QFileInfo(fName)
        settings.setValue(
            "identifyplus/lastSavePhotoDir", file_info.absolutePath()
        )

        ngw_attachments = [ngw_attachment]
        default_names = [file_info.fileName()]
        downloadDialog = ImageDownloadDialog(
            ngw_attachments, file_info.absolutePath(), default_names
        )
        downloadDialog.exec_()

    def downloadImages(self):
        settings = QSettings()
        lastSavePhotosDir = settings.value(
            "identifyplus/lastSavePhotosDir", "", type=str
        )

        dirPath = QFileDialog.getExistingDirectory(
            self, self.tr("Select directory fo save photos"), lastSavePhotosDir
        )

        if dirPath == "":
            return

        settings.setValue("identifyplus/lastSavePhotoDir", dirPath)

        ngw_attachments = []
        for i in range(self.__model.rowCount()):
            index = self.__model.index(i, 0)
            ngw_attachments.append(self.__model.data(index, Qt.UserRole + 1))

        downloadDialog = ImageDownloadDialog(ngw_attachments, dirPath)
        downloadDialog.exec_()


class ImageUploadDialog(QProgressDialog):
    def __init__(self, parent=None):
        QProgressDialog.__init__(self, parent)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.tr("Upload images process"))
        self.setCancelButton(None)
        self.forceShow()
        self.setValue(0)

    def uploadNext(self, total, readed):
        progress = int((float(readed) / float(total)) * 100)
        self.setValue(progress)


class ImageDownloadDialog(QDialog):
    def __init__(
        self, ngw_attachments, save_dir, default_names=None, parent=None
    ):
        QDialog.__init__(self, parent)
        if default_names is None:
            default_names = []

        self.setWindowTitle(self.tr("Download images process"))
        self.setFixedSize(250, 75)

        layout = QVBoxLayout(self)
        self.pb = QProgressBar(self)
        self.pb.setRange(0, len(ngw_attachments))
        self.pb.setValue(0)
        layout.addWidget(self.pb)

        self.__ngw_attachments = ngw_attachments
        self.__default_names = default_names

        difference_len = len(self.__ngw_attachments) - len(
            self.__default_names
        )
        if difference_len > 0:
            self.__default_names.extend([None] * difference_len)

        self.__save_dir = save_dir
        self.__current_index = 0

        if len(self.__ngw_attachments) > 0:
            self.downloadNext()

    def downloadNext(self):
        self.pb.setValue(self.pb.value() + 1)
        if self.__current_index == len(self.__ngw_attachments):
            self.hide()
            self.close()
            return

        self.worker = ImageDownloader(
            self.__ngw_attachments[self.__current_index],
            self.__save_dir,
            self.__default_names[self.__current_index],
        )

        self.__current_index = self.__current_index + 1

        self.thread = QThread(self)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.saveImage)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.downloadNext)
        self.thread.start()


class ImageDownloader(QObject):
    finished = pyqtSignal()

    def __init__(self, ngw_attachment, save_dir, filename=None, parent=None):
        QObject.__init__(self, parent)
        self.__ngw_attachment = ngw_attachment
        self.__filename = filename
        self.__save_dir = save_dir

        self.__thread = QThread(self)
        self.moveToThread(self.__thread)
        self.__thread.started.connect(self.saveImage)
        self.finished.connect(self.__thread.quit)
        self.__thread.start()

    def saveImage(self):
        img = QImage()
        attachment_info = self.__ngw_attachment.get_image()
        img.loadFromData(attachment_info[2])

        if self.__filename is None:
            img.save(
                os.path.join(
                    self.__save_dir,
                    attachment_info[0] + f".{attachment_info[1]}",
                ),
                attachment_info[1],
            )
        else:
            img.save(
                os.path.join(
                    self.__save_dir,
                    self.__filename + f".{attachment_info[1]}",
                ),
                attachment_info[1],
            )
        self.finished.emit()
