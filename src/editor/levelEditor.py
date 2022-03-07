import os
import sys
import importlib
import traceback
import panda3d.core as p3d_core
import editor.core as ed_core

from editor.project import Project
from editor.constants import *
from editor.nodes import EdPointLight, EdSpotLight, EdDirectionalLight, ModelNp, EdCameraNp


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

        self.scene_lights = []  # all scene lights in one repository
        self.scene_cameras = []  # all scene camera in one repository

        self.ed_plugins = {}
        self.__user_modules = {}

        self.pending_events = []

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

            file_browser.create_or_rebuild_tree(proj_path, rebuild_event=False)
            file_browser.Refresh()

            wx_main.SetTitle("PandaEditor (Default Project)")

            self.load_all_mods(file_browser.resources["py"])

    def create_new_project(self, path):
        if self.ed_state == GAME_STATE:
            self.switch_state(EDITOR_STATE)

        res = self.project.set_project(path)
        if res is True:
            self.__user_modules.clear()
            self.ed_plugins.clear()

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
        self.runtime_np_parent = p3d_core.NodePath("GameRender")
        self.runtime_np_parent.reparent_to(self.panda_app.showbase.render)

        self.scene_render = p3d_core.NodePath("LevelEditorRender")
        self.scene_render.reparent_to(self.panda_app.showbase.render)

        self.player_camera = self.add_camera()
        self.panda_app.showbase.set_player_camera(self.player_camera)
        self.setup_default_scene()

    def setup_default_scene(self):
        light = self.add_light("DirectionalLight")
        light.setPos(400, 200, 350)
        light.setHpr(p3d_core.Vec3(115, -25, 0))
        light.set_color(p3d_core.Vec4(255, 250, 140, 255))

        self.player_camera.setPos(-220, 280, 80)
        self.player_camera.setHpr(p3d_core.Vec3(218, 0, 0))

        self.panda_app.showbase.ed_camera.reset()

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
            if type(np) == p3d_core.NodePath:
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
            if type(np) == p3d_core.NodePath:
                np.getPythonTag(TAG_PICKABLE).on_remove()
                np.remove_node()

        for np in self.scene_render.get_children():
            if type(np) == p3d_core.NodePath:
                np.getPythonTag(TAG_PICKABLE).restore_data()

    # -------------------------------USER MODULES / edTools SECTION-----------------------------#
    def load_all_mods(self, modules_paths):
        if self.ed_state == GAME_STATE:
            print("LevelEditor --> Caution..! editor cannot be reloaded in game_state this reload will be delayed "
                  "until next editor_state.")

            # make sure not to append same function_call twice
            if not self.pending_events.__contains__(self.load_all_mods):
                self.pending_events.append(self.load_all_mods)
            return

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

        if len(modules_paths) == 0:
            return True

        result = try_execute_1(import_modules)

        if result:
            print("LevelEditor --> Modules imported successfully.")
        else:
            print("LevelEditor --> Error while importing modules.")
            return False

        for key in self.__user_modules:
            mod = self.__user_modules[key]
            mod.save_data()

        # temporarily save editor tools here, to later register them all at once, at the end
        # of this function
        ed_plugins = []
        self.unregister_editor_plugins()

        new_modules = []

        for mod, cls_name in imported_modules:
            if hasattr(mod, cls_name):
                cls = getattr(mod, cls_name)
                obj_type = None

                try:
                    obj_type = cls.__mro__[1]
                except AttributeError:
                    pass

                # make sure to load only PModBase and PToolBase object types
                if obj_type == ed_core.pModBase.PModBase:
                    pass
                else:
                    continue

                # instantiate the class and catch any errors from its init method
                try:
                    cls_instance = cls(
                        name=cls_name,
                        level_editor=self,
                        render=self.panda_app.showbase.render,
                        render_2d=self.panda_app.showbase.render2d,
                        mouse_watcher_node=self.panda_app.showbase.ed_mouse_watcher_node,
                        win=self.panda_app.showbase.ed_win)

                except Exception as e:
                    print("LevelEditor --> Unable to instantiate module {0}".format(cls_name))
                    cls_instance = None
                    tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
                    for x in tb_str:
                        print(x)

                # if there is an error return
                if cls_instance is None:
                    if self.__user_modules.__contains__(cls_name):
                        self.__user_modules[cls_name].class_instance._error = True
                    continue

                saved_data = None
                if self.__user_modules.__contains__(cls_name):
                    saved_data = self.__user_modules[cls_name].saved_data

                self.__user_modules[cls_name] = ed_core.UserModule(cls_instance,
                                                                   cls_instance._sort)

                if saved_data is not None:
                    self.__user_modules[cls_name].saved_data = saved_data
                    self.__user_modules[cls_name].reload_data()
                else:
                    self.__user_modules[cls_name].save_data()

                if self.__user_modules[cls_name].class_instance._editor_plugin:
                    ed_plugins.append(self.__user_modules[cls_name].class_instance)
                    self.__user_modules[cls_name].class_instance._sort = 2

                new_modules.append(cls_name)

        # finally, register editor tools
        self.register_editor_plugins(ed_plugins)

        # ------------------------------------
        # remove any previously loaded modules
        to_be_removed = []
        for cls_name in self.__user_modules.keys():
            if cls_name not in new_modules:
                to_be_removed.append(cls_name)
        for cls_name in to_be_removed:
            del self.__user_modules[cls_name]
            print("LevelEditor --> Unloaded user modules {0}.".format(cls_name))
        # ---------------------------------------------------------------------

        print("LevelEditor --> Modules loaded successfully.")
        obs.trigger("UpdatePropertiesPanel")

        return True

    def register_editor_plugins(self, plugins):
        # start plugins
        for plugin in plugins:
            plugin.start(1)
            self.ed_plugins[plugin._name] = plugin  # save the tool into editor_tools repository

    def unregister_editor_plugins(self):
        for key in self.ed_plugins.keys():
            self.ed_plugins[key].stop()
        self.ed_plugins.clear()

    # ----------------------------- level editor section ----------------------------- #
    def switch_state(self, state):
        if state == GAME_STATE:
            self.enable_game_state()

        elif state == EDITOR_STATE:
            self.enable_editor_state()

        else:
            print("LevelEditor --> Undefined editor state {0}".format(state))

    def enable_editor_state(self):
        print("LevelEditor --> Editor state enabled.")
        self.ed_state = EDITOR_STATE
        self.stop_user_modules()
        self.clean_runtime_scene_modifications()

        # update ui data
        obs.trigger("XFormTask")

        self.panda_app.bind_key_events()

        # switch camera
        self.panda_app.showbase.set_ed_dr_camera(self.panda_app.showbase.ed_camera)

        # call pending events
        for function_call in self.pending_events:
            function_call()

        self.pending_events.clear()

    def enable_game_state(self):
        print("LevelEditor --> Game state enabled.")

        # start by clearing pending events list
        self.pending_events.clear()

        # switch camera
        self.panda_app.showbase.set_ed_dr_camera(self.player_camera)

        self.ed_state = GAME_STATE
        self.panda_app.unbind_key_events()
        self.panda_app.set_active_gizmo(None)

        # create runtime scene graph
        self.create_runtime_scene_graph()

        self.start_user_modules()

    def start_user_modules(self):
        mod_exec_order = {}
        for key in self.__user_modules:
            mod = self.__user_modules[key]

            if mod.class_instance._editor_plugin:
                continue

            sort_value = mod.class_instance._sort

            if mod_exec_order.__contains__(sort_value):
                mod_exec_order[sort_value].append(mod)
            else:
                mod_exec_order[sort_value] = []
                mod_exec_order[sort_value].append(mod)

        def _start(j):
            for _mod in mod_exec_order[j]:

                cls_instance = _mod.class_instance

                if not cls_instance._enabled:
                    # print(cls_instance.get_name(), "is disabled")
                    return

                _mod.save_data()

                # start module's update
                _res = cls_instance.start(late_update_sort=late_update_sort)
                if _res is False:
                    return

            return True

        # copy modules execution order keys to a list, you will get a list of ints representing all
        # sort order
        lst = [*mod_exec_order.keys()]

        if len(lst) == 0:
            return

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
        for key in self.__user_modules:
            mod = self.__user_modules[key]

            if mod.class_instance._editor_plugin:
                continue

            mod.class_instance.stop()
            mod.reload_data()

    LIGHT_MAP = {"PointLight": (p3d_core.PointLight, EdPointLight, POINT_LIGHT_MODEL),
                 "Spotlight": (p3d_core.Spotlight, EdSpotLight, SPOT_LIGHT_MODEL),
                 "DirectionalLight": (p3d_core.DirectionalLight, EdDirectionalLight, DIR_LIGHT_MODEL)}

    NODE_TYPE_MAP = {"ModelNp": ModelNp,
                     "DirectionalLight": EdDirectionalLight,
                     "PointLight": EdPointLight,
                     "SpotLight": EdSpotLight,
                     "EdCameraNp": EdCameraNp}

    def load_model(self, path, geo=SCENE_GEO, reparent_to_render=True):
        # TO:DO **INSERT A TRY EXECUTE HERE** #
        # TO:DO **REPLACE showbase.loader with a new loader instance** #

        np = self.panda_app.showbase.loader.loadModel(path)
        np = ModelNp(np, uid="ModelNp")
        # np.setPythonTag(TAG_PICKABLE, self)

        # set a default model colour
        np.setColor(1, 1, 1, 1)

        # setup a default material
        mat = p3d_core.Material()
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
            print("LevelEditor --> Unable to load 3d model.")
            return False

        return np

    def add_camera(self, *args):
        if len(self.scene_cameras) > 0:
            return

        # Create lens
        lens = p3d_core.PerspectiveLens()
        lens.set_fov(60)
        lens.setAspectRatio(800 / 600)

        # Create camera
        cam_np = p3d_core.NodePath(p3d_core.Camera("Camera"))
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
        np.setHpr(p3d_core.Vec3(0, 90, 0))
        np.setColor(1, 1, 1, 1)
        mat = p3d_core.Material()
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

            light_np = p3d_core.NodePath("light")
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
            selections = self.panda_app.selection.selected_nps

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

    def on_remove(self, *args, **kwargs):
        if len(self.panda_app.selection.selected_nps) > 0:
            obs.trigger("RemoveNodePath")

    def remove_selected_nps(self, selections=None):
        if selections is None:
            selections = self.panda_app.selection.selected_nps

        for x in selections:
            x.hideBounds()

            # for the time being, cannot remove camera
            if x.uid == "EdCameraNp":
                continue

            x.on_remove()
            x.clearPythonTag(TAG_PICKABLE)
            x.remove_node()

        self.panda_app.selection.selected_nps.clear()
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

        self.panda_app.gizmo_mgr_root_np.setLightOff()
        return self.scene_lights_on

    def get_save_data(self):
        pass

    def get_mod_instance(self, class_name):
        """returns a user module, by class_name, modules with an error will not be found"""

        if self.__user_modules.__contains__(class_name):
            if not self.__user_modules[class_name].class_instance._error:
                return self.__user_modules[class_name].class_instance

        return None
