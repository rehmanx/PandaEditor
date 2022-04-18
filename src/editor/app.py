from editor.showBase import ShowBase
from editor.wxUI.wxMain import WxFrame
from editor.levelEditor import LevelEditor
from editor.p3d import wxPanda, MOUSE_ALT
from editor.constants import *
from panda3d.core import WindowProperties


class MyApp(wxPanda.App):
    _auto_center_mouse = False
    wx_main = None
    showbase = None

    level_editor = None

    def init(self):
        object_manager.add_object("P3dApp", self)

        self.wx_main = WxFrame(parent=None, title="PandaEditor (Default Project)", size=(800, 600))
        self.showbase = ShowBase(self.wx_main.ed_viewport_panel)

        self.wx_main.Show()
        self.ReplaceEventLoop()

        wx.CallAfter(self.finish_init)

    def finish_init(self):
        self.showbase.finish_init()
        self.level_editor = LevelEditor(self)
        self.wx_main.finish_init()
        self.level_editor.start()

    def center_mouse_pointer(self):
        win = self.wx_main.ed_viewport_panel.GetWindow()
        win.movePointer(0, int(win.getProperties().getXSize() / 2), int(win.getProperties().getYSize() / 2))

    MOUSE_MODE_MAP = {"Absolute": WindowProperties.M_absolute,
                      "Relative": WindowProperties.M_relative,
                      "Confined": WindowProperties.M_confined}

    def set_mouse_mode(self, mode):
        if mode not in self.MOUSE_MODE_MAP.keys():
            print("Incorrect mouse mode {0}".format(mode))
            self.mouse_mode = self.MOUSE_MODE_MAP[0]
            return

        mode = self.MOUSE_MODE_MAP[mode]
        self.mouse_mode = mode
        wp = WindowProperties()
        wp.setMouseMode(mode)
        self.wx_main.ed_viewport_panel.GetWindow().requestProperties(wp)
        self.center_mouse_pointer()

    def set_cursor_hidden(self, hidden=False):
        wp = WindowProperties()
        wp.setCursorHidden(hidden)
        self.wx_main.game_viewport_panel.GetWindow().requestProperties(wp)

    def auto_center_mouse(self, value=False):
        self._auto_center_mouse = value

    def get_mouse_mode(self):
        return self.mouse_mode
