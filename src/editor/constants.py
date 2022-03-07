import os
import wx
from thirdparty.event.observable import Observable
from editor.utils.exceptionHandler import try_execute, try_execute_1
from panda3d.core import BitMask32

EDITOR_STATE = 0  # editor mode
GAME_STATE = 1  # play mode

RUN_TIME_GEO = 0
EDITOR_GEO = 1
SCENE_GEO = 2
GEO_NO_PARENT = -1

TAG_IGNORE = "SELECT_IGNORE"
TAG_PICKABLE = "PICKABLE"

ED_GEO_MASK = BitMask32.bit(0)
GAME_GEO_MASK = BitMask32.bit(1)

FILE_EXTENSIONS_ICONS_PATH = "src/editor/resources/icons/fileExtensions"
ICONS_PATH = "src/editor/resources/icons"
MODELS_PATH = "src/editor/resources"
MODELS_PATH_2 = "src/editor/resources/models"

DEFAULT_PROJECT_PATH = "src/Default Project"

# asset resources
POINT_LIGHT_MODEL = MODELS_PATH + "\\" + "Pointlight.egg.pz"
DIR_LIGHT_MODEL = MODELS_PATH + "\\" + "Dirlight.egg.pz"
SPOT_LIGHT_MODEL = MODELS_PATH + "\\" + "Spotlight.egg.pz"
CAMERA_MODEL = MODELS_PATH + "\\" + "camera.egg.pz"

CUBE_PATH = MODELS_PATH_2 + "\\" + "cube.fbx"
CAPSULE_PATH = MODELS_PATH_2 + "\\" + "capsule.fbx"
CONE_PATH = MODELS_PATH_2 + "\\" + "cone.fbx"
PLANE_PATH = MODELS_PATH_2 + "\\" + "plane.fbx"


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
obs = Observable()  # the event manager object


class DirectoryEventHandler:
    """handler all events related to project resources"""

    @staticmethod
    @obs.on("DirectoryEvent")
    def on_directory_event(*args):
        proj_browser = object_manager.get("ProjectBrowser")
        le = object_manager.get("LevelEditor")

        proj_browser.create_or_rebuild_tree("", rebuild_event=True)  # rebuild project files/tree
        # proj_browser.rebuild_tree()
        le.load_all_mods(proj_browser.resources["py"])  # reload all user mods and tools


