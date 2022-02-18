from editor.nodes.baseNp import BaseNp


class EdCameraNp(BaseNp):
    def __init__(self, np, le=None, uid=None):
        BaseNp.__init__(self, np, le, uid)

    def update(self, task):
        model = self.getChild(0)
        scale = (model.getPos() - self.le.panda_app.showbase.ed_camera.getPos()).length() / 80
        model.setScale(scale)
        return task.cont
