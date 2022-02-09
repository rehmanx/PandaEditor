import sys
import os
import importlib
from editor.directoryWatcher import DirWatcher
from editor.utilities import get_dir_items
from editor.constants import object_manager
from editor.assetsHandler import AssetsHandler as AH


class Project(object):
    def __init__(self, level_editor):
        self.level_editor = level_editor

        self.project_name = ""
        self.project_path = ""
        self.libraries = {}

        self.proj_path_valid = False  # set this var to True, after project is set
        # and it's path is valid

        self.user_modules = []
        self.dir_watcher = DirWatcher()
        
        self.project_browser = object_manager.get("ProjectBrowser")

    def set_project(self, path):
        # clear out any existing libraries
        self.libraries.clear()

        # check if the path is a valid path
        if path is not None and path != "" and os.path.exists(path) and os.path.isdir(path):
            print("project path found ", path)
            self.proj_path_valid = True
        else:
            self.proj_path_valid = False
            self.project_path = ""
            print("unable to set project path")
            return False

        # set project path
        sys.path.append(self.project_path)
        self.project_path = path

        # key[Project] in self.libraries is default project dir,
        # it is set when project is set, and cannot be removed
        self.libraries["Project"] = path
        # start dir watcher
        self.dir_watcher.schedule(path, append=False)
        return True

    def refresh(self):
        if not self.proj_path_valid:
            print("unable to refresh project, project path is invalid !")
            return
        
        AH.refresh(self.project_browser.get_libraries())

    def on_add_library(self, name: str, path: str):
        self.dir_watcher.schedule(path)
        return True

    def on_remove_library(self, path: str):
        self.dir_watcher.unschedule(path)
        
    def load_user_modules(self):
        libs = self.project_browser.get_libraries()
        AH.load_user_modules(libs)
        
    def get_user_modules(self):
        return AH.USER_MODULES
