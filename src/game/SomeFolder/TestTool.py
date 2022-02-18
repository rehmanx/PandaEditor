from editor.p3d.pToolBase import PToolBase


class TestTool(PToolBase):
    def __init__(self, *args, **kwargs):
        PToolBase.__init__(self, *args, **kwargs)

        self.chest = "chests"
        self.breasts = "breasts"
        self.nipples = "nipples"

    # on_enable method is called once
    def on_enable(self):
        # self.request_unique_tab(menu="fUCK/breasts/Tits")

        self.accept("a", self.foo)
        self.accept("b", self.bar)

    # update method is called every frame
    def on_update(self):
        pass

    def foo(self):
        print("foo called")

    def bar(self):
        print("bar called")
