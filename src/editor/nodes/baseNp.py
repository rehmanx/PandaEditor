from panda3d.core import NodePath
from panda3d.core import Vec3
from editor.utils import Math
from editor.utils import EdProperty


class BaseNp(NodePath):
    def __init__(self, np, level_editor=None, uid=None):
        NodePath.__init__(self, np)

        self.uid = uid
        self.le = level_editor

        self._task = None

        self.properties = []
        self._save_data_infos = {}
        self._save_data = []

        self.create_properties()
        self.create_save_data()

    def start_update(self):
        self._task = taskMgr.add(self.update, '%sUpdate' % self.getName())

    def update(self, task):
        scale = (self.getPos() - self.le.panda_app.showbase.ed_camera.getPos()).length() / 80
        self.setScale(scale)
        return task.cont

    def create_properties(self):
        pos = EdProperty.FuncProperty(name="Position", value=self.getPos(),
                                      setter=self.setPos, getter=self.getPos)

        rot = EdProperty.FuncProperty(name="Rotation", value=self.get_ed_rotation(),
                                      setter=self.set_ed_rotation, getter=self.get_ed_rotation)

        scale = EdProperty.FuncProperty(name="Scale    ", value=self.getScale(),
                                        setter=self.setScale, getter=self.getScale)

        self.properties.append(pos)
        self.properties.append(rot)
        self.properties.append(scale)

    def create_save_data(self):
        self._save_data_infos["Pos"] = [Vec3, self.getPos, self.setPos]
        self._save_data_infos["Rot"] = [Vec3, self.getHpr, self.setHpr]
        self._save_data_infos["Scale"] = [Vec3, self.getScale, self.setScale]

    def save_data(self):
        self._save_data.clear()
        for key in self._save_data_infos.keys():
            prop = EdProperty.FuncProperty(name=key,
                                           value=self._save_data_infos[key][1](),
                                           setter=self._save_data_infos[key][2])
            self._save_data.append(prop)

    def restore_data(self):
        for prop in self._save_data:
            setter = prop.get_setter()
            setter(prop.get_value())

        self.update_properties()

    def get_ed_data(self):
        pass

    def get_uid(self):
        return self.uid

    def get_properties(self):
        return self.properties

    def get_ed_rotation(self):
        return self.getHpr()

    def set_ed_rotation(self, val):
        self.setHpr(val)

    def set_ed_data(self, data):
        pass

    def update_properties(self):
        for prop in self.properties:
            x = prop.get_getter()
            if x:
                prop.set_value(x())
            else:
                prop.set_value(getattr(self, prop.get_name()))

    def on_property_modified(self, prop, value):
        x = prop.get_setter()
        x(self, value)

    def on_remove(self):
        if self._task in taskMgr.getAllTasks():
            taskMgr.remove(self._task)
        # self.clearPythonTag(TAG_PICKABLE)
