import os
import wx
from thirdparty.event.observable import Observable
from editor.utils.exceptionHandler import try_execute

RUN_TIME_GEO = 0
EDITOR_GEO = 1
SCENE_GEO = 2
GEO_NO_PARENT = -1

TAG_IGNORE = "SELECT_IGNORE"
TAG_PICKABLE = "PICKABLE"

# asset resources
POINT_LIGHT_MODEL = "editor/resources/Pointlight.egg.pz"
DIR_LIGHT_MODEL = "editor/resources/Dirlight.egg.pz"
SPOT_LIGHT_MODEL = "editor/resources/Spotlight.egg.pz"
CAMERA_MODEL = "editor/resources/camera.egg.pz"

CUBE_PATH = "editor/resources/models/cube.fbx"
CAPSULE_PATH = "editor/resources/models/capsule.fbx"
CONE_PATH = ""
PLANE_PATH = "editor/resources/models/plane.fbx"


class ObjectManager:
    def __init__(self):
        self.object_dictionary = {}

    def add_object(self, name, obj):
        if not self.object_dictionary.__contains__(name):
            self.object_dictionary[name] = obj

    def remove_object(self, name):
        if self.object_dictionary.__contains__(name):
            self.object_dictionary.pop(name)

    def get(self, name):
        if self.object_dictionary.__contains__(name):
            return self.object_dictionary[name]
        return None

    def remove_all_objects(self):
        self.object_dictionary.clear()


object_manager = ObjectManager()
# the event manager object
obs = Observable()


# ---------------------WX EVENTS-------------------------#
@obs.on("SelectTreeItem")
def on_tree_item_select(selections, *args):
    cls = None

    for file_name, data in selections:
        # tree item data can either be a path(string) or a sub-object of a module
        # if data is a sub-object
        if type(data) is not str:
            cls = data
        else:
            # try get module from level editor
            name = file_name.split(".")[0]
            cls = object_manager.get("LevelEditor").get_mod_instance(name)

    if cls is None:
        object_manager.get("PropertiesPanel").reset()
        return

    object_manager.get("PropertiesPanel").layout_object_properties(cls)


@obs.on("EventWxSize")
def event_size(size, *args):
    # scene ui is initialized after wx ui,
    # so make sure of that
    if object_manager.get("SceneUI") is None:
        return
    object_manager.get("SceneUI").on_resize(size.x, size.y)


@obs.on("DirectoryEvent")
def directory_event(*args):
    proj_browser = object_manager.get("ProjectBrowser")
    le = object_manager.get("LevelEditor")

    proj_browser.rebuild_tree()  # rebuild project files/tree
    # TO: DO this should be done in ResourceHandler
    le.load_all_modules()  # reload all user mods and tools


@obs.on("UpdatePropertiesPanel")
def update_properties_panel(*args):
    le = object_manager.get("LevelEditor")
    proj_browser = object_manager.get("ProjectBrowser")
    prop_panel = object_manager.get("PropertiesPanel")

    # update properties panel
    # check if any tree item is currently selected if yes then show it's updated properties
    selection = proj_browser.GetSelection()
    if selection:
        selection = proj_browser.GetItemText(selection)
        selection = selection.split(".")[0]
    else:
        selection = "-1"

    # now make sure that it is an asset, also split file name from 
    # extension, level_editor.get_mod_instance takes input object's name without extenison
    obj = le.get_mod_instance(selection)
    if obj:
        prop_panel.reset()
        prop_panel.layout_object_properties(obj)
    else:
        # resets object inspection panel
        prop_panel.reset()


@obs.on("EventAddTab")
def evt_add_tab(tab):
    object_manager.get("WxMain").add_tab(tab)


@obs.on("UILayoutEvent")
def evt_ui_layout(evt):
    if evt == "SaveUILayout":
        register_user_layout()


@obs.on("UnregisterEdTools")
def unregister_ed_tools():
    # clear menu bar menus
    object_manager.get("WxMain").menu_bar.clear_user_menus()
    # clear custom panel definitions defined in wx_main.user_panels