class LevelEditorEventHandler:
    """handler all events emitted by level editor"""

    @staticmethod
    @obs.on("LevelEditorEvent")
    def on_le_event(*args):
        pass

    @staticmethod
    @obs.on("UpdatePropertiesPanel")
    def update_properties_panel(*args):
        """update properties panel based on currently selected resource or scene item"""

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

        # now make sure that it is a module, also split file name from
        # extension, level_editor.get_mod_instance takes input object's name without extenison
        obj = le.get_mod_instance(selection)
        if obj:
            prop_panel.reset()
            prop_panel.layout_object_properties(obj)
        else:
            # resets object inspection panel
            prop_panel.reset()

    @staticmethod
    @obs.on("ToggleSounds")
    def toggle_sounds(*args):
        pass

    @staticmethod
    @obs.on("ToggleSceneLights")
    def toggle_scene_lights(val=None):
        le = object_manager.get("LevelEditor")

        if val is None:
            # invert scene lights on status
            current_status = le.toggle_scene_lights()
        else:
            current_status = val

        # change graphics
        wx_main = object_manager.get("WxMain")
        if current_status:
            wx_main.lights_toggle_btn.SetBitmap(wx_main.lights_on_icon)
        elif not current_status:
            wx_main.lights_toggle_btn.SetBitmap(wx_main.lights_off_icon)

        wx_main.aui_manager.Update()

    @staticmethod
    @obs.on("AddLight")
    def add_light(light):
        object_manager.get("LevelEditor").add_light(light)

    @staticmethod
    @obs.on("AddCamera")
    def add_camera():
        print("currently support is limited to only camera per scene...!")
        # object_manager.get("LevelEditor").add_camera()

    @staticmethod
    @obs.on("AddObject")
    def add_object(path):
        object_manager.get("LevelEditor").add_object(path)

    @staticmethod
    @obs.on("RemoveNodePath")
    def delete_object():
        def on_ok(*args):
            le = object_manager.get("LevelEditor")
            le.remove_selected_nps()

        wx_main = object_manager.get("WxMain")
        dm = wx_main.dialogue_manager
        dm.create_dialog("YesNoDialog", "Delete Item",
                         dm,
                         descriptor_text="Are you sure you want to delete this selection ?",
                         ok_call=on_ok)

    @staticmethod
    @obs.on("NodepathSelected")
    def np_selected(nps, *args):
        pp = object_manager.get("PropertiesPanel")
        np = nps[0].getNetPythonTag(TAG_PICKABLE)

        if np is not False:
            pp.layout_object_properties(np)

            # also unselect this, since as properties will be displaying in
            # properties panel as well
            object_manager.get("ProjectBrowser").UnselectAll()

    @staticmethod
    @obs.on("DeselectAllNps")
    def deselect_all():
        object_manager.get("PropertiesPanel").reset()
        object_manager.get("ProjectBrowser").UnselectAll()

    @staticmethod
    @obs.on("XFormTask")
    def on_xform_task():
        pp = object_manager.get("PropertiesPanel")
        if pp.get_object():
            pp.update_properties_panel()


