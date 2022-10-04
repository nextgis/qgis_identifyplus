from .identifytool_qgis import QGISTool
from .identifytool_sqlite import SQLiteTool
from .identifytool_ngw import NGWTool


def allTools():
	return [
		QGISTool,
		SQLiteTool,
		NGWTool
	]