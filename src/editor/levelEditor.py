from panda3d.core import NodePath, Material, DirectionalLight, PointLight
from panda3d.core import Spotlight, Camera, Vec3, Vec4, BitMask32
from editor.p3d import pModBase, pToolBase
from editor.project import Project
from editor.constants import *
from editor.onSceneUI import OnSceneUI
from editor.nodes import EdPointLight, EdSpotLight, EdDirectionalLight, ModelNp, EdCameraNp
from editor.utils import Math
from editor.utilities import Property, ObjectData, euler_from_hpr
from editor.assetsHandler import AssetsHandler as ResourceHandler
from editor.utils.exceptionHandler import try_execute


EDITOR_STATE = 0  # editor mode
GAME_STATE = 1  # play mode


class LevelEditor:
    def __init__(self, panda_app, *args, **kwargs):
        object_manager.add_object("LevelEditor", self)

        self.panda_app = panda_app

        self.project = Project(self)
        self.project_set = False

        self.ed_state = EDITOR_STATE

        self.runtime_np_parent = None
        self.level_editor_render = None

        self.__main_camera__ = None

        self.scene_lights = []
        self.scene_lights_on = False

        # gizmos, grid, selection
        self.active_gizmo = None
        self.gizmos_active = False

        self.user_modules_running = False
        self.selected_module = False

        self.ed_tools = {}
        self.user_modules = {}
        self.user_modules_data = {}
        self.mod_exec_order = {}
        self.max_sort_index = -1

        self.active_user_modules = []
        self.pre_start_modules_data = {}

        self.pending_events = []

        # initialize the resource handler
        ResourceHandler.init(self.panda_app.showbase)

        self.save_file = ""

    '''this method will be called ever frame in editor_state and play_state'''
    def update(self):
        pass

    # self.on_scene_ui = OnSceneUI(self, rootP2d=self.panda_app.showbase.edPixel2d)
    # -------------------------------PROJECT SECTION-----------------------------#
    def setup_project(self, path):
        if self.user_modules_running is True:
            self.stop_user_modules()

        # self.panda_app.reset()
        self.start_new_scene()

        res = self.project.set_project(path)
        if res is True:
            success = self.load_all_modules()
            if success:
                self.project_set = True
                return True
        return False

    def open_project(*args):
        pass

    def start_new_scene(self):
        print("new scene")
        self.clean_scene()

        # holds all geometry procedurally generated or loaded
        # at run time, it is cleaned on exit from gamemode
        self.runtime_np_parent = NodePath("GameRender")
        self.runtime_np_parent.reparent_to(self.panda_app.showbase.render)

        self.level_editor_render = NodePath("LevelEditorRender")
        self.level_editor_render.reparent_to(self.panda_app.showbase.render)

        self.__main_camera__ = self.add_camera()
        self.setup_default_scene()

    def setup_default_scene(self):
        light = self.add_light("DirectionalLight")
        light.setPos(400, 200, 350)
        light.setHpr(Math.hpr_from_euler(Vec3(-25, 0, 150)))
        light.set_color(Vec4(255, 250, 140, 255))

        self.__main_camera__.setPos(-220, 280, 80)
        self.__main_camera__.setHpr(Math.hpr_from_euler(Vec3(0, 0, -140)))

        obj = self.add_object(CUBE_PATH)
        obj.setScale(0.5)

        obs.trigger("ToggleSceneLights", True)

    def clean_scene(self):
        self.panda_app.showbase.render.clearLight()
        self.scene_lights.clear()
        self.scene_lights_on = False

        for np in self.panda_app.showbase.render.get_children():
            if type(np) == NodePath:
                if np.hasPythonTag(TAG_PICKABLE):
                    np.getPythonTag(TAG_PICKABLE).on_remove()
                np.remove_node()

        self.__main_camera__ = None

    # -------------------------------USER MODULES / edTools SECTION-----------------------------#
    def load_all_modules(self):
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

        modules = ResourceHandler.USER_MODULES

        for mod, cls_name in modules:
            if hasattr(mod, cls_name):
                cls = getattr(mod, cls_name)
                obj_type = cls.__mro__[1]

                # make sure to load only PModBase and PToolBase object types
                if obj_type == pModBase.PModBase or obj_type == pToolBase.PToolBase:
                    pass
                else:
                    continue

                # *************************TO:DO ERROR HANDLER************************ #
                cls_instance = cls(cls_name, self,
                                   mouseWatcherNode=self.panda_app.showbase.edMouseWatcherNode,
                                   render=self.runtime_np_parent,
                                   win=self.panda_app.showbase.ed_win)

                if obj_type == pModBase.PModBase or obj_type == pToolBase.PToolBase:
                    # try restore mod data
                    self.restore_module_settings(cls_instance, data_object=self.user_modules_data)
                    # and append it to user_modules list
                    self.user_modules[cls_instance.get_name()] = cls_instance

                if obj_type == pModBase.PModBase:

                    # also save modules name according to it's sort order 
                    _sort = cls_instance.get_sort()
                    if _sort not in self.mod_exec_order.keys():
                        self.mod_exec_order[_sort] = []

                    self.mod_exec_order[_sort].append(cls_instance)

                    obs.trigger("OnModuleLoaded", cls_instance)

                elif obj_type == pToolBase.PToolBase:
                    ed_tools.append(cls_instance)

        # finally register editor tools
        self.register_editor_tools(ed_tools)

        obs.trigger("UpdatePropertiesPanel")
        print("user modules loaded successfully")
        return True

    def register_editor_tools(self, tools):
        def register(tool):
            """registers an editor tool,
            registering an editor tool involves calling tool's enable method,
            adding it's unique tab if requested & adding it to level_editor.ed_tools
            repository"""
            tool.enable()

            if tool.has_tab_request() and tool.get_tab_request() not in unique_tab_paths:
                unique_tab = tool.get_tab_request()
                unique_tab_paths.append(unique_tab)
                unique_tabs.append(unique_tab[0].split("/")[-1])
                obs.trigger("RegisterUserTab", unique_tab, tool)
            else:
                pass

            self.ed_tools[tool.get_name()] = tool  # save the tool into editor_tools repository

        unique_tabs = []  # name of the requested unique tabs by editor tools
        unique_tab_paths = []  # names of the the full menu paths of requested unique tabs by ed tools

        # register tools
        for tool in tools:
            register(tool)

        # now refresh user created tabs 
        obs.trigger("RefreshUserTabs", unique_tabs)

    def unregister_editor_tools(self):
        for key in self.ed_tools.keys():
            self.ed_tools[key].Stop()
        obs.trigger("UnregisterEdTools")
        self.ed_tools.clear()

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

        # call pending events
        for function_call in self.pending_events:
            function_call()

        self.pending_events.clear()

    def enable_game_state(self):
        print("game state enabled")

        # start by clearing pending events list
        self.pending_events.clear()

        self.ed_state = GAME_STATE
        self.panda_app.unbind_key_events()
        self.panda_app.set_active_gizmo(None)
        self.start_user_modules()

    def start_user_modules(self):
        # create runtime scene graph
        self.create_runtime_scene_graph()
        self.pre_start_modules_data.clear()

        def _start(i):
            for mod in self.mod_exec_order[i]:
                if not mod.is_enabled():
                    print(mod.get_name(), "is disabled")
                    return

                # save this module's data in pre_start_user_modules, this
                # data will be reloaded as soon as user exits from game mode
                self.save_module_properties(mod, data_obj=self.pre_start_modules_data)

                # start module's update
                res = mod.Start()
                if res is False:
                    return

                # start module's late update
                mod.StartLateUpdateTask(sort=late_update_sort)

                # append to active modules
                self.active_user_modules.append(mod)

            return True

        lst = [*self.mod_exec_order.keys()]
        lst.sort()
        start = lst[0]
        stop = lst[len(lst) - 1]

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
            print("unable to restore object data", module.get_name(), "does not exist !")
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

    def create_runtime_scene_graph(self):
        for np in self.level_editor_render.get_children():
            np.getPythonTag(TAG_PICKABLE).save_data()

    def clean_runtime_scene_modifications(self):
        # clean scene hierarchy from any objects loaded at runtime
        for np in self.runtime_np_parent.get_children():
            if type(np) == NodePath:
                np.getPythonTag(TAG_PICKABLE).on_remove()
                np.remove_node()

        for np in self.level_editor_render.get_children():
            if type(np) == NodePath:
                np.getPythonTag(TAG_PICKABLE).restore_data()

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

        # reparent only if asked to do so !
        if geo == EDITOR_GEO and reparent_to_render:
            np.reparent_to(self.panda_app.showbase.edRender)

        elif geo == RUN_TIME_GEO and reparent_to_render:
            # create_python_object(np, TAG_PICKABLE)
            np.reparent_to(self.runtime_np_parent)

        elif geo == SCENE_GEO and reparent_to_render:
            # create_python_object(np, TAG_PICKABLE)
            np.reparent_to(self.level_editor_render)

        elif geo == GEO_NO_PARENT:
            pass

        elif reparent_to_render:
            np.remove_node()
            print("unable to add model")
            return False

        return np

    def find(self, model):
        np = self.level_editor_render.find(model)
        if np is not None:
            return np
        return None

    def set_main_camera(self):
        pass

    def add_camera(self, *args):
        # Create camera
        cam_np = NodePath(Camera("Camera"))

        # wrap it into a editor camera
        cam_np = EdCameraNp(cam_np, self, uid="EdCameraNp")
        cam_np.setPythonTag(TAG_PICKABLE, cam_np)
        cam_np.reparent_to(self.level_editor_render)

        # create a handle
        cam_handle = self.panda_app.showbase.loader.loadModel(CAMERA_MODEL)
        cam_handle.setLightOff()
        cam_handle.show(BitMask32(0))
        cam_handle.hide(BitMask32(1))

        # re-parent handle to cam_np
        cam_handle.reparent_to(cam_np)
        cam_handle.setScale(2.25)
        cam_np.start_update()

        return cam_np

    def add_object(self, path):
        np = self.panda_app.showbase.loader.loadModel(path)
        np = ModelNp(np, self, uid="ModelNp")
        np.setPythonTag(TAG_PICKABLE, np)
        np.reparent_to(self.level_editor_render)
        np.setHpr(Math.hpr_from_euler(Vec3(90, 0, 0)))
        np.setColor(1, 1, 1, 1)
        mat = Material()
        mat.setDiffuse((1, 1, 1, 1))
        np.setMaterial(mat)

        # turn on per pixel lightning
        np.setShaderAuto()
        return np

    LIGHT_MAP = {"PointLight": (PointLight, EdPointLight, POINT_LIGHT_MODEL),
                 "Spotlight": (Spotlight, EdSpotLight, SPOT_LIGHT_MODEL),
                 "DirectionalLight": (DirectionalLight, EdDirectionalLight, DIR_LIGHT_MODEL)}

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
            handle.show(BitMask32(0))
            handle.hide(BitMask32(1))

            if self.ed_state == GAME_STATE:
                handle.reparent_to(self.runtime_np_parent)
            else:
                handle.reparent_to(self.level_editor_render)

            if self.scene_lights_on:
                self.panda_app.showbase.render.setLight(handle)

            self.scene_lights.append(handle)
            model.reparentTo(handle)
            # model.setScale(2.25) point light
            # model.setScale(0.8) point light
            return handle

    NODE_TYPE_MAP = {"ModelNp": ModelNp,
                     "DirectionalLight": EdDirectionalLight,
                     "PointLight": EdPointLight,
                     "SpotLight": EdSpotLight,
                     "EdCameraNp": EdCameraNp}

    def duplicate_object(self, selections=[], select=True, *args):
        if len(selections) is 0:
            selections = self.panda_app.selection.get_selections()

        self.panda_app.selection.deselect_all()

        new_selections = []

        for np in selections:
            uid = np.get_uid()

            if uid in self.NODE_TYPE_MAP.keys():

                x = np.copyTo(self.level_editor_render)
                # for some reason np.copy does not duplicate PYTHON TAG as well
                # so clear existing PY TAG and recreate object according to it's type e.g
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
            self.panda_app.selection.set_selected(new_selections)
            self.panda_app.update_gizmo()
            obs.trigger("NodepathSelected", new_selections)

        return new_selections

    def on_delete(self, *args, **kwargs):
        if len(self.panda_app.selection.selected_nps) > 0:
            obs.trigger("DeleteObject")
            self.panda_app.update_gizmo()

    def delete_selected(self, selections=None):
        selections = self.panda_app.selection.get_selections()

        for x in selections:
            x.hideBounds()
            x.on_remove()
            x.clearPythonTag(TAG_PICKABLE)
            x.remove_node()

        if len(selections) > 0:
            self.panda_app.selection.selected_nps.clear()

    def toggle_scene_lights(self, val=None):
        if self.scene_lights_on:
            self.scene_lights_on = False
            self.panda_app.showbase.render.setLightOff()

        elif not self.scene_lights_on:
            for light in self.scene_lights:
                self.panda_app.showbase.render.setLight(light)
            self.scene_lights_on = True

        return self.scene_lights_on

    def get_editor_state(self):
        return self.ed_state

    def get_main_camera(self):
        return self.__main_camera__

    def get_ed_camera(self):
        return self.panda_app.showbase.ed_camera

    def get_mod_instance(self, mod_name):
        # TO:DO needs an exception handler here
        mod_name = mod_name[0].upper() + mod_name[1:]
        if self.user_modules.__contains__(mod_name):
            return self.user_modules[mod_name]
        return None

    def get_user_mods(self):
        return self.user_modules

    def get_scene_lights(self):
        return self.scene_lights

    def get_save_data(self):
        pass