class ProjectEventHandler:
    """handler all project related events"""

    @staticmethod
    @obs.on("ProjectEvent")
    def on_proj_event(evt, *args):
        if evt == "AppendLibrary":
            ProjectEventHandler.append_library()

        elif evt == "SetProject":
            ProjectEventHandler.create_new_project()

        elif evt == "LoadDefaultProject":
            ProjectEventHandler.load_default_project()

        elif evt == "NewScene":
            ProjectEventHandler.start_new_scene()

        elif evt == "SwitchEdState":
            le = object_manager.get("LevelEditor")
            wx_main = object_manager.get("WxMain")

            # get the current editor state
            ed_state = le.ed_state  # 0 = editor, 1 = game_state

            if len(args) > 0:
                le.switch_state(args[0])

            elif ed_state == 0:
                le.switch_state(1)

            elif ed_state == 1:
                le.switch_state(0)

            # change graphics
            if le.ed_state == 1:
                wx_main.ply_btn.SetBitmap(wx_main.stop_icon)
            elif le.ed_state == 0:
                wx_main.ply_btn.SetBitmap(wx_main.play_icon)

            wx_main.aui_manager.Update()

        elif evt == "ToggleSceneLights":
            LevelEditorEventHandler.toggle_scene_lights()

    def load_default_project(self):
        pass

    @staticmethod
    def create_new_project(*args):
        le = object_manager.get("LevelEditor")
        wx_main = object_manager.get("WxMain")
        file_browser = object_manager.get("ProjectBrowser")

        if le.ed_state is GAME_STATE:
            print("ProjectEventHandler --> Exit game mode to create a new project.")
            return

        def on_ok(proj_name, proj_path):
            if not proj_name.isalnum():  # validate project name
                print("ProjectEventHandler --> project name should not be null and can"
                      " only consists of alphabets and digits.")
                return

            # validate project path and set project
            #  and os.listdir(proj_path) == 0
            if os.path.exists(proj_path) and os.path.isdir(proj_path):
                le.create_new_project(proj_path)

                file_browser.create_or_rebuild_tree(proj_path, rebuild_event=False)
                file_browser.Refresh()

                DirectoryEventHandler.on_directory_event()

                wx_main.SetTitle("PandaEditor " + "(" + proj_name + ")")

                dialog.Close()  # finally, close project dialog
            else:
                print("ProjectEventHandler --> unable to create a new project, probably path is invalid.")

        def on_cancel(*_args):
            pass

        wx_main = object_manager.get("WxMain")
        dm = wx_main.dialogue_manager
        dialog = dm.create_dialog("ProjectDialog", "PandaEditor", dm, ok_call=on_ok, cancel_call=on_cancel)
        return

    @staticmethod
    def open_project(*args):
        pass

    @staticmethod
    def start_new_scene(*args):
        le = object_manager.get("LevelEditor")

        if le.ed_state is GAME_STATE:
            print("Exit game mode to create a new scene..!")
            return

        dlg = wx.MessageDialog(parent=None,
                               message="Confirm start new scene ?",
                               caption="NewScene",
                               style=wx.YES | wx.NO | wx.ICON_QUESTION)
        res = dlg.ShowModal()
        if res == wx.ID_YES:
            le = object_manager.get("LevelEditor")
            le.create_new_scene()

    @staticmethod
    def append_library(*args):
        le = object_manager.get("LevelEditor")

        if le.ed_state is GAME_STATE:
            print("Exit game mode to append new library..!")
            return

        default_path_to = "C:/Users/Obaid ur Rehman/Desktop/Panda3d/P3dLevelEditor/game"

        dir_dialog = wx.DirDialog(None, style=wx.DD_DEFAULT_STYLE)

        if dir_dialog.ShowModal() == wx.ID_OK:
            path = dir_dialog.GetPath()
            name = ""
            dlg = wx.TextEntryDialog(object_manager.get("WxMain"), 'LibraryName', 'Set Library Name', value="")
            if dlg.ShowModal() == wx.ID_OK:
                name = dlg.GetValue()
            if name == "":
                return

            if le.project.on_add_library(name, path):
                object_manager.get("ProjectBrowser").append_library(name, path)
                DirectoryEventHandler.on_directory_event()

    @staticmethod
    @obs.on("OnRemoveLibrary")
    def remove_library(lib_path):
        """event called when a library is removed"""

        le = object_manager.get("LevelEditor")
        le.project.on_remove_library(lib_path)
        DirectoryEventHandler.on_directory_event()

    @staticmethod
    @obs.on("CreateAsset")
    def create_asset(_type, path):
        def create_file(file_name, base_cls=None, py_mod=False, ed_plugin=False):

            def indent(_file, spaces):
                # add indentation by adding empty spaces
                for i in range(spaces):
                    _file.write(" ")

            cls_name = file_name.split("/")[-1]
            cls_name = cls_name[0].upper() + cls_name[1:]
            file_name = file_name[0].lower() + file_name[1:] + ".py"

            with open(file_name, "w") as file:

                file.write("import math\n")
                file.write("import panda3d.core as p3dCore\n")

                if base_cls:
                    base_mod = base_cls[0].lower() + base_cls[1:]  # file name as on disk e.g. pModBase
                    base_cls = base_cls[0].upper() + base_cls[1:]  # class name as PModBase
                    file.write("from editor.core.{0} import {1}\n\n\n".format(base_mod, base_cls))
                else:
                    file.write("\n\n")
                    base_cls = "object"

                # class header and init method
                file.write("class {0}({1}):".format(cls_name, base_cls))
                file.write("\n")
                indent(file, 4)
                file.write("def __init__(self, *args, **kwargs):\n")

                if base_cls != "object":

                    indent(file, 8)

                    if ed_plugin:
                        file.write(base_cls + ".__init__(self, *args, **kwargs)\n")
                        indent(file, 8)
                        file.write("self.is_ed_plugin(True)\n\n")
                    else:
                        file.write(base_cls + ".__init__(self, *args, **kwargs)\n\n")

                    indent(file, 8)
                    file.write("# __init__ should contain anything except for variable declaration...!\n\n")

                else:
                    file.write("pass\n\n")

                if py_mod:
                    return

                start_func_name = "on_start"

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
            try_execute(func, path, py_mod=True)

        elif _type == "p3d_user_mod":
            try_execute(func, path, base_cls="pModBase")

        elif _type == "p3d_ed_tool":
            try_execute(func, path, base_cls="pModBase", ed_plugin=True)

    @staticmethod
    @obs.on("ToolExecutionFailed")
    def plugin_execution_failed(tool_name):
        print("plugin {} execution failed", tool_name)