@obs.on("RegisterUserTab")
def register_user_tab(tab, obj):
    # print("{0} registered".format(tab))
    name, func = tab
    wx_main = object_manager.get("WxMain")
    # 1: create and add a new menu to menu bar
    wx_main.menu_bar.add_user_menu(name, func)

    # 2: if a function has been associated with a menu item then the associated
    # function will be called when menu is clicked, otherwise a new wx tab will be
    # created and the object passed as argument to this event/function,
    # will be attached to the new tab, the object to which a tab is associated will
    # be un-editable by default PandaEditor's object inspector panel, and the associated object will
    # be completely responsible for drawing any ui widget to it's associated tab
    tab = name.split("/")[-1]
    if (tab not in wx_main.get_user_tabs()) and (func is None) and (obj is not None):
        wx_main.add_panel_def(tab)
        panel = wx_main.get_panel_defs()[tab][0]
        panel.set_object(obj)
        panel.set_layout_auto(True)


@obs.on("RefreshUserTabs")
def refresh_user_tabs(new_tabs):
    wx_main = object_manager.get("WxMain")
    le = object_manager.get("LevelEditor")

    # start refreshing user tabs by removing any existing user panel definitions not in new_tabs
    current_user_tabs = wx_main.get_user_tabs()

    for tab in current_user_tabs:
        panel = wx_main.get_panel_defs()[tab][0]
        panel_obj_name = panel.get_object().get_name()
        panel_obj = le.get_mod_instance(panel_obj_name)

        if tab in new_tabs:  # then refresh it
            panel.refresh(panel_obj)
        else:
            wx_main.delete_tab(tab)


@obs.on("RegisterUserLayout")
def register_user_layout():
    wx_main = object_manager.get("WxMain")
    aui_mgr = wx_main.aui_manager

    def on_ok(layout_name):
        if layout_name == "":
            return

        perspective = aui_mgr.SavePerspective()

        if aui_mgr.save_layout(layout_name, wx_main.aui_manager.GetAllPanes(), perspective):
            wx_main.menu_bar.add_layout_menu(layout_name)

    # get a name for this layout from user
    dm = wx_main.dialogue_manager
    dm.create_dialog("TextEntryDialog", "NewEditorLayout", descriptor_text="Enter new layout name", ok_call=on_ok)


@obs.on("LoadUserLayout")
def load_user_layout(layout):
    wx_main = object_manager.get("WxMain")
    aui_mgr = wx_main.aui_manager

    if aui_mgr.load_layout(layout):
        print("loaded layout: ", layout)


@obs.on("SetStatusBarText")
def set_status_bar_text(text):
    if text == "":
        text = "PandaEditor"


# ---------------------EDITOR EVENTS-------------------------#
@obs.on("AddLight")
def add_light(light):
    object_manager.get("LevelEditor").add_light(light)


@obs.on("AddCamera")
def add_camera():
    object_manager.get("LevelEditor").add_camera()


@obs.on("AddObject")
def add_object(path):
    object_manager.get("LevelEditor").add_object(path)


@obs.on("DeleteObject")
def delete_object():
    def on_ok(*args):
        le = object_manager.get("LevelEditor")
        le.delete_selected()

    wx_main = object_manager.get("WxMain")
    dm = wx_main.dialogue_manager
    dm.create_dialog("YesNoDialog", "Delete Item", descriptor_text="Are you sure you want to delete this selection ?",
                     ok_call=on_ok)


@obs.on("ToggleSounds")
def toggle_sound(*args):
    wx_main = object_manager.get("WxMain")

    if wx_main.sounds_on:
        wx_main.sounds_on = False
        wx_main.sound_toggle_btn.SetBitmap(wx_main.no_sound_icon)
    else:
        wx_main.sound_toggle_btn.SetBitmap(wx_main.sound_icon)
        wx_main.sounds_on = True

    wx_main.aui_manager.Update()


@obs.on("LoadModel")
def load_model(name, geo, *args):
    model = object_manager.get("LevelEditor").load_model(name, geo)
    return model


