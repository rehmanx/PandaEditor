import panda3d.core as p3dCore
from editor.core.pModBase import PModBase
from editor.utils import EdProperty


class Basics(PModBase):
    def __init__(self, *args, **kwargs):
        """__init__ should not be used for anything but variable declaration"""

        PModBase.__init__(self, *args, **kwargs)

        # --------------------------------------------------------------------
        # create some properties that will be displayed in inspector
        # properties of these types are laid out automatically by the editor
        self.int_property = 5
        self.float_property = 7.5
        self.str_property = "Panda3d"
        self.bool_property = False
        self.vector3 = p3dCore.Vec3(10, 17, 28)
        self.vector2 = p3dCore.Vec3(25, 46)
        # --------------------------------------------------------------------

        # --------------------------------------------------------------------
        # Custom properties, have to be created manually
        self.add_property(EdProperty.EmptySpace(0, 10))  # add some empty space
        self.add_property(EdProperty.Label(name="Custom Properties", is_bold=True))  # label property
        self.add_property(EdProperty.ButtonProperty("Button", self.on_button))  # button property

        # a slider property
        self.__temperature = 5  # private to hide in inspector
        self.add_property(EdProperty.Slider("Temperature",
                                            value=self.__temperature,  # initial value
                                            min_value=0,
                                            max_value=10,
                                            setter=self.set_temperature,
                                            getter=self.get_temperature
                                            ))

        # a choice property
        self.curr_choice = 0
        self.add_property(EdProperty.ChoiceProperty("Apple",
                                                    choices=["Apple", "PineApple", "BigApple", "Blueberry"],
                                                    value=self.curr_choice,  # initial value
                                                    setter=self.set_choice,
                                                    getter=self.get_choice))
        # --------------------------------------------------------------------

        win = self._win  # the window we are rendering into currently
        mouse_watcher_node = self._mouse_watcher_node  # mouse watcher node
        render = self._render  # this is the current scene parent Nodepath
        player_cam = self._game_cam  # this is camera rendering the game view
        le = self._le  # instance of LevelEditor

    def on_start(self):
        """on_start method is called only once"""

        test_module = self._le.get_module("TestModule")  # get a reference to other modules or editor plugins
        if test_module is not None:
            test_module.foo()

        self.accept("a", self.bar, [])  # event handling

        smiley = self._render.find("**/smiley")  # searching the scene graph, you should have a smiley in the scene
                                                 # beforehand.

    def foo(self):
        return self.bar

    def on_update(self):
        """update method is called every frame"""
        pass

    def on_late_update(self):
        """on late update is called after update"""
        pass

    def bar(self, *args):
        print("event a")

    def on_button(self):
        print("button pressed")

    def set_temperature(self, val):
        self.__temperature = val

    def get_temperature(self):
        return self.__temperature

    def set_choice(self, val):
        self.curr_choice = val

    def get_choice(self):
        return self.curr_choice
