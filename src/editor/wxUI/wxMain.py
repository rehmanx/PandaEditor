import wx
import wx.lib.agw.aui as aui

from wx.lib.scrolledpanel import ScrolledPanel
from thirdparty.wxCustom.auiManager import AuiManager
from editor.wxUI.wxMenuBar import WxMenuBar
from editor.wxUI.resourceBrowser import ResourceBrowser
from editor.wxUI.inspectorPanel import InspectorPanel
from editor.wxUI.customInspectorPanel import CustomInspectorPanel
from editor.wxUI.logPanel import LogPanel
from editor.wxUI.wxDialogs import DialogManager
from editor.p3d import wxPanda
from editor.constants import object_manager, obs

# scene events
TB_EVT_NEW = wx.NewId()
TB_EVT_OPEN = wx.NewId()
TB_EVT_SAVE = wx.NewId()
TB_EVT_SAVE_AS = wx.NewId()

TB_EVT_PROJ_OPEN = wx.NewId()
TB_EVT_PROJ_SAVE = wx.NewId()
TB_EVT_APPEND_LIB = wx.NewId()

TB_EVT_PLAY = wx.NewId()
TB_EVT_TOGGLE_LIGHTS = wx.NewId()
TB_EVT_TOGGLE_SOUND = wx.NewId()

PROJ_EVENTS = {
    TB_EVT_NEW: "NewScene",
    TB_EVT_OPEN: "OpenScene",
    TB_EVT_SAVE: "SaveScene",
    TB_EVT_SAVE_AS: "SaveSceneAs",
    TB_EVT_PROJ_OPEN: "OpenProject",
    TB_EVT_PROJ_SAVE: "SaveProject",
    TB_EVT_APPEND_LIB: "AppendLibrary",

    TB_EVT_PLAY: "SwitchEdState",
    TB_EVT_TOGGLE_LIGHTS: "ToggleSceneLights",
    TB_EVT_TOGGLE_SOUND: "ToggleSounds",
}

# resources
ICON_FILE = "editor/resources/pandaIcon.ico"
NEW_ICON = "editor/resources/icons/fileNew_32.png"
OPEN_ICON = "editor/resources/icons/fileOpen_32.png"
SAVE_ICON = "editor/resources/icons/fileSave_32.png"
SAVE_AS_ICON = "editor/resources/icons/fileSaveAs_32.png"
PROJ_OPEN_ICON = "editor/resources/icons/fileOpen_32.png"
PROJ_SAVE_ICON = "editor/resources/icons/fileOpen_32.png"
IMPORT_LIBRARY_ICON = "editor/resources/icons/importLib_32.png"

PLAY_ICON = "editor/resources/icons/playIcon_32x.png"
STOP_ICON = "editor/resources/icons/stopIcon_32.png"

ALL_LIGHTS_ON_ICON = "editor/resources/icons/lightbulb_32x_on.png"
ALL_LIGHTS_OFF_ICON = "editor/resources/icons/lightbulb_32x_off.png"
SOUND_ICON = "editor/resources/icons/soundIcon.png"
NO_SOUND_ICON = "editor/resources/icons/noSoundIcon.png"

DISABLED_ICON = "editor/resources/icons/disabled_icon.png"

DEFAULT_AUI_LAYOUT = "layout2|name=FileMenuToolBar;caption=Toolbar;state=6737\
9964;dir=1;layer=10;row=0;pos=0;prop=100000;bestw=135;besth=42;minw=-1;minh=-\
1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;trans\
parent=255|name=ProjectMenuToolbar;caption=Toolbar;state=67379964;dir=1;layer=10;r\
ow=0;pos=137;prop=100000;bestw=95;besth=42;minw=-1;minh=-1;maxw=-1;maxh=-1;fl\
oatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transparent=255|name=SceneControlsToolbar\
;caption=Toolbar;state=67379964;dir=1;layer=10;row=0;pos=234;prop=100\
000;bestw=95;besth=42;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;flo\
atw=-1;floath=-1;notebookid=-1;transparent=255|name=PlayControlsToolbar;caption=\
Toolbar;state=67379964;dir=1;layer=10;row=0;pos=331;prop=100000;bestw=55;best\
h=42;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;\
notebookid=-1;transparent=255|name=EditorViewport;caption=EditorView;state=13\
4481916;dir=4;layer=0;row=0;pos=0;prop=100000;bestw=1;besth=1;minw=-1;minh=-1\
;maxw=-1;maxh=-1;floatx=-1;floaty=-1;floatw=-1;floath=-1;notebookid=-1;transp\
arent=255|name=GameViewport;caption=GameView;state=134481916;dir=4;layer=0;ro\
w=1;pos=0;prop=100000;bestw=1;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx\
=313;floaty=380;floatw=1;floath=20;notebookid=-1;transparent=255|name=ObjectI\
nspectorTab;caption=InspectorTab;state=201590780;dir=4;layer=0;row=2;pos=0;pr\
op=100000;bestw=1;besth=20;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=1018;floaty\
=383;floatw=1;floath=20;notebookid=-1;transparent=255|name=ResourceBrowser;ca\
ption=ResourceBrowser;state=201590780;dir=3;layer=1;row=0;pos=0;prop=106332;b\
estw=16;besth=35;minw=-1;minh=-1;maxw=-1;maxh=-1;floatx=509;floaty=657;floatw\
=576;floath=216;notebookid=-1;transparent=255|name=LogTab;caption=LogTab;stat\
e=201590780;dir=3;layer=1;row=0;pos=1;prop=93667;bestw=118;besth=49;minw=-1;m\
inh=-1;maxw=-1;maxh=-1;floatx=637;floaty=555;floatw=118;floath=49;notebookid\
=-1;transparent=255|dock_size(1,10,0)=44|dock_size(4,0,0)=556|dock_size(4,0,1)\
=477|dock_size(4,0,2)=331|dock_size(3,1,0)=262|"


class WxFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)

        self.load_resources()

        self.panda_app = wx.GetApp()

        icon_file = ICON_FILE
        icon = wx.Icon(icon_file, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        object_manager.add_object("WxMain", self)

        # set menu bar
        self.menu_bar = WxMenuBar(self)
        self.SetMenuBar(self.menu_bar)

        # set status bar
        self.status_bar = self.CreateStatusBar()
        self.status_bar.SetStatusText("Welcome to PandaEditor")

        # setup dialogue manager
        self.dialogue_manager = DialogManager()

        # setup aui manager
        self.aui_manager = AuiManager(self)

        self.tb_panes = []  # names of all aui toolbars

        # setup toolbars
        self.build_filemenu_tb()
        self.build_proj_menus_tb()
        self.build_scene_ctrls_tb()
        self.build_play_ctrls_tb()

        # setup different panda3d editor tabs
        # editor_viewport
        self.ed_viewport_panel = wxPanda.Viewport(self, style=wx.BORDER_SUNKEN)

        # game_viewport
        # self.game_viewport_panel = wxPanda.Viewport(self, style=wx.BORDER_SUNKEN)

        # inspector panel
        self.inspector_panel = InspectorPanel(self)
        self.inspector_panel.set_layout_auto(False)

        # log panel
        self.log_panel = LogPanel(self)

        # project browser panel----------------------
        self.proj_browser_panel = ScrolledPanel(self)
        self.proj_browser = ResourceBrowser(self.proj_browser_panel, self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.proj_browser, 1, wx.EXPAND)
        self.proj_browser_panel.SetSizer(sizer)

        self.proj_browser_panel.Layout()
        self.proj_browser_panel.SetupScrolling()
        # --------------------------------------------------

        self.panel_defs = {
            "EditorViewport": (self.ed_viewport_panel,
                               True,
                               aui.AuiPaneInfo().
                               Name("EditorViewport").
                               Caption("EditorViewport").
                               CloseButton(False).
                               MaximizeButton(True).
                               Left()),

            "ObjectInspectorTab": (self.inspector_panel,
                                   True,
                                   aui.AuiPaneInfo().
                                   Name("ObjectInspectorTab").
                                   Caption("InspectorTab").
                                   CloseButton(True).
                                   MaximizeButton(True).
                                   Top()),

            "ResourceBrowser": (self.proj_browser_panel,
                                True,
                                aui.AuiPaneInfo().
                                Name("ResourceBrowser").
                                Caption("ResourceBrowser").
                                CloseButton(True).
                                MaximizeButton(True).
                                Top()),

            "LogTab": (self.log_panel,
                       True,
                       aui.AuiPaneInfo().
                       Name("LogTab").
                       Caption("LogTab").
                       CloseButton(True).
                       MaximizeButton(True).
                       Top()),
        }

        self.default_panel_defs = self.panel_defs.copy()  # default panels

        # tell aui_manager to start managing these panels,
        for pane_def in self.panel_defs.values():
            self.aui_manager.AddPane(pane_def[0], pane_def[2])

        # load default layout
        self.aui_manager.LoadPerspective(DEFAULT_AUI_LAYOUT)
        self.aui_manager.save_layout("UILayoutGeneral", self.panel_defs.keys(), DEFAULT_AUI_LAYOUT)

        self.aui_manager.Update()

        self.SetMinSize((800, 600))
        self.Maximize(True)

        self.Bind(wx.EVT_SIZE, self.on_event_size)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_evt_left_down)
        self.Bind(wx.EVT_CLOSE, self.on_event_close)

        self.Layout()
        self.Center()

    def load_resources(self):
        self.new_icon = wx.Bitmap(NEW_ICON)
        self.open_icon = wx.Bitmap(OPEN_ICON)
        self.save_icon = wx.Bitmap(SAVE_ICON)
        self.save_as_icon = wx.Bitmap(SAVE_AS_ICON)

        self.proj_open_icon = wx.Bitmap(PROJ_OPEN_ICON)
        self.proj_save_icon = wx.Bitmap(PROJ_SAVE_ICON)
        self.import_lib_icon = wx.Bitmap(IMPORT_LIBRARY_ICON)

        self.play_icon = wx.Bitmap(PLAY_ICON)
        self.stop_icon = wx.Bitmap(STOP_ICON)

        self.lights_on_icon = wx.Bitmap(ALL_LIGHTS_ON_ICON)
        self.lights_off_icon = wx.Bitmap(ALL_LIGHTS_OFF_ICON)
        self.sound_icon = wx.Bitmap(SOUND_ICON)
        self.no_sound_icon = wx.Bitmap(NO_SOUND_ICON)

        self.disabled_icon = wx.Bitmap(DISABLED_ICON)

    def finish_init(self):
        self.on_event_size()

    def build_filemenu_tb(self):
        self.filemenu_tb = aui.AuiToolBar(self)

        new_btn = self.filemenu_tb.AddTool(TB_EVT_NEW, '', self.new_icon,
                                           disabled_bitmap=self.disabled_icon,
                                           kind=wx.ITEM_NORMAL,
                                           short_help_string="NewScene")

        save_btn = self.filemenu_tb.AddTool(TB_EVT_SAVE, '', self.save_icon,
                                            disabled_bitmap=self.disabled_icon,
                                            kind=wx.ITEM_NORMAL,
                                            short_help_string="SaveScene")

        save_as_btn = self.filemenu_tb.AddTool(TB_EVT_SAVE_AS, '', self.save_as_icon,
                                               disabled_bitmap=self.disabled_icon,
                                               kind=wx.ITEM_NORMAL,
                                               short_help_string="SaveSceneAs")

        # add to aui
        self.aui_manager.AddPane(self.filemenu_tb, aui.AuiPaneInfo().Name("FileMenuToolBar").
                                 Caption("Toolbar").ToolbarPane().Top())
        self.tb_panes.append("FileMenuToolBar")

        # events
        self.Bind(wx.EVT_TOOL, self.on_event, new_btn)
        self.Bind(wx.EVT_TOOL, self.on_event, save_btn)
        self.Bind(wx.EVT_TOOL, self.on_event, save_as_btn)

    def build_proj_menus_tb(self):
        self.proj_meuns_tb = aui.AuiToolBar(self)

        open_proj_btn = self.proj_meuns_tb.AddTool(TB_EVT_PROJ_OPEN, '', self.proj_open_icon,
                                                   disabled_bitmap=self.disabled_icon,
                                                   kind=wx.ITEM_NORMAL,
                                                   short_help_string="OpenProject")

        import_lib_btn = self.proj_meuns_tb.AddTool(TB_EVT_APPEND_LIB, '', self.import_lib_icon,
                                                    disabled_bitmap=self.disabled_icon,
                                                    kind=wx.ITEM_NORMAL,
                                                    short_help_string="AppendLibrary")

        # add to aui
        self.aui_manager.AddPane(self.proj_meuns_tb, aui.AuiPaneInfo().Name("ProjectMenuToolbar").
                                 Caption("Toolbar").ToolbarPane().Top())
        self.tb_panes.append("ProjectMenuToolbar")

        self.Bind(wx.EVT_TOOL, self.on_event, open_proj_btn)
        self.Bind(wx.EVT_TOOL, self.on_event, import_lib_btn)

    def build_play_ctrls_tb(self):
        # build
        self.playctrls_tb = aui.AuiToolBar(self)

        self.ply_btn = self.playctrls_tb.AddTool(TB_EVT_PLAY, "", bitmap=self.play_icon,
                                                 disabled_bitmap=self.disabled_icon,
                                                 kind=wx.ITEM_NORMAL,
                                                 short_help_string="StartGame")

        # add to aui
        self.aui_manager.AddPane(self.playctrls_tb, aui.AuiPaneInfo().Name("PlayControlsToolbar").
                                 Caption("Toolbar").ToolbarPane().Top())
        self.tb_panes.append("PlayControlsToolbar")

        # events
        self.Bind(wx.EVT_TOOL, self.on_event, self.ply_btn)

    def build_scene_ctrls_tb(self):
        self.scene_ctrls_tb = aui.AuiToolBar(self)

        self.lights_toggle_btn = self.scene_ctrls_tb.AddTool(TB_EVT_TOGGLE_LIGHTS, "",
                                                             bitmap=self.lights_off_icon,
                                                             disabled_bitmap=self.disabled_icon,
                                                             kind=wx.ITEM_NORMAL,
                                                             short_help_string="ToggleSceneLights")

        self.sounds_on = True
        self.sound_toggle_btn = self.scene_ctrls_tb.AddTool(TB_EVT_TOGGLE_SOUND, "",
                                                            bitmap=self.sound_icon,
                                                            disabled_bitmap=self.disabled_icon,
                                                            kind=wx.ITEM_NORMAL,
                                                            short_help_string="ToggleSound")

        self.aui_manager.AddPane(self.scene_ctrls_tb, aui.AuiPaneInfo().Name("SceneControlsToolbar").
                                 Caption("Toolbar").ToolbarPane().Top())
        self.tb_panes.append("SceneControlsToolbar")

        self.Bind(wx.EVT_TOOL, self.on_event, self.sound_toggle_btn)
        self.Bind(wx.EVT_TOOL, self.on_event, self.lights_toggle_btn)

    def add_panel_def(self, name):
        if name not in self.panel_defs.keys():
            # create a CustomInspectorPanel
            my_panel = CustomInspectorPanel(self)

            # also create and save a panel definition for it
            paneldef = (my_panel,
                        True,
                        aui.AuiPaneInfo().
                        Name(name).
                        Caption(name).
                        CloseButton(True).
                        MaximizeButton(True).
                        Top()),

            self.panel_defs[name] = paneldef[0]

    def add_tab(self, tab):
        if tab in self.panel_defs.keys():
            paneldef = self.panel_defs[tab]
        else:
            print("unable to add tab {0}, tab is not defined in panel_definitions".format(tab))
            return

        self.aui_manager.AddPane(paneldef[0], paneldef[2])
        self.aui_manager.ShowPane(paneldef[0], True)

        if tab not in ["EditorViewport", "GameViewport", "ResourceBrowser", "LogTab", ]:
            paneldef[0].enable()

        self.aui_manager.Update()

    def on_pane_close(self, pane_name):
        if pane_name in self.panel_defs.keys():
            paneldef = self.panel_defs[pane_name]
        else:
            print("unable to remove tab {0}, tab is not defined in pane_defs".format(pane_name))
            return

        self.aui_manager.Update()

    def delete_tab(self, tab):
        """permanently deletes a tab from aui manager's managed tab's list"""
        if tab in self.panel_defs.keys():
            panel_def = self.panel_defs[tab]

            # tell aui manager to remove and detach the paneldef from managed panes
            self.aui_manager.ClosePane(panel_def[2])
            self.aui_manager.DetachPane(panel_def[0])

            # now destroy the wx panel itself
            panel_def[0].Destroy()

            # finally remove from panel_defs repo
            del self.panel_defs[tab]
            print("deleted tab {0}".format(panel_def[0]))
            # sometimes aui manager crashes during Update when window is minimized and
            # or aui manager is not in focus
            try:
                self.aui_manager.Update()
            except:
                pass

    def set_status_bar_text(self, txt: str):
        self.status_bar.SetStatusText(txt)

    @staticmethod
    def get_default_layout():
        return DEFAULT_AUI_LAYOUT

    def get_panel_defs(self):
        return self.panel_defs

    def get_save_data(self):
        pass

    def get_user_tabs(self):
        keys = list(self.panel_defs.keys())
        user_tabs = keys[len(self.default_panel_defs):]
        return user_tabs

    def on_event(self, evt):
        if evt.GetId() in PROJ_EVENTS:
            obs.trigger("ProjectEvent", PROJ_EVENTS[evt.GetId()])

        evt.Skip()

    def on_evt_left_down(self, evt):
        # print("left down")
        evt.Skip()

    def on_event_size(self, event=None):
        size = self.ed_viewport_panel.GetSize()
        obs.trigger("EventWxSize", size)
        if event is not None:
            event.Skip()

    def on_event_close(self, event):
        obs.trigger("EvtCloseApp", close_wx=False)
        event.Skip()
