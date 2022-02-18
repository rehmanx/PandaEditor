import os
import sys
import importlib
import traceback

from panda3d.core import NodePath, Material, DirectionalLight, PointLight
from panda3d.core import Spotlight, Camera, PerspectiveLens, Vec3, Vec4, BitMask32
from editor.p3d import pModBase, pToolBase
from editor.project import Project
from editor.constants import *
from editor.onSceneUI import OnSceneUI
from editor.nodes import EdPointLight, EdSpotLight, EdDirectionalLight, ModelNp, EdCameraNp
from editor.utils import Math
from editor.utilities import Property, ObjectData, euler_from_hpr
from editor.utils.exceptionHandler import try_execute


class LevelEditor:
    def __init__(self, panda_app, *args, **kwargs):
        object_manager.add_object("LevelEditor", self)

        self.panda_app = panda_app

        self.project = Project(self)
        self.project_set = False

        self.ed_state = EDITOR_STATE

        self.runtime_np_parent = None
        self.scene_render = None
        self.player_camera = None
        self.selected_module = None

        # gizmos, grid, selection
        self.active_gizmo = None
        self.gizmos_active = False
        self.scene_lights_on = False

        self.user_modules_running = False

        self.scene_lights = []  # all scene lights in one repository
        self.scene_cameras = []  # all scene camera in one repository

        self.ed_tools = {}
        self.user_modules = {}
        self.user_modules_data = {}
        self.mod_exec_order = {}
        self.max_sort_index = -1

        self.active_user_modules = []
        self.pre_start_modules_data = {}

        self.pending_events = []

        # initialize the resource handler
        # ResourceHandler.init(self.panda_app.showbase)

        self.save_file = ""

    def start(self):
        self.create_default_project(DEFAULT_PROJECT_PATH)

    def update(self):
        """this method will be called ever frame in editor_state and play_state"""
        pass

    def create_default_project(self, proj_path):
        wx_main = object_manager.get("WxMain")
        file_browser = object_manager.get("ProjectBrowser")

        if os.path.exists(proj_path) and os.path.isdir(proj_path):
            self.create_new_project(proj_path)

            file_browser.build_tree(proj_path)
            file_browser.Refresh()

            DirectoryEventHandler.on_directory_event()

            wx_main.SetTitle("PandaEditor (Default Project)")

    def create_new_project(self, path):
        if self.user_modules_running is True:
            self.stop_user_modules()

        res = self.project.set_project(path)
        if res is True:
            self.project_set = True
            self.create_new_scene()
            return True
        return False

    def load_project(self):
        pass

    # ------------------------------- various scene operations -----------------------------#
    def create_new_scene(self):
        self.clean_scene()

        # holds all geometry procedurally generated or loaded
        # at run time, it is cleaned on exit from game-mode
        self.runtime_np_parent = NodePath("GameRender")
        self.runtime_np_parent.reparent_to(self.panda_app.showbase.render)

        self.scene_render = NodePath("LevelEditorRender")
        self.scene_render.reparent_to(self.panda_app.showbase.render)

        self.player_camera = self.add_camera()
        self.panda_app.showbase.set_player_camera(self.player_camera)
        self.setup_default_scene()

    def setup_default_scene(self):
        light = self.add_light("DirectionalLight")
        light.setPos(400, 200, 350)
        light.setHpr(Vec3(115, -25, 0))
        light.set_color(Vec4(255, 250, 140, 255))

        self.player_camera.setPos(-220, 280, 80)
        self.player_camera.setHpr(Vec3(218, 0, 0))

        obj = self.add_object(CUBE_PATH)
        obj.setScale(0.5)
        obj.setHpr(90, 90, 0)

        self.toggle_scene_lights()
        obs.trigger("ToggleSceneLights", True)

    def clean_scene(self):
        # clear scene lights
        self.panda_app.showbase.render.clearLight()
        self.scene_lights.clear()
        self.scene_lights_on = False
        obs.trigger("ToggleSceneLights", False)

        # clear scene cameras
        self.scene_cameras.clear()

        self.panda_app.selection.deselect_all()
        self.panda_app.update_gizmo()

        for np in self.panda_app.showbase.render.get_children():
            if type(np) == NodePath:
                if np.hasPythonTag(TAG_PICKABLE):
                    np.getPythonTag(TAG_PICKABLE).on_remove()
                np.remove_node()

        self.player_camera = None

    def load_scene(self):
        pass

    # ------------------------------- various scene graph operations -----------------------------#
    def create_runtime_scene_graph(self):
        for np in self.scene_render.get_children():
            np.getPythonTag(TAG_PICKABLE).save_data()

    def clean_runtime_scene_modifications(self):
        # clean scene hierarchy from any objects loaded at runtime
        for np in self.runtime_np_parent.get_children():
            if type(np) == NodePath:
                np.getPythonTag(TAG_PICKABLE).on_remove()
                np.remove_node()

        for np in self.scene_render.get_children():
            if type(np) == NodePath:
                np.getPythonTag(TAG_PICKABLE).restore_data()

    # -------------------------------USER MODULES / edTools SECTION-----------------------------#
    def load_all_modules(self, modules_paths):
        if self.get_editor_state() == GAME_STATE:
            print("Caution: editor cannot be reloaded in game_state this reload will be delayed until next "
                  "editor_state !")

            # make sure not to append same function_call twice
            if not self.pending_events.__contains__(self.load_all_modules):
                self.pending_events.append(self.load_all_modules)
            return

        # save currently loaded module's data, this data will be reloaded
        # as soon as new modules are loaded
        self.user_modules_data.clear()
        for key in self.user_modules.keys():
            mod = self.user_modules[key]
            mod.ignoreAll()
            self.save_module_properties(mod, data_obj=self.user_modules_data)

        # unregister loaded editor tools as well
        self.unregister_editor_tools()

        # clear out already loaded user modules and editor tools & load new ones
        self.user_modules.clear()
        self.mod_exec_order.clear()
        self.ed_tools.clear()

        # temporarily save editor tools here, to later register them all at once, at the end
        # of this function
        ed_tools = []

        imported_modules = []

        # ---------------import python modules ------------------ #
        def import_modules():
            for path in modules_paths:
                file = path.split("/")[-1]
                # path = _path
                # print("LOADED \n FILE--> {0} \n PATH {1} \n".format(file, path))

                mod_name = file.split(".")[0]
                cls_name_ = mod_name[0].upper() + mod_name[1:]

                # load the module
                spec = importlib.util.spec_from_file_location(mod_name, path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)

                imported_modules.append((module, cls_name_))

            return imported_modules
        # ---------------------------------------------------------------------

        result = try_execute(import_modules)

        if result:
            print("modules imported successfully...!")
        else:
            print("error while importing modules...!")
            return

        for mod, cls_name in imported_modules:
            if hasattr(mod, cls_name):
                cls = getattr(mod, cls_name)
                obj_type = None

                try:
                    obj_type = cls.__mro__[1]
                except AttributeError:
                    pass

                # make sure to load only PModBase and PToolBase object types
                if obj_type == pModBase.PModBase or obj_type == pToolBase.PToolBase:
                    pass
                else:
                    continue

                # instantiate the class and catch any error, mainly from its init method
                # cls_instance = None
                try:
                    cls_instance = cls(cls_name, self,
                                       mouseWatcherNode=self.panda_app.showbase.ed_mouse_watcher_node,
                                       render=self.panda_app.showbase.render,
                                       win=self.panda_app.showbase.ed_win)
                except Exception as e:
                    print("unable to instantiate module {0}".format(cls_name))
                    cls_instance = None
                    tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
                    for x in tb_str:
                        print(x)

                # if there is an error return
                if cls_instance is None:
                    print("error while loading modules...!")
                    self.user_modules.clear()
                    self.ed_tools.clear()
                    self.mod_exec_order.clear()
                    break

                if obj_type == pModBase.PModBase or obj_type == pToolBase.PToolBase:
                    # try restore mod data
                    self.restore_module_settings(cls_instance, data_object=self.user_modules_data)
                    # and append it to user_modules list
                    self.user_modules[cls_instance.get_name()] = cls_instance

                if obj_type == pModBase.PModBase:
                    # also save modules name according to its sort order
                    _sort = cls_instance.get_sort()
                    if _sort not in self.mod_exec_order.keys():
                        self.mod_exec_order[_sort] = []

                    self.mod_exec_order[_sort].append(cls_instance)

                elif obj_type == pToolBase.PToolBase:
                    ed_tools.append(cls_instance)

        # finally, register editor tools
        self.register_editor_tools(ed_tools)

        obs.trigger("UpdatePropertiesPanel")
        return True

    def register_editor_tools(self, tools):
        # register tools
        for tool in tools:
            tool.enable()
            self.ed_tools[tool.get_name()] = tool  # save the tool into editor_tools repository

    def unregister_editor_tools(self):
        for key in self.ed_tools.keys():
            self.ed_tools[key].Stop()
        self.ed_tools.clear()

    @staticmethod
    def save_module_properties(module, obj_data=None, data_obj=None):
        if obj_data is None:
            obj_data = ObjectData(module.get_name())

        # get all attributes of module and add them to object data
        for name, val in module.get_savable_atts():
            # if type(val) is list, copy individual elements separately
            if type(val) is list:
                x = []
                x.extend(val)
                val = x

            prop = Property(name, val)
            obj_data.add_property(prop)

        data_obj[module.get_name()] = obj_data

        if module.are_sub_objects_valid():
            x = module.get_sub_objects()
            for obj in x:
                LevelEditor.save_module_properties(module=obj, obj_data=None, data_obj=data_obj)

        return obj_data

    @staticmethod
    def restore_module_settings(module, data_object=None, parent_module=None):
        if parent_module is None:
            parent_module = module

        if not data_object.__contains__(module.get_name()):
            # print("unable to restore object data", module.get_name(), "does not exist !")
            return

        obj_data = data_object[module.get_name()]
        properties = obj_data.properties

        for name, val in properties:
            attr = module.get_attr(name)

            if attr is not None and type(attr) == type(val):
                setattr(module, name, val)

        if module.are_sub_objects_valid():
            for obj in module.get_sub_objects():
                LevelEditor.restore_module_settings(obj, data_object, parent_module)

        return module

    # ----------------------------- level editor section ----------------------------- #
    def switch_state(self, state):
        if self.project_set is False:
            print("project not set")
            return False

        # make sure argument state is a valid state
        if state not in (0, 1):
            print("unknown editor state: {0}".format(state))
            return

        if state == GAME_STATE:
            self.enable_game_state()

        elif state == EDITOR_STATE:
            self.enable_editor_state()

        else:
            print("undefined editor state {0}".format(state))

    def enable_editor_state(self):
        print("editor state enabled")
        self.ed_state = EDITOR_STATE
        self.stop_user_modules()
        self.panda_app.bind_key_events()

        # switch camera
        self.panda_app.showbase.set_ed_dr_camera(self.panda_app.showbase.ed_camera)

        # call pending events
        for function_call in self.pending_events:
            function_call()

        self.pending_events.clear()

    def enable_game_state(self):
        print("game state enabled")

        # start by clearing pending events list
        self.pending_events.clear()

        # switch camera
        self.panda_app.showbase.set_ed_dr_camera(self.player_camera)

        self.ed_state = GAME_STATE
        self.panda_app.unbind_key_events()
        self.panda_app.set_active_gizmo(None)
        self.start_user_modules()

    def start_user_modules(self):
        # create runtime scene graph
        self.create_runtime_scene_graph()
        self.pre_start_modules_data.clear()

        def _start(j):
            for mod in self.mod_exec_order[j]:
                if not mod.is_enabled():
                    print(mod.get_name(), "is disabled")
                    return

                # save this module's data in pre_start_user_modules, this
                # data will be reloaded as soon as user exits from game mode
                self.save_module_properties(mod, data_obj=self.pre_start_modules_data)

                # start module's update
                _res = mod.Start(late_update_sort=late_update_sort)
                if _res is False:
                    return

                # append to active runtime user modules
                self.active_user_modules.append(mod)

            return True

        '''Philosophy of module sort order in PandaEditor'''
        ''''''

        if len(self.mod_exec_order) == 0:
            return

        # copy modules execution order keys to a list, you will get a list of ints representing all
        # sort order
        lst = [*self.mod_exec_order.keys()]

        # sort the sort order
        lst.sort()

        # self-explanatory
        start = lst[0]
        stop = lst[len(lst) - 1]

        # late updates are executed after all updates have been executed,
        # the sort order of all updates set in a way, that messenger executes them after updates
        late_update_sort = stop + 1

        for i in range(start, stop + 1):
            res = _start(i)
            if res is False:
                break
            late_update_sort += 1

    def stop_user_modules(self):
        for mod in self.active_user_modules:
            mod.Stop()

            # restore runtime values
            if self.pre_start_modules_data.__contains__(mod.get_name()):
                self.restore_module_settings(mod, data_object=self.pre_start_modules_data)

        self.pre_start_modules_data.clear()
        self.active_user_modules.clear()
        self.clean_runtime_scene_modifications()

        # update ui data
        obs.trigger("XFormTask")

    LIGHT_MAP = {"PointLight": (PointLight, EdPointLight, POINT_LIGHT_MODEL),
                 "Spotlight": (Spotlight, EdSpotLight, SPOT_LIGHT_MODEL),
                 "DirectionalLight": (DirectionalLight, EdDirectionalLight, DIR_LIGHT_MODEL)}

    NODE_TYPE_MAP = {"ModelNp": ModelNp,
                     "DirectionalLight": EdDirectionalLight,
                     "PointLight": EdPointLight,
                     "SpotLight": EdSpotLight,
                     "EdCameraNp": EdCameraNp}

    def load_model(self, path, geo=RUN_TIME_GEO, reparent_to_render=True):

        if self.user_modules_running and geo is not RUN_TIME_GEO:
            print("only -RUN_TIME_GEO- can be loaded at game mode !")
            return

        def create_python_object(_np, tag):
            if type(_np) == NodePath:
                xx = ModelNp(_np, uid="ModelNp")

            children = _np.getChildren()
            if len(children) > 0:
                for child in children:
                    create_python_object(child, tag)

        # TO:DO **INSERT A TRY EXECUTE HERE** #
        # TO:DO **REPLACE showbase.loader with a new loader instance** #

        np = self.panda_app.showbase.loader.loadModel(path)
        np = ModelNp(np, uid="ModelNp")
        np.setPythonTag(TAG_PICKABLE, np)
        create_python_object(np, TAG_PICKABLE)

        # set a default model colour
        np.setColor(1, 1, 1, 1)

        # setup a default material
        mat = Material()
        mat.setDiffuse((1, 1, 1, 1))
        np.setMaterial(mat)

        # parent only if asked to do so !
        if geo == EDITOR_GEO and reparent_to_render:
            np.reparent_to(self.panda_app.showbase.edRender)

        elif geo == RUN_TIME_GEO and reparent_to_render:
            np.reparent_to(self.runtime_np_parent)

        elif geo == SCENE_GEO and reparent_to_render:
            np.reparent_to(self.scene_render)

        elif geo == GEO_NO_PARENT:
            pass

        elif reparent_to_render:
            np.remove_node()
            print("unable to add model")
            return False

        return np

    def add_camera(self, *args):
        if len(self.scene_cameras) > 0:
            return

        # Create lens
        lens = PerspectiveLens()
        lens.set_fov(60)
        lens.setAspectRatio(800 / 600)

        # Create camera
        cam_np = NodePath(Camera("Camera"))
        cam_np.node().setLens(lens)
        cam_np.node().setCameraMask(GAME_GEO_MASK)

        # wrap it into a editor camera
        cam_np = EdCameraNp(cam_np, self, uid="EdCameraNp")
        cam_np.setPythonTag(TAG_PICKABLE, cam_np)
        cam_np.reparent_to(self.scene_render)

        # create a handle
        cam_handle = self.panda_app.showbase.loader.loadModel(CAMERA_MODEL)
        cam_handle.setLightOff()
        cam_handle.show(ED_GEO_MASK)
        cam_handle.hide(GAME_GEO_MASK)

        # re-parent handle to cam_np
        cam_handle.reparent_to(cam_np)
        cam_handle.setScale(2.25)
        cam_np.start_update()

        self.scene_cameras.append(cam_np)

        return cam_np

    def add_object(self, path):
        np = self.panda_app.showbase.loader.loadModel(path, noCache=True)
        np = ModelNp(np, self, uid="ModelNp")
        np.setPythonTag(TAG_PICKABLE, np)
        np.reparent_to(self.scene_render)
        np.setHpr(Vec3(0, 90, 0))
        np.setColor(1, 1, 1, 1)
        mat = Material()
        mat.setDiffuse((1, 1, 1, 1))
        np.setMaterial(mat)

        # turn on per pixel lightning
        # np.setShaderAuto()
        return np

    def add_light(self, light):
        if self.LIGHT_MAP.__contains__(light):

            x = self.LIGHT_MAP[light]

            light_node = x[0](light)
            ed_handle = x[1]
            model = x[2]

            light_np = NodePath("light")
            light_np = light_np.attachNewNode(light_node)

            model = self.panda_app.showbase.loader.loadModel(model)
            handle = ed_handle(light_np, self, uid=light)

            handle.setPythonTag(TAG_PICKABLE, handle)
            handle.start_update()
            handle.setLightOff()
            handle.show(ED_GEO_MASK)
            handle.hide(GAME_GEO_MASK)

            if self.ed_state == GAME_STATE:
                handle.reparent_to(self.runtime_np_parent)
            else:
                handle.reparent_to(self.scene_render)

            if self.scene_lights_on:
                self.panda_app.showbase.render.setLight(handle)

            self.scene_lights.append(handle)
            model.reparentTo(handle)

            return handle

    def duplicate_object(self, selections=None, select=True, *args):
        if selections is None:
            selections = []

        if len(selections) is 0:
            selections = self.panda_app.selection.get_selections()

        new_selections = []

        for np in selections:
            uid = np.get_uid()

            if uid in self.NODE_TYPE_MAP.keys():

                x = np.copyTo(self.scene_render)
                # for some reason np.copy does not duplicate PYTHON TAG as well
                # so clear existing PY TAG and recreate object according to its type e.g.
                # light, model, camera, actor etc
                x.clearPythonTag(TAG_PICKABLE)
                x = self.NODE_TYPE_MAP[uid](x, self, uid=uid)
                x.setPythonTag(TAG_PICKABLE, x)

                # TO:DO copy object's editor data

                if uid in ["PointLight", "DirectionalLight", "SpotLight"]:
                    if self.scene_lights_on:
                        self.panda_app.showbase.render.setLight(x)
                    self.scene_lights.append(x)

                new_selections.append(x)

        if select:
            self.panda_app.selection.deselect_all()
            self.panda_app.selection.set_selected(new_selections)
            self.panda_app.update_gizmo()
            obs.trigger("NodepathSelected", new_selections)

        return new_selections

    def remove_nodepaths(self, nodepaths=[]):
        pass

    def on_remove(self, *args, **kwargs):
        if len(self.panda_app.selection.selected_nps) > 0:
            obs.trigger("RemoveNodePath")

    def remove_selected_nps(self, selections=None):
        if selections is None:
            selections = self.panda_app.selection.get_selections()

        for x in selections:
            x.hideBounds()

            # for the time being, cannot remove camera
            if x.uid == "EdCameraNp":
                continue

            x.on_remove()
            x.clearPythonTag(TAG_PICKABLE)
            x.remove_node()

        self.panda_app.selection.get_selections().clear()
        self.panda_app.update_gizmo()

    def toggle_scene_lights(self):
        """inverts scene_light_on status and returns inverted value"""

        if self.scene_lights_on:
            self.scene_lights_on = False
            self.panda_app.showbase.render.setLightOff()

        elif not self.scene_lights_on:
            for light in self.scene_lights:
                self.panda_app.showbase.render.setLight(light)
            self.scene_lights_on = True

        return self.scene_lights_on

    def set_main_camera(self):
        pass

    def get_save_data(self):
        pass

    # ------------------- public methods of level editor ------------------- #

    def get_editor_state(self):
        return self.ed_state

    def get_player_camera(self):
        return self.player_camera

    def get_ed_camera(self):
        return self.panda_app.showbase.ed_camera

    def get_render(self):
        return self.panda_app.showbase.render

    def get_mod_instance(self, mod_name):
        # TO:DO need an exception handler here
        mod_name = mod_name[0].upper() + mod_name[1:]
        if self.user_modules.__contains__(mod_name):
            return self.user_modules[mod_name]
        return None

    def get_user_mods(self):
        return self.user_modules

    def get_scene_lights(self):
        return self.scene_lights
