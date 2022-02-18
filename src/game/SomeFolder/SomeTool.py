import math
import panda3d.core as pm
from editor.p3d.pToolBase import PToolBase


class SomeTool( PToolBase ):
    def __init__(self, *args, **kwargs):
        PToolBase.__init__(self, *args, **kwargs)

    # on_enable method is called once
    def on_enable(self):
        pass

    # update method is called every frame
    def on_update(self):
        pass
