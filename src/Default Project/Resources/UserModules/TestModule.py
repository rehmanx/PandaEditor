import math
import panda3d.core as p3dCore
from editor.p3d.pModBase import PModBase


class TestModule(PModBase):
    def __init__(self, *args, **kwargs):
        PModBase.__init__(self, *args, **kwargs)

        self.msg = "This is test module...!"

    # on_start method is called once
    def on_start(self):
        pass

    # update method is called every frame
    def on_update(self):
        pass

    def foo(self):
        print(self.msg)
