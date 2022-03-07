"""
import editor.constants as constant
from editor.p3d import pModBase
from editor.utils.exceptionHandler import try_execute
from direct.showbase.ShowBase import taskMgr


class PToolBase(pModBase.PModBase):
    def __init__(self, *args, **kwargs):
        """