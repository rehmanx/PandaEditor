from editor.constants import object_manager
from panda3d.core import Vec3, Vec2, Vec4


class UIPreferences:
    def __init__(self, *args, **kwargs):
        pass


class EditorPreferences:
    def __init__(self, *args, **kwargs):
        self.float_precision = 4
        
        # grid
        self.grid_size = Vec2(200, 200)
        self.grid_step = 20
        self.sub_divisions = 2
        
        # mouse
        mouse_speed = 5

        # scene
        self.bg_colour = Vec4(0.3, 0.3, 0.3, 1.0)
        

class GlobalPreferences:
    def __init__(self):
        self.ed_preferences = EditorPreferences()
        
    def load(self):
        pass
    
    def get_save_data(self):
        pass
        
        