@obs.on("NodepathSelected")
def np_selected(nps, *args):
    pp = object_manager.get("PropertiesPanel")
    np = nps[0].getNetPythonTag(TAG_PICKABLE)
    if np is not False:
        pp.layout_object_properties(np)

        # also unselect this, since is's properties will be displaying in 
        # properties panel as well
        object_manager.get("ProjectBrowser").UnselectAll()


@obs.on("DeselectAllNps")
def deselect_all():
    pp = object_manager.get("PropertiesPanel").reset()
    object_manager.get("ProjectBrowser").UnselectAll()


@obs.on("XFormTask")
def on_xform_task():
    pp = object_manager.get("PropertiesPanel")
    if pp.get_object():
        pp.update_properties_panel()


@obs.on("PropertyModified")
def property_modified():
    app = object_manager.get("P3dApp")
    app.update_gizmo()


@obs.on("ToolExecutionFailed")
def tool_execution_failed(tool_name):
    print("tool execution failed", tool_name)


@obs.on("SetModEnabledStatus")
def set_mod_active(mod):
    x = object_manager.get("LevelEditor").get_mod_instance(mod[0].upper() + mod[1:])
    if x.is_enabled():
        x.set_enabled(False)
    else:
        x.set_enabled(True)


@obs.on("OnModuleLoaded")
def on_module_loaded(module):
    asset_browser = object_manager.get("ProjectBrowser")

    def load_sub_objects(objs=[], parent_item=None):
        for obj in objs:
            # INCOMPLETE SECTION, MAKE SURE AN OBJECT IS NOT OF BUILT IN TYPES
            # ----------------------------------------------------------------

            sub_obj_name = obj.__class__.__name__
            item = asset_browser.AppendItem(parent_item, sub_obj_name, data=obj,
                                            image=asset_browser.file_img_index)

            if obj.are_sub_objects_valid():
                sub_objs = obj.get_sub_objects()
                load_sub_objects(sub_objs, item)

    parent_mod_name = module.__class__.__name__
    parent_mod_name = parent_mod_name[0].lower() + parent_mod_name[1:]
    parent_mod_name = parent_mod_name + ".py"
    parent_item = asset_browser.get_item_by_name(item_name=parent_mod_name)

    if module.are_sub_objects_valid() and parent_item is not None:
        sub_objs = module.get_sub_objects()
        load_sub_objects(sub_objs, parent_item)


# ---------------------PROJECT EVENTS-------------------------#

@obs.on("ProjectEvent")
def on_proj_event(evt, *args):
    if evt == "AppendLibrary":
        append_library()

    elif evt == "SetProject":
        set_project()

    elif evt == "NewScene":
        start_new_scene()

    elif evt == "SwitchEdState":
        le = object_manager.get("LevelEditor")
        wx_main = object_manager.get("WxMain")

        # get the current editor state    
        ed_state = le.get_editor_state()  # 0 = editor, 1 = game_state

        if len(args) > 0:
            le.switch_state(args[0])

        elif ed_state == 0:
            le.switch_state(1)

        elif ed_state == 1:
            le.switch_state(0)

        # get updated state
        ed_state = le.get_editor_state()

        # change graphics
        if ed_state == 1:
            wx_main.ply_btn.SetBitmap(wx_main.stop_icon)
        elif ed_state == 0:
            wx_main.ply_btn.SetBitmap(wx_main.play_icon)

        wx_main.aui_manager.Update()

    elif evt == "ToggleSceneLights":
        toggle = object_manager.get("LevelEditor").toggle_scene_lights(args)
        # change graphics
        wx_main = object_manager.get("WxMain")
        if toggle:
            wx_main.lights_toggle_btn.SetBitmap(wx_main.lights_on_icon)
        elif not toggle:
            wx_main.lights_toggle_btn.SetBitmap(wx_main.lights_off_icon)
        wx_main.aui_manager.Update()


def set_project(*args):
    dir_dialog = wx.DirDialog(None,
                              style=wx.DD_DEFAULT_STYLE,
                              defaultPath="C:/Users/Obaid ur Rehman/Desktop/Panda3d/P3dLevelEditor/game")

    if dir_dialog.ShowModal() == wx.ID_OK:
        path = dir_dialog.GetPath()

        # make sure the target directory is empty
        if len(os.listdir(path)) > 0:
            print("SetProjectError: directory must be empty")
            return

        dir_dialog.Destroy()
        le = object_manager.get("LevelEditor")
        res = le.setup_project(path)
        if res is True:
            file_browser = object_manager.get("ProjectBrowser")
            file_browser.build_tree(path)
            file_browser.Refresh()


