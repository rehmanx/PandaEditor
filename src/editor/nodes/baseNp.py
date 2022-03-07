import editor.utils as EdUtils
from panda3d.core import NodePath
from panda3d.core import Vec3


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

        self.setPythonTag("PICKABLE", self)

    def start_update(self):
        self._task = taskMgr.add(self.update, '%sUpdate' % self.getName(), sort=1)

    def update(self, task):
        return task.cont

    def create_properties(self):
        name = EdUtils.EdProperty.FuncProperty(name="Name      ",
                                               value=self.get_name(),
                                               setter=self.set_name,
                                               getter=self.get_name)

        pos = EdUtils.EdProperty.FuncProperty(name="Position",
                                              value=self.getPos(),
                                              setter=self.setPos,
                                              getter=self.getPos)

        rot = EdUtils.EdProperty.FuncProperty(name="Rotation",
                                              value=self.getHpr(),
                                              setter=self.setHpr,
                                              getter=self.getHpr)

        scale = EdUtils.EdProperty.FuncProperty(name="Scale    ",
                                                value=self.getScale(),
                                                value_limit=Vec3(0.01, 0.01, 0.01),
                                                setter=self.set_scale,
                                                getter=self.getScale)

        self.properties.append(name)
        self.properties.append(pos)
        self.properties.append(rot)
        self.properties.append(scale)

    def create_save_data(self):
        # format = save_data["variable"] = [value, getter, setter]
        self._save_data_infos["Pos"] = [Vec3, self.getPos, self.setPos]
        self._save_data_infos["Rot"] = [Vec3, self.getHpr, self.setHpr]
        self._save_data_infos["Scale"] = [Vec3, self.getScale, self.setScale]

    def save_data(self):
        self._save_data.clear()
        for key in self._save_data_infos.keys():
            prop = EdUtils.EdProperty.FuncProperty(name=key,
                                                   value=self._save_data_infos[key][1](),
                                                   setter=self._save_data_infos[key][2])
            self._save_data.append(prop)

    def restore_data(self):
        for prop in self._save_data:
            setter = prop.setter
            setter(prop.val)

        self.update_properties()

    def get_uid(self):
        return self.uid

    def get_properties(self):
        return self.properties

    def update_properties(self):
        for prop in self.properties:
            x = prop.getter
            if x:
                prop.set_value(x())
            else:
                prop.set_value(getattr(self, prop.get_name()))

    def on_property_modified(self, prop, value):
        x = prop.setter
        x(self, value)

    def on_remove(self):
        if self._task in taskMgr.getAllTasks():
            taskMgr.remove(self._task)
        # self.clearPythonTag(TAG_PICKABLE)
