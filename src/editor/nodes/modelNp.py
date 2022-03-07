import editor.utils as EdUtils
from editor.nodes.baseNp import BaseNp
from panda3d.core import LColor


class ModelNp(BaseNp):
    def __init__(self, np, le=None, uid=None):
        BaseNp.__init__(self, np, le, uid)

    def create_properties(self):
        super().create_properties()

        color = EdUtils.EdProperty.FuncProperty(name="Colour", value=self.get_ed_colour(), setter=self.set_ed_colour,
                                                getter=self.get_ed_colour)
        self.properties.append(color)

    def create_save_data(self):
        super(ModelNp, self).create_save_data()
        self._save_data_infos["Colour"] = [LColor, self.get_ed_colour, self.set_ed_colour]

    def set_ed_colour(self, val):
        r = EdUtils.Utils.convert_to_range(0, 255, 0, 1, val.x)
        g = EdUtils.Utils.convert_to_range(0, 255, 0, 1, val.y)
        b = EdUtils.Utils.convert_to_range(0, 255, 0, 1, val.z)
        a = EdUtils.Utils.convert_to_range(0, 255, 0, 1, val.w)

        color = LColor(r, g, b, a)
        self.setColor(color)

    def get_ed_colour(self):
        val = self.getColor()

        r = EdUtils.Utils.convert_to_range(0, 1, 0, 255, val.x)
        g = EdUtils.Utils.convert_to_range(0, 1, 0, 255, val.y)
        b = EdUtils.Utils.convert_to_range(0, 1, 0, 255, val.z)
        a = EdUtils.Utils.convert_to_range(0, 1, 0, 255, val.w)

        color = LColor(r, g, b, a)
        return color
