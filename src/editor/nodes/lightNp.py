from editor.nodes.baseNp import BaseNp
from panda3d.core import Vec2, LColor, PerspectiveLens
from editor.utils import EdProperty
from editor.utils import Math


class LightNp(BaseNp):
    def __init__(self, np, level_editor=None, uid=None):
        self.intensity = 1.0

        # this attribute is the actual pure color(Hue), as seen, unscaled by intensity
        self.ed_light_colour = LColor(255, 255, 255, 255)

        BaseNp.__init__(self, np, level_editor, uid)

        self.set_color(self.ed_light_colour)
        self.setScale(4)

    def create_properties(self):
        super().create_properties()

        colour = EdProperty.FuncProperty(name="Light Color", value=self.get_color(),
                                         setter=self.set_color, getter=self.get_color)

        intensity = EdProperty.FuncProperty(name="Color intensity", value=self.intensity,
                                            setter=self.set_intensity, getter=self.get_intensity)

        self.properties.append(colour)
        self.properties.append(intensity)

    def create_save_data(self):
        super(LightNp, self).create_save_data()
        self._save_data_infos["EdLightColour"] = [LColor, self.get_color, self.set_color]
        self._save_data_infos["EdLightIntensity"] = [float, self.get_intensity, self.set_intensity]

    def set_intensity(self, val):
        self.intensity = val

        # update light color according to intensity
        r = Math.convert_to_range(0, 255, 0, 1, self.ed_light_colour.x)
        g = Math.convert_to_range(0, 255, 0, 1, self.ed_light_colour.y)
        b = Math.convert_to_range(0, 255, 0, 1, self.ed_light_colour.z)
        color = LColor(r, g, b, 1)
        self.node().setColor(color)

        r = self.node().getColor().x * self.intensity
        g = self.node().getColor().y * self.intensity
        b = self.node().getColor().z * self.intensity
        color = LColor(r, g, b, 1)
        self.node().setColor(color)

    def set_color(self, val):
        self.ed_light_colour = val

        # convert to panda3d colour range
        r = Math.convert_to_range(0, 255, 0, 1, self.ed_light_colour.x)
        g = Math.convert_to_range(0, 255, 0, 1, self.ed_light_colour.y)
        b = Math.convert_to_range(0, 255, 0, 1, self.ed_light_colour.z)

        color = LColor(r, g, b, 1)
        self.setColor(color)

        r = r * self.intensity
        g = g * self.intensity
        b = b * self.intensity

        color = LColor(r, g, b, 1)
        self.node().setColor(color)

    def get_light(self):
        return self.node()

    def get_intensity(self):
        return self.intensity

    def get_color(self):
        return self.ed_light_colour

    def clear_geometry(self):
        pass

    def on_remove(self):
        self.le.get_scene_lights().remove(self)
        self.le.panda_app.showbase.render.clearLight(self)
        super().on_remove()


class EdDirectionalLight(LightNp):
    def __init__(self, *args, **kwargs):
        LightNp.__init__(self, *args, **kwargs)

    def create_properties(self):
        super(EdDirectionalLight, self).create_properties()


class EdPointLight(LightNp):
    def __init__(self, *args, **kwargs):
        LightNp.__init__(self, *args, **kwargs)

        self.attenuation = 0
        self.node().attenuation = (1, 0, 0)
        self.attenuation_map = {
            0: (1, 0, 0),
            1: (0, 1, 0),
            2: (0, 0, 1),
            3: (0, 1, 1)
        }

    def create_properties(self):
        super(EdPointLight, self).create_properties()

        attenuations = ['constant', 'linear', 'quadratic', 'linear-quadratic']
        attenuation = EdProperty.ChoiceProperty(name="attenuation",
                                                setter=self.set_attenuation,
                                                getter=self.get_attenuation,
                                                choices=attenuations)
        self.properties.append(attenuation)

    def get_attenuation(self):
        return self.attenuation

    def set_attenuation(self, val):
        self.node().attenuation = self.attenuation_map[val]
        self.attenuation = val


class EdSpotLight(LightNp):
    def __init__(self, *args, **kwargs):
        # create a lens
        self.lens = PerspectiveLens()
        self.lens.setFov(2)
        self.lens.setNear(0.1)
        self.lens.setFar(2)

        LightNp.__init__(self, *args, **kwargs)

        self.node().setLens(self.lens)
        self.node().setExponent(4)

        self.attenuation = 0
        self.node().attenuation = (1, 0, 0)
        self.attenuation_map = {
            0: (1, 0, 0),
            1: (0, 1, 0),
            2: (0, 0, 1),
            3: (0, 1, 1)
        }

    def create_properties(self):
        super(EdSpotLight, self).create_properties()

        attenuation_types = ['constant', 'linear', 'quadratic', 'linear-quadratic']
        attenuation_prop = EdProperty.ChoiceProperty(name="attenuation",
                                                     setter=self.set_attenuation,
                                                     getter=self.get_attenuation,
                                                     choices=attenuation_types)

        fov = EdProperty.FuncProperty(name="FOV(SpotAngel)",
                                      value=self.lens.getFov(),
                                      setter=self.lens.setFov,
                                      getter=self.lens.getFov)

        self.properties.append(attenuation_prop)
        self.properties.append(fov)

    def get_attenuation(self):
        return self.attenuation

    def set_attenuation(self, val):
        self.node().attenuation = self.attenuation_map[val]
        self.attenuation = val
