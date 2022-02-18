import editor.gizmos as gizmos

from editor.showBase import ShowBase
from direct.showbase.ShowBase import taskMgr
from editor.wxUI.wxMain import WxFrame
from editor.levelEditor import LevelEditor
from editor.p3d import ThreeAxisGrid, wxPanda, MOUSE_ALT
from editor.selection import Selection
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
        self.selection = None
        self.gizmo = False
        self.gizmo_mgr = None
        self.update_task = None
        self.mouse_mode = None

        # set this variable to true as soon as pointer enters window and false on leave
        self.mouse_in_viewport = False

        self.mouse_1_down = False
        self.mouse_2_down = False

        self._auto_center_mouse = False

        self.showbase.finish_init()

        self.grid = ThreeAxisGrid(rootNp=self.showbase.edRender, xsize=200, ysize=200, gridstep=20,
                                  subdiv=4)
        self.grid_np = self.grid.create()
        self.grid_np.reparent_to(self.showbase.edRender)
        self.grid_np.show(ED_GEO_MASK)
        self.grid_np.hide(GAME_GEO_MASK)

        '''setup selection and gizmos'''
        self.setup_selection_system()

        self.setup_gizmo_manager()

        '''start the editor'''
        self.level_editor = LevelEditor(self)

        self.wx_main.finish_init()

        # bind events
        self.key_event_map = {"q": (self.set_active_gizmo, None),
                              "w": (self.set_active_gizmo, "pos"),
                              "e": (self.set_active_gizmo, "rot"),
                              "r": (self.set_active_gizmo, "scl"),
                              "space": (self.toggle_gizmo_local, None),
                              "+": (self.gizmo_mgr.SetSize, 2),
                              "-": (self.gizmo_mgr.SetSize, 0.5),
                              "control-d": (self.level_editor.duplicate_object, []),
                              "x": (self.level_editor.on_remove, None),

                              "mouse1": (self.on_mouse1_down, None),
                              "mouse2": (self.on_mouse2_down, None),

                              "mouse1-up": (self.on_mouse1_up, None),
                              "mouse2-up": (self.on_mouse2_up, None),

                              "shift-mouse1": (self.on_mouse1_down, [True]),
                              "control-mouse1": (self.on_mouse1_down, None)
                              }
        self.bind_key_events()

        # start update and late update tasks
        self.update_task = taskMgr.add(self.update, 'EditorUpdateTask', sort=0)
        self.late_update_task = taskMgr.add(self.late_update, 'EditorLateUpdateTask', sort=1)

        # setup a default working project
        # curr_working_dir = os.getcwd()
        # default_dir = curr_working_dir + "\\game"
        # self.level_editor.load_default_project(default_dir)
        self.level_editor.start()

    def setup_selection_system(self):
        self.selection = Selection(
            camera=self.showbase.ed_camera,
            rootNp=self.showbase.edRender,
            root2d=self.showbase.edRender2d,
            win=self.showbase.win,
            mouseWatcherNode=self.showbase.ed_mouse_watcher_node
        )

    def setup_gizmo_manager(self):
        """Create gizmo manager."""
        self.gizmo_mgr_root_np = self.showbase.edRender.attachNewNode('gizmoManager')
        kwargs = {
            'camera': self.showbase.ed_camera,
            'rootNp': self.gizmo_mgr_root_np,
            'win': self.showbase.win,
            'mouseWatcherNode': self.showbase.ed_mouse_watcher_node
        }
        self.gizmo_mgr = gizmos.Manager(**kwargs)
        self.gizmo_mgr.AddGizmo(gizmos.Translation('pos', **kwargs))
        self.gizmo_mgr.AddGizmo(gizmos.Rotation('rot', **kwargs))
        self.gizmo_mgr.AddGizmo(gizmos.Scale('scl', **kwargs))

    def start_transform(self):
        self.gizmo = True
        self.update_gizmo()

    def stop_transform(self):
        self.gizmo = False

    def set_active_gizmo(self, gizmo):
        self.level_editor.active_gizmo = gizmo
        if len(self.selection.get_selections()) > 0:
            self.gizmo_mgr.SetActiveGizmo(gizmo)
            self.update_gizmo()

    def set_gizmo_local(self, val):
        self.gizmo_mgr.SetLocal(val)

    def toggle_gizmo_local(self, *args):
        self.gizmo_mgr.ToggleLocal()

    def update_gizmo(self):
        nps = self.selection.get_selections()
        self.gizmo_mgr.AttachNodePaths(nps)
        self.gizmo_mgr.RefreshActiveGizmo()

    def bind_key_events(self):
        for key in self.key_event_map.keys():
            func = self.key_event_map[key][0]
            args = self.key_event_map[key][1]

            if args is None:
                self.accept(key, func)
            else:
                self.accept(key, func, [args])

    def unbind_key_events(self):
        for key in self.key_event_map.keys():
            self.ignore(key)

    def on_mouse1_down(self, shift=False):
        self.mouse_1_down = True

        if not self.gizmo_mgr.IsDragging() and MOUSE_ALT not in self.showbase.ed_camera.mouse.modifiers:
            self.selection.start_drag_select(shift)

        elif self.gizmo_mgr.IsDragging():
            self.start_transform()

    def on_mouse1_up(self):
        self.mouse_1_down = False

        nps = []
        if self.selection.marquee.IsRunning():
            nps = self.selection.stop_drag_select()
            # start transform
            if len(nps) > 0:
                # temporary ---------------- ??? for what
                # print("selected nps-->", nps)
                obs.trigger("NodepathSelected", nps)
                # --------------------------
                self.gizmo_mgr.SetActiveGizmo(self.level_editor.active_gizmo)
                self.start_transform()
            else:
                self.gizmo_mgr.SetActiveGizmo(None)
                self.gizmo = False
                # trigger deselect all
                obs.trigger("DeselectAllNps")

        elif self.gizmo_mgr.IsDragging() or self.gizmo:
            self.stop_transform()

        self.wx_main.ed_viewport_panel.OnMouseOneUp()

    def on_mouse2_down(self):
        pass

    def on_mouse2_up(self):
        pass

    def on_mouse_hover(self):
        self.wx_main.ed_viewport_panel.OnMouseHover(0, 0)

    def update(self, task):
        """update is called every frame"""
        if self.showbase.ed_mouse_watcher_node.hasMouse():
            if self.mouse_in_viewport is False:
                self.mouse_in_viewport = True
                self.wx_main.ed_viewport_panel.OnMouseEnter()

            self.on_mouse_hover()

        elif self.mouse_in_viewport is True:
            self.wx_main.ed_viewport_panel.OnMouseLeave()

            self.mouse_in_viewport = False
            self.mouse_1_down = False
            self.mouse_2_down = False

        return task.cont

    def late_update(self, task):
        """late_update is called every after update"""
        if self.gizmo_mgr.IsDragging():
            obs.trigger("XFormTask")
        return task.cont

    def center_mouse_pointer(self):
        win = self.wx_main.ed_viewport_panel.GetWindow()
        win.movePointer(0,
                        int(win.getProperties().getXSize() / 2),
                        int(win.getProperties().getYSize() / 2))

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

    def get_ed_config_file(self):
        pass