class UserModuleEvent:
    """Handle all events coming from UserModules"""

    @staticmethod
    @obs.on("UserModuleEvent")
    def user_module_event(evt):
        if evt == "PluginExecutionFailed":
            UserModuleEvent.plugin_execution_failed()

    @staticmethod
    def plugin_execution_failed(*args):
        print("plugin executing failed...!")
        le = object_manager.get("LevelEditor")
        le.unregister_editor_plugins()


class WxEventHandler:
    """Handles events coming from different wx widgets"""

    @staticmethod
    @obs.on("WxEvent")
    def on_wx_event(evt_type, **kwargs):
        if evt_type == "load_resource":
            WxEventHandler.load_resource(**kwargs)

    @staticmethod
    def load_resource(**kwargs):
        le = object_manager.get("LevelEditor")

        resource_type = kwargs.pop("resource_type", None)
        resource_path = kwargs.pop("resource_path", "")

        if resource_type is "3d_model":
            xx = resource_path[len(le.project.project_path)+1:]
            le.load_model(xx)

    @staticmethod
    @obs.on("SelectTreeItem")
    def on_tree_item_select(selections, *args):
        """event called when a resource item is selected in resource browser"""

        cls = None

        for file_name, data in selections:
            # tree item data can either be a path(string) or a sub-object of a module
            # if data is a sub-object
            if type(data) is not str:
                cls = data
            else:
                # try to get module from level editor
                name = file_name.split(".")[0]
                cls = object_manager.get("LevelEditor").get_mod_instance(name)

        if cls is None:
            object_manager.get("PropertiesPanel").reset()
            return

        object_manager.get("PropertiesPanel").layout_object_properties(cls)

    @staticmethod
    @obs.on("EventWxSize")
    def event_size(size, *args):
        pass
        # object_manager.get("SceneUI").on_resize(size.x, size.y)

    @staticmethod
    @obs.on("EventAddTab")
    def evt_add_tab(tab):
        """event called when a request to a new tab is made from main menu bar"""

        object_manager.get("WxMain").add_tab(tab)

    @staticmethod
    @obs.on("UILayoutEvent")
    def evt_ui_layout(evt):
        if evt == "SaveUILayout":
            WxEventHandler.register_user_layout()

    @staticmethod
    def register_user_layout():
        wx_main = object_manager.get("WxMain")
        aui_mgr = wx_main.aui_manager

        def on_ok(layout_name):
            if layout_name == "":
                return

            if aui_mgr.save_current_layout(layout_name):
                wx_main.menu_bar.add_layout_menu(layout_name)

        # get a name for this layout from user
        dm = wx_main.dialogue_manager
        dm.create_dialog("TextEntryDialog", "NewEditorLayout", dm,
                         descriptor_text="Enter new layout name", ok_call=on_ok)

    @staticmethod
    @obs.on("LoadUserLayout")
    def load_user_layout(layout):
        wx_main = object_manager.get("WxMain")
        aui_mgr = wx_main.aui_manager

        if aui_mgr.load_layout(layout):
            print("loaded layout: ", layout)


@obs.on("PropertyModified")
def property_modified():
    app = object_manager.get("P3dApp")
    app.update_gizmo()


@obs.on("EvtCloseApp")
def exit_app(close_wx=True):
    print("exited")
    if close_wx:
        object_manager.get("WxMain").Close()
    object_manager.get("P3dApp").Quit()
