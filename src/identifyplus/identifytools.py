from typing import List

from .identifytool import IdentifyTool
from .identifytool_ngw import NGWTool
from .identifytool_qgis import QGISTool
from .identifytool_sqlite import SQLiteTool


def allTools() -> List[IdentifyTool]:
    return [QGISTool, SQLiteTool, NGWTool]
