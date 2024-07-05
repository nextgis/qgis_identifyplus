from typing import List

from .identifytool import IdentifyTool
from .identifytool_qgis import QGISTool
from .identifytool_sqlite import SQLiteTool
from .identifytool_ngw import NGWTool


def allTools() -> List[IdentifyTool]:
    return [QGISTool, SQLiteTool, NGWTool]
