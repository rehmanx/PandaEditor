import sys
import importlib

from direct.showbase.Loader import Loader
from editor.utils import try_execute
from editor.constants import object_manager, SCENE_GEO


class AssetsHandler(object):

    USER_MODULES = []
    ASSETS_2D = {}
    ASSETS_3D = {}
    TEXTURES = {}

    __RESOURCES = {}

    __loader__ = None

    @staticmethod
    def init(base):
        AssetsHandler.__loader__ = Loader(base)

    @staticmethod
    def load(modules, textures, models):
        # unload all resources
        AssetsHandler.unload_all()

        # AssetsHandler.load_textures(textures)  # textures
        # AssetsHandler.load_assets_2d(libs) # sprites
        # AssetsHandler.load_assets_3d(models)  # 3d models

        # load user modules
        x = try_execute(AssetsHandler.load_user_modules, modules)
        if x:
            print("user modules loaded successfully !")
            # print(AssetsHandler.USER_MODULES)
            # TO:DO sort modules according to edConfigFile if available
        else:
            print("unable to load user modules !")

    @staticmethod
    def unload_all():
        AssetsHandler.USER_MODULES.clear()
        AssetsHandler.TEXTURES.clear()
        AssetsHandler.ASSETS_3D.clear()

    @staticmethod
    def load_user_modules(modules):
        """loads all user modules from libraries provided as a argument to this method"""

        # ------------------------------
        def _load(_path):
            file = _path.split("/")[-1]
            path = _path
            # print("LOADED \n FILE--> {0} \n PATH {1} \n".format(file, path))

            mod_name = file.split(".")[0]
            cls_name = mod_name[0].upper() + mod_name[1:]

            # load the module
            spec = importlib.util.spec_from_file_location(mod_name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            AssetsHandler.USER_MODULES.append((module, cls_name))
            # ------------------------------

        # and reload
        for module_path in modules:
            _load(module_path)

        # finally return newly loaded modules
        return AssetsHandler.USER_MODULES

    @staticmethod
    def load_assets_2d(libs):
        pass

    @staticmethod
    def load_textures(images):
        for image in images:
            image = image.replace("\\", "/")
            image = image.split("/")[-1]
            # TO: DO insert a try execute here
            tex = AssetsHandler.__loader__.loadTexture("game/Assets/" + image)
            # ---------------
            AssetsHandler.TEXTURES[image] = tex

    @staticmethod
    def load_assets_3d(asset_paths):

        # get the level editor
        le = object_manager.get("LevelEditor")

        for path in asset_paths:
            path = path.replace("\\", "/")
            path = path.split("/")[-1]

            # TO: DO insert a try execute here
            # model = AssetsHandler.__loader__.loadModel("game/Assets/"+path)
            res = try_execute(le.load_model, path, SCENE_GEO, reparent_to_render=False, return_func_val=True,
                              log_error=True)

            if res is not False:
                AssetsHandler.ASSETS_3D[path] = res
