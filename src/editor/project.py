import sys
import os
from editor.directoryWatcher import DirWatcher
from editor.constants import object_manager


class Project(object):
    def __init__(self, level_editor):

        self.level_editor = level_editor
        self.dir_watcher = DirWatcher()
        self.project_browser = object_manager.get("ProjectBrowser")

        self.project_name = ""
        self.project_path = ""

        self.project_set = False  # set this var to True, after a project is set

        self.libraries = {}
        self.user_modules = []

    def set_project(self, path):
        # clear out any existing libraries
        self.libraries.clear()

        # set project path
        self.project_path = path
        self.project_set = True

        sys.path.append(self.project_path)

        # key[Project] in self.libraries is default project dir,
        # it is set when a project is created, and cannot be removed
        self.libraries["Project"] = path

        # start dir watcher
        self.dir_watcher.schedule(path, append=False)

        return True

    def on_add_library(self, lib_name: str, path: str):
        if lib_name in self.libraries.keys():
            print("a library with name {0} already exists".format(lib_name))
            return False

        if path in self.libraries.values():
            print("a library with path {0} already exist".format(path))
            return False

        self.dir_watcher.schedule(path)
        return True

    def on_remove_library(self, path: str):
        self.dir_watcher.unschedule(path)
