import panda3d.core as p3dCore
from editor.core.pModBase import PModBase
from editor.utils import EdProperty


class Basics(PModBase):
    def __init__(self, *args, **kwargs):
        """__init__ should not be used for anything but variable declaration"""

        PModBase.__init__(self, *args, **kwargs)

        self.player_cam = None

        # create some properties that will be displayed in inspector
        self.int_property = 5
        self.float_property = 7.5
        self.str_property = "Panda3d"
        self.bool_property = False
        self.vector_3 = p3dCore.Vec3(10, 17, 28)
        self.vector_2 = p3dCore.Vec3(25, 46)

        # Custom properties
        self.add_property(EdProperty.EmptySpace(0, 10))  # add some empty space

        self.add_property(EdProperty.Label(name="Custom Properties", is_bold=True))  # label

        self.add_property(EdProperty.ButtonProperty("Button", self.on_button))  # button

        # slider
        self.temperature = 5  # private to hide in inspector
        self.add_hidden_variable("temperature")
        self.add_property(EdProperty.Slider("Temperature",
                                            value=self.temperature,  # initial value
                                            min_value=0,
                                            max_value=10,
                                            setter=self.set_temperature,
                                            getter=self.get_temperature
                                            ))

        # choice property
        self.choices = ["Apple", "PineApple", "BigApple"]
        self.curr_choice = 0
        self.add_hidden_variable("curr_choice")
        self.add_property(EdProperty.ChoiceProperty("Apple",
                                                    choices=self.choices,
                                                    value=self.curr_choice,  # initial value
                                                    setter=self.set_choice,
                                                    getter=self.get_choice))

        self.add_property(EdProperty.EmptySpace(0, 5))  # add some empty space

    def on_start(self):
        """on_start method is called only once"""

        # get access to other user modules or editor plugins
        test_module = self._le.get_mod_instance("TestModule")
        if test_module is not None:
            test_module.foo()

        self.player_cam = self._le.player_camera  # get the player cam

        np = self._render.find("**/smiley.egg")  # scene graph search

        self.accept("a", self.bar, [])  # event handling

        win = self._win  # the window we are rendering into currently

        mouse_watcher_node = self._mouse_watcher_node  # mouse watcher node

    def on_update(self):
        """update method is called every frame"""
        pass

    def on_late_update(self):
        """on late update is called after update"""
        pass

    def bar(self, *args):
        print(args[0])

    def on_button(self):
        print("button pressed")

    def set_temperature(self, val):
        self.temperature = val

    def get_temperature(self):
        return self.temperature

    def set_choice(self, val):
        self.curr_choice = val

    def get_choice(self):
        return self.curr_choice
