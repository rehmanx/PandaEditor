from editor.p3d.pModBase import PModBase
from panda3d.core import Vec2
from editor.utils import Math, EdProperty


def some_func():
    print("button clicked")


class InputManager(PModBase):
    def __init__(self, *args, **kwargs):
        PModBase.__init__(self, *args, **kwargs)
        self._sort = 3
                
        # keyboard events
        self.key_map = {}

        # list of all the keys to bind
        self.keys = ["w", "a", "s", "d", "r", "escape", "mouse1"]
        
        # mouse
        self.__dx = 0
        self.__dy = 0
        self.__lastMousePos = Vec2(0, 0)
        self.mouseInput = Vec2(0, 0)
        self.zoom = 0

        # other
        self.__slider = 5

        # add discarded attr
        # self.add_discarded_attr("mouseInput")
        # self.add_discarded_attr("zoom")

        # add custom properties
        self.add_property(EdProperty.EmptySpace(0, 5))
        self.add_property(EdProperty.ButtonProperty("Button", some_func))
        self.add_property(EdProperty.EmptySpace(0, 5))

        self.add_property(EdProperty.ChoiceProperty("choice", ["triss", "yeneffer"], value=1, obj=self))
        self.add_property(EdProperty.Label(name="Yennefer", is_bold=True))
        self.add_property(EdProperty.Label("Triss", is_bold=False))

        self.add_property(EdProperty.Slider("fuck strength potion",
                                            value=5,
                                            min_value=0,
                                            max_value=10,
                                            setter=self.set_slider_val,
                                            getter=self.get_slider_val
                                            ))
        # self.add_property(EdProperty.StaticBox("FuckStrength oh yeah more..."))

    def get_slider_val(self):
        return self.__slider

    def set_slider_val(self, val):
        self.__slider = val
        print(self.__slider)

    def on_start(self):
        self.key_map.clear()
        
        for key in self.keys:
            self.accept(key, self.on_key_event, [key, 1])
            # also create an up key event 
            key_up_evt = key+"-up"
            self.accept(key_up_evt, self.on_key_event, [key_up_evt, 1, True])
            # and append both keys
            self.key_map[key] = 0
            self.key_map[key_up_evt] = 0

        self.accept("wheel_up", self.on_key_event, ["wheel_up", 1])
        self.accept("wheel_down", self.on_key_event, ["wheel_down", -1])

        self.key_map["wheel_up"] = 0 
        self.key_map["wheel_down"] = 0  

    def on_update(self):
        if not self.mouseWatcherNode.hasMouse():
            self.mouseInput = Vec2(0, 0)
            return
                        
        self.get_mouse_input()
                        
        # auto center the mouse...
        if self.le.panda_app._auto_center_mouse:
            self.le.panda_app.center_mouse_pointer()

        # particularly for mouse wheels,
        if self.key_map["wheel_up"] > 0:
            self.zoom = 1
        elif self.key_map["wheel_down"] < 0:
            self.zoom = -1
        else:
            self.zoom = 0
            
        if self.key_map["escape"] > 0:
            self.le.panda_app.auto_center_mouse(False)
        elif self.key_map["mouse1"] > 0:
            self.le.panda_app.auto_center_mouse(True)
 
    def on_late_update(self):
        for key in self.key_map.keys():
            # exclude 
            if key not in self.keys or "-" in key:  
                self.key_map[key] = 0
        
    def on_stop(self):
        for key in self.key_map.keys():
            self.ignore(key)
        
    def on_key(self, key, value):
        pass
        
    def on_key_event(self, key, value, is_evt_key_up=False):
        self.key_map[key] = value
        if is_evt_key_up:
            key = key.split("-")[0]
            self.key_map[key] = 0
        
    def get_mouse_input(self):
        mouseX = self.mouseWatcherNode.getMouseX()
        mouseY = self.mouseWatcherNode.getMouseY()

        if self.le.panda_app._auto_center_mouse:
            self.__dx = mouseX - self.__lastMousePos.x
            self.__dy = mouseY - self.__lastMousePos.y
            
            if abs(self.__dx) > 0:
                self.mouseInput.x = mouseX
            else:
                self.mouseInput.x = 0
                
            if abs(self.__dy) > 0:
                self.mouseInput.y = mouseY
            else:
                self.mouseInput.y = 0
                
            self.__lastMousePos.x = mouseX
            self.__lastMousePos.y = mouseY

            return

        else:  # calculate displacemnt based to previous pos
            self.__dx = mouseX - self.__lastMousePos.x
            self.__dy = mouseY - self.__lastMousePos.y
            # print(self.__dx)
            
        # set last pos to current pos
        self.__lastMousePos.x = mouseX
        self.__lastMousePos.y = mouseY
            
        # self.mouseInput = Vec2(0, 0)
        
        if self.__dx > 0:
            self.mouseInput.x = 1
        
        if self.__dx < 0:
            self.mouseInput.x = -1
            
        if self.__dy > 0:
            self.mouseInput.y = 1
        
        if self.__dy < 0:
            self.mouseInput.y = -1
            
        # print(self.mouseInput)
