import math
import panda3d.core as p3dCore
from editor.p3d.pModBase import PModBase
from editor.utils import EdProperty


class Tutorial(PModBase):
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
        self.__temperature = 5  # private to hide in inspector
        self.add_property(EdProperty.Slider("Temperature",
                                            value=self.__temperature,  # initial value
                                            min_value=0,
                                            max_value=10,
                                            setter=self.set_temperature,
                                            getter=self.get_temperature
                                            ))

        # choice property
        self.choices = ["Apple", "PineApple", "BigApple"]
        self.__curr_choice = 0
        self.add_property(EdProperty.ChoiceProperty("Apple",
                                                    choices=self.choices,
                                                    value=self.__curr_choice,  # initial value
                                                    setter=self.set_choice,
                                                    getter=self.get_choice))

        self.add_property(EdProperty.EmptySpace(0, 5))  # add some empty space

    # on_start method is called once
    def on_start(self):
        # --------------------------------- #
        # Tutorial - uncomment lines with * #
        # --------------------------------- #

        # get access to other user modules or editor plugins
        # *test_module = self.le.get_mod_instance("TestModule")
        # *test_module.foo()

        # get the player cam
        self.player_cam = self.le.get_player_camera()

        # load a 3d model
        smiley = self.load_model("Resources/Models/smiley.egg")
        smiley.setScale(10)

        # find a 3d model
        np = self.rootNp.find("**/GameRender/smiley*")
        np.setScale(20)

        # basic event handling
        # *self.accept("a", self.bar, ["messenger event"])

        # win = self.win  # the window we are rendering into currently
        # mouse_watcher_node = self.mouse_watcher_node

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
        self.__temperature = val

    def get_temperature(self):
        return self.__temperature

    def set_choice(self, val):
        self.__curr_choice = val
        print(self.__curr_choice)

    def get_choice(self):
        return self.__curr_choice