def open_project():
    pass


def start_new_scene(*args):
    dlg = wx.MessageDialog(parent=None,
                           message="Confirm start new scene ?",
                           caption="NewScene",
                           style=wx.YES | wx.NO | wx.ICON_QUESTION)
    res = dlg.ShowModal()
    if res == wx.ID_YES:
        le = object_manager.get("LevelEditor")
        le.start_new_scene()


def append_library():
    le = object_manager.get("LevelEditor")

    default_path_to = "C:/Users/Obaid ur Rehman/Desktop/Panda3d/P3dLevelEditor/game"
    dir_dialog = wx.DirDialog(None, style=wx.DD_DEFAULT_STYLE, defaultPath=default_path_to)
    if dir_dialog.ShowModal() == wx.ID_OK:
        path = dir_dialog.GetPath()
        name = ""
        dlg = wx.TextEntryDialog(object_manager.get("WxMain"), 'LibraryName', 'Set Library Name', value="")
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetValue()
        if name == "":
            return

        res_a = le.project.on_add_library(name, path)
        res_b = object_manager.get("ProjectBrowser").append_library(name, path)

        if res_a and res_b:
            directory_event()
            # object_manager.get("WxFileBrowser").build_tree(path, root_name=name, initial=False)


@obs.on("OnRemoveLibrary")
def remove_library(lib_path):
    le = object_manager.get("LevelEditor")
    le.project.on_remove_library(lib_path)


@obs.on("CreateAsset")
def create_asset(_type, path):
    def create_file(file_name, base_cls=None, start_func_name="on_start"):
        def indent(_file, spaces):
            # add indentation by adding empty spaces
            for i in range(spaces):
                _file.write(" ")

        cls_name = file_name.split("/")[-1]
        cls_name = cls_name[0].upper() + cls_name[1:]
        file_name = file_name[0].lower() + file_name[1:] + ".py"

        with open(file_name, "w") as file:

            file.write("import math\n")
            file.write("import panda3d.core as pm\n")

            if base_cls:
                base_mod = base_cls[0].lower() + base_cls[1:]
                base_cls = base_cls[0].upper() + base_cls[1:]
                file.write("from editor.p3d.{0} import {1}\n\n\n".format(base_mod, base_cls))
            else:
                file.write("\n")
                base_cls = "object"

            # class header and init method
            file.write("class {0}( {1} ):".format(cls_name, base_cls))
            file.write("\n")
            indent(file, 4)
            file.write("def __init__(self, *args, **kwargs):\n")

            indent(file, 8)
            if base_cls != "object":
                file.write(base_cls + ".__init__(self, *args, **kwargs)\n\n")
            else:
                file.write("pass\n\n")

            # write on start method
            indent(file, 4)
            file.write("# {0} method is called once\n".format(start_func_name))
            indent(file, 4)
            file.write("def {0}(self):\n".format(start_func_name))
            indent(file, 8)
            file.write("pass\n\n")

            # write on update method
            indent(file, 4)
            file.write("# update method is called every frame\n")
            indent(file, 4)
            file.write("def on_update(self):\n")
            indent(file, 8)
            file.write("pass\n")

    func = create_file

    if _type == "py_mod":
        try_execute(func, path, start_func_name="on_enable")

    elif _type == "p3d_user_mod":
        try_execute(func, path, base_cls="pModBase", start_func_name="on_start")

    elif _type == "p3d_ed_tool":
        try_execute(func, path, base_cls="pToolBase", start_func_name="on_enable")


# ---------------------P3dApp(Application) EVENTS-------------------------#
@obs.on("EvtCloseApp")
def exit_app(close_wx=True):
    print("exited")
    if close_wx:
        object_manager.get("WxMain").Close()
    object_manager.get("P3dApp").Quit()
