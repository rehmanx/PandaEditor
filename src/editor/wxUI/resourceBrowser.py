import os
import shutil
import wx
import wx.lib.agw.customtreectrl as customtree

from editor.colourPalette import ColourPalette as Colours
from editor.constants import object_manager, obs, SCENE_GEO
from editor.assetsHandler import AssetsHandler as ResourceHandler
from editor.utils.exceptionHandler import try_execute

RESOURCES_PATH = "editor/resources/icons/fileExtensions\\"

# resources
FOLDER_ICON = RESOURCES_PATH + "folder16.png"

PY_FILE_ICON = RESOURCES_PATH + "pyFile32.png"
USER_MOD_ICON = RESOURCES_PATH + "pyFile32.png"
ED_TOOL_ICON = RESOURCES_PATH + "pyFile32.png"

EGG_FILE_ICON = RESOURCES_PATH + "pandaIcon.png"

SOUND_FILE_ICON = RESOURCES_PATH + "file_extension_sound.png"
TEXT_FILE_ICON = RESOURCES_PATH + "file_extension_txt.png"
IMAGE_FILE_ICON = RESOURCES_PATH + "file_extension_bmp.png"
VIDEO_FILE_ICON = RESOURCES_PATH + "file_extension_video.png"

COLLAPSE_ICON = RESOURCES_PATH + "page_white.png"
EXPAND_ICON = RESOURCES_PATH + "page_white.png"

EXTENSIONS = {"folder": FOLDER_ICON,

              # "egg": EGG_FILE_ICON,
              # "bam": EGG_FILE_ICON,
              # "pz": EGG_FILE_ICON,

              # "tiff": IMAGE_FILE_ICON,
              # "tga": IMAGE_FILE_ICON,
              # "jpg": IMAGE_FILE_ICON,
              # "png": IMAGE_FILE_ICON,

              "py": PY_FILE_ICON,

              # "mp4": VIDEO_FILE_ICON,
              # "mp3": IMAGE_FILE_ICON,
              }

#
EVT_NEW_DIR = wx.NewId()
EVT_RENAME_ITEM = wx.NewId()
EVT_DUPLICATE_ITEM = wx.NewId()
EVT_REMOVE_ITEM = wx.NewId()
EVT_SHOW_IN_EXPLORER = wx.NewId()

EVT_CREATE_PY_MOD = wx.NewId()
EVT_CREATE_P3D_USER_MOD = wx.NewId()
EVT_CREATE_ED_TOOL = wx.NewId()
EVT_DISABLE_PY_FILE = wx.NewId()
#
EVT_LOAD_MODEL = wx.NewId()
#
EVT_APPEND_LIBRARY = wx.NewId()
EVT_IMPORT_ASSETS = wx.NewId()


class ResourceBrowser(customtree.CustomTreeCtrl):
    def __init__(self, parent, wx_main, *args, **kwargs):
        customtree.CustomTreeCtrl.__init__(self, parent, *args, **kwargs)
        self.wxMain = wx_main

        self.SetBackgroundColour(Colours.NORMAL_GREY)
        self.SetWindowStyleFlag(wx.BORDER_SUNKEN)

        agw_win_styles = wx.TR_DEFAULT_STYLE | wx.TR_SINGLE | wx.TR_MULTIPLE | wx.TR_HIDE_ROOT
        agw_win_styles |= wx.TR_TWIST_BUTTONS | wx.TR_NO_LINES

        self.SetAGWWindowStyleFlag(agw_win_styles)
        self.SetIndent(10)
        self.SetSpacing(10)

        self.SetBorderPen(wx.Pen((0, 0, 0), 0, wx.TRANSPARENT))
        self.EnableSelectionGradient(True)
        self.SetGradientStyle(True)
        self.SetFirstGradientColour(wx.Colour(46, 46, 46))
        self.SetSecondGradientColour(wx.Colour(123, 123, 123))

        object_manager.add_object("ProjectBrowser", self)

        # image_index associates a file_extension, with image index in tree image_list  
        self.image_index = {}
        # create an image list for tree control to use
        self.image_list = wx.ImageList(16, 16)

        i = 0
        for ext in EXTENSIONS.keys():
            # create a bitmap
            icon_bitmap = wx.Bitmap(EXTENSIONS[ext])
            # and append it to image list
            self.image_list.Add(icon_bitmap)
            self.image_index[ext] = i
            i = i + 1
        self.SetImageList(self.image_list)

        # file menus associates a file extension with, or an extension with a function,
        # which creates its menus, to be used in popup menus
        self.file_menus = {"directory": [self.create_directory_menu_items,
                                         self.create_generic_menu_items], "py": [self.create_py_file_menu_items,
                                                                                 self.create_generic_menu_items],
                           "generic": [self.create_generic_menu_items], "pz": [self.create_generic_menu_items],
                           "egg": [self.create_generic_menu_items]}

        # self.SetButtonsImageList(self.image_list)

        self.root_path = ""
        self.libraries = {}

        # resource maps with the files of one particular type their it's full
        # path as on disk, to it's corresponding type for example...
        # self.resources[py] = ['path\\file1.py', 'path\\file.py']
        # self.resources[egg] = ['path\\SomeModel.egg', 'path\\SomeActor.egg']
        self.resources = {}

        # name_to_item maps a file's or directory's name to it's
        # corresponding tree item and other info such as expanded status
        # name_to_item[file_name] = item
        self.name_to_item = {}

        self.event_map = {
            EVT_NEW_DIR: (self.on_file_op, "add_folder"),
            EVT_RENAME_ITEM: (self.on_file_op, "rename_item"),
            EVT_DUPLICATE_ITEM: (self.on_file_op, "duplicate"),
            EVT_REMOVE_ITEM: (self.on_file_op, "remove_item"),
            EVT_SHOW_IN_EXPLORER: (self.on_file_op, "show_in_explorer"),
            EVT_CREATE_PY_MOD: (self.create_asset, "py_mod"),
            EVT_CREATE_P3D_USER_MOD: (self.create_asset, "p3d_user_mod"),
            EVT_CREATE_ED_TOOL: (self.create_asset, "p3d_ed_tool"),
            EVT_DISABLE_PY_FILE: (self.set_py_mod_active, ""),

            EVT_APPEND_LIBRARY: (self.append_library, None),
            EVT_IMPORT_ASSETS: (self.import_assets, None),
        }

        self.rootnode = self.AddRoot(os.path.basename("Project"), image=self.image_index["folder"], data="")
        self.selections = []

        self.mouse_left_down = False
        self.is_dragging = False

        # if set to True, files in a folder are organized based on file_extension,
        # before adding them to tree, similar extension files are placed together
        self.organize_tree = True

        # Event Handlers
        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.on_item_expanded)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.on_item_collapsed)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_item_selected)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_item_activated)
        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.create_popup_menu)
        self.Bind(wx.EVT_MENU, self.on_select_context)

        self.Bind(wx.EVT_LEFT_DOWN, self.on_evt_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_evt_left_up)
        self.Bind(wx.EVT_MOTION, self.on_evt_mouse_move)

    def build_tree(self, path, root_name: str = "", initial=True):
        """builds tree items from given path, provided a root node exists"""

        assert os.path.exists(path), "error: path does not exist"
        assert os.path.isdir(path), "error: path is not a directory"

        if initial:
            self.libraries.clear()

            self.resources.clear()
            for ext in EXTENSIONS.keys():
                self.resources[ext] = []

            self.name_to_item.clear()
            self.DeleteChildren(self.GetRootItem())
            self.root_path = path
            self.SetItemData(self.rootnode, data=path)

            # setup a default project library
            parent_item = self.AppendItem(self.rootnode, "Project", data=path, image=self.image_index["folder"])
            self.name_to_item["Project"] = parent_item
            self.libraries["Project"] = path

        else:
            # TO:DO make sure that root_name does not already exists via self.name_to_item
            # before appending a new library
            parent_item = self.AppendItem(self.rootnode, root_name, data=path, image=self.folder_img_index)
            self.libraries[root_name] = path
            #

        self.UnselectAll()

        self.create_tree_from_dir(dir_path=path, parent=parent_item)

        self.update_resource_handler()

        self.ExpandAll()

    def rebuild_tree(self):
        """rebuild tree attempts to rebuild entire tree from current tree.libraries """

        # save the current selection to reselect it once the tree is reloaded
        selection = self.GetSelection()
        if selection:
            selection = self.GetItemText(selection)

        print("rebuilding tree")

        self.UnselectAll()

        parent = self.name_to_item["Project"]
        self.name_to_item.clear()
        self.name_to_item["Project"] = parent

        # unload the resources & create a key for each resource type
        self.resources.clear()
        for ext in EXTENSIONS.keys():
            self.resources[ext] = []
        # 
        self.DeleteChildren(self.GetRootItem())

        for key in self.libraries.keys():
            path = self.libraries[key]
            parent_item = self.AppendItem(self.rootnode, key, data=path, image=self.image_index["folder"])
            self.create_tree_from_dir(path, parent_item)

        self.ExpandAll()
        self.Refresh()

        self.update_resource_handler()

        # select tree item that was previously selected, if it is still parent,
        # after rebuilding tree
        if selection in self.name_to_item.keys():
            self.SelectItem(self.name_to_item[selection])

    files_and_extensions = {}

    def organize(self, _files):
        while len(_files) != 0:
            _file = _files.pop()
            extension = _file.split(".")[-1]
            if extension not in self.files_and_extensions.keys():
                self.files_and_extensions[extension] = []
            self.files_and_extensions[extension].append(_file)
            self.organize(_files)

    def create_tree_from_dir(self, dir_path=None, parent=None):
        def append_item(_file_path, _file_name):
            extension = _file_path.split(".")[-1]
            if extension in EXTENSIONS:
                icon = self.image_index[extension]
                __item = self.AppendItem(parent, file, data=file_path, image=icon)

                # self.SetItemTextColour(item, wx.Colour(255, 255, 190, 255))
                self.name_to_item[file] = __item
                self.resources[extension].append(_file_path)

        dir_files = os.listdir(dir_path)

        tmp_files = []
        folders = []
        for _item in dir_files:
            is_file = os.path.isfile(dir_path + "/" + _item)
            if is_file:
                tmp_files.append(_item)
            else:
                folders.append(_item)

        self.files_and_extensions.clear()
        self.organize(tmp_files)

        tmp = []
        for key in self.files_and_extensions.keys():
            tmp += self.files_and_extensions[key]
        tmp += folders
        dir_files = tmp

        for file in dir_files:
            file_path = dir_path + "/" + file

            if os.path.isdir(file_path) and file != "__pycache__":
                item = self.AppendItem(parent, file, data=file_path, image=self.image_index["folder"])
                # self.SetItemTextColour(item, wx.Colour(255, 255, 190, 255))
                self.Expand(item)
                self.name_to_item[file] = item

                self.create_tree_from_dir(file_path, item)

            elif os.path.isfile(file_path):
                append_item(file_path, file)

    def update_resource_handler(self):
        # refresh Resource Handler to handle all loaded/reloaded resources
        modules = self.resources["py"]

        # all the textures
        # TO: DO make sure extensions also exist in EXTENSIONS
        '''
        textures = self.resources["tiff"] + \
                   self.resources["tga"] + \
                   self.resources["jpg"] + \
                   self.resources["png"]
        '''
        textures = []

        '''
        models = self.resources["egg"] + self.resources["pz"]
        '''
        models = []

        ResourceHandler.load(modules, textures, models)

    def append_library(self, name, path):
        if name not in self.libraries.keys():
            self.libraries[name] = path
            print("Library appended name: {0} @ path: {1}".format(name, path))
            return True
        return False

    def on_item_expanded(self, event):
        event.Skip()

    def on_item_collapsed(self, event):
        event.Skip()

    def on_item_activated(self, evt):
        item_path = self.GetItemData(self.GetSelection())
        if os.path.isfile(item_path) and item_path.split(".")[-1] == "py":
            pass
            # self.open_file(item_path)
        evt.Skip()

    def on_item_selected(self, evt):
        selections = []
        for item in self.GetSelections():
            name = self.GetItemText(item)
            data = self.GetItemData(item)
            selections.append((name, data))

        obs.trigger("SelectTreeItem", selections)
        evt.Skip()

    def on_evt_mouse_move(self, evt):
        if self.mouse_left_down:
            self.is_dragging = True

            for item in self.tmp_selections:
                self.SetItemTextColour(item, wx.Colour(0, 0, 0, 255))

            # highlight item under the mouse, when dragging
            self.tmp_selections.clear()
            x, y = evt.GetPosition()
            (_id, flag) = self.HitTest((x, y))
            if _id:
                self.SetItemTextColour(_id, wx.Colour(255, 255, 190, 255))
                self.tmp_selections.append(_id)

        if not self.is_dragging and len(self.tmp_selections) > 0:
            for item in self.tmp_selections:
                self.SetItemTextColour(item, wx.Colour(0, 0, 0, 255))

        evt.Skip()

    def on_evt_left_down(self, evt):
        self.mouse_left_down = True
        evt.Skip()

    def on_evt_left_up(self, evt):
        # do drag drop here
        x, y = evt.GetPosition()
        (_id, flag) = self.HitTest((x, y))

        if self.is_dragging and _id:
            # print("{0} dropped onto {1}".format(self.GetSelections(), self.GetItemText(_id)) )
            for item in self.GetSelections():
                if _id == item:
                    continue

                self.do_drag_drop(self.GetItemData(item), self.GetItemData(_id))

        self.mouse_left_down = False
        self.is_dragging = False

        evt.Skip()

    tmp_selections = []

    def do_drag_drop(self, src_file: str, target_dir: str):
        # move a source file to target directory, the source file and target directory must exist,
        """src=source file, target=target directory"""
        # make sure source is a file & target directory exists
        if not os.path.isfile(src_file) or not os.path.isdir(target_dir):
            print("file move operation failed")
            return False

        # generate a new target file path, to move src_file to, by combining target_dir with src_file_name
        target_file = target_dir + "/" + src_file.split("/")[-1]

        # ---------------TO:DO---------------
        # make sure the target_file already does not exists, if it does exists then ask
        # user for a file overwrite operation
        if os.path.isfile(target_file):
            msg = "file {0} already exists in directort {1}".format(src_file, target_dir)
            print(msg)
            return

        shutil.move(src_file, target_file)
        print("from {0} <==TO==> {1}".format(src_file, target_dir))
        return True

    def end_drag(self):
        self.mouse_left_down = False

    def on_select_context(self, event):
        if event.GetId() in self.event_map.keys():
            foo = self.event_map[event.GetId()][0]
            args = self.event_map[event.GetId()][1]
            foo(args)

        event.Skip()

    def create_popup_menu(self, evt):
        selections = self.GetSelections()

        if len(selections) > 1:
            item_ext = "generic"
        else:
            item = selections[0]
            item_path = self.GetItemData(item)
            item_text = self.GetItemText(item)
            item_ext = item_text.split(".")[-1]  # file_extension
            is_item_dir = os.path.isdir(item_path)

            if is_item_dir:
                item_ext = "directory"
            elif item_ext not in self.file_menus.keys():
                return

        popup_menu = wx.Menu()

        for func in self.file_menus[item_ext]:
            func(popup_menu)

        self.PopupMenu(popup_menu, evt.GetPoint())
        popup_menu.Destroy()

        evt.Skip()

    def build_menu(self, menu, items):
        for i in range(len(items)):
            _items = items[i]

            if _items == "":
                menu.AppendSeparator()
                continue

            menu_item = wx.MenuItem(menu, _items[0], _items[1])
            # menu_item.SetBitmap(wx.Bitmap('exit.png'))
            menu.Append(menu_item)

    def create_directory_menu_items(self, parent_menu):
        # ******* build menu items for a directory ******************************
        # add objects menu
        objects_items = [
            (EVT_CREATE_PY_MOD, "&UserModule", None),
            (EVT_CREATE_P3D_USER_MOD, "&P3d UserModule", None),
            (EVT_CREATE_ED_TOOL, "&P3d EditorTool", None),
            (EVT_NEW_DIR, "&New Folder", None)
        ]
        objects_menu = wx.Menu()
        self.build_menu(objects_menu, objects_items)
        parent_menu.Append(wx.ID_ANY, "Add", objects_menu)

        # import assets menu
        import_assets_item = wx.MenuItem(parent_menu, EVT_IMPORT_ASSETS, "Import Assets")
        parent_menu.Append(import_assets_item)
        parent_menu.AppendSeparator()

        # show in explorer menu
        library_items = [(EVT_SHOW_IN_EXPLORER, "&Show In Explorer", None)]
        self.build_menu(parent_menu, library_items)

    def create_py_file_menu_items(self, parent_menu):
        # placeholder system for loading assets until an asset manager is in place
        item_path = self.GetItemData(self.GetSelection())

        ext = item_path.split(".")[-1]
        name = item_path.split(".")[0].split("/")[-1]

        if os.path.isfile(item_path) and ext == "py":
            mod = object_manager.get("LevelEditor").get_mod_instance(name)
            # get mod active status
            if mod:
                x = mod.is_enabled()
                if x:
                    menu_txt = "&DisableMod"
                    # change corresponding item graphics
                else:
                    menu_txt = "&EnableMod"

                py_file_items = [(EVT_DISABLE_PY_FILE, menu_txt, None)]
                self.build_menu(parent_menu, py_file_items)
                parent_menu.AppendSeparator()

    def create_generic_menu_items(self, parent_menu):
        # others  menu
        misc_items = [(EVT_RENAME_ITEM, "&Rename", None),
                      (EVT_REMOVE_ITEM, "&Remove", None),
                      (EVT_DUPLICATE_ITEM, "&Duplicate", None)]
        self.build_menu(parent_menu, misc_items)

    def on_file_op(self, op, *args, **kwargs):
        def can_perform_operation():
            if self.GetSelection() == self.GetRootItem():
                return False
            return True

        if op == "add_folder":
            self.add_dir()

        elif op == "show_in_explorer":
            self.show_in_explorer(self.GetItemData(self.GetSelection()))

        elif op == "rename_item" and can_perform_operation():
            self.rename_item()

        elif op == "duplicate" and can_perform_operation():
            self.duplicate()

        elif op == "remove_item" and can_perform_operation():
            self.remove_item()

        elif op == "LoadModel":
            # if it is an absolute path
            absolute = self.GetItemParent(self.GetSelection()) == self.GetRootItem()
            if absolute:
                path = self.GetItemText(self.GetSelection())
                obs.trigger("LoadModel", path, SCENE_GEO)
            else:
                proj_path = self.GetItemPyData(self.GetRootItem())
                item_path = self.GetItemPyData(self.GetSelection())
                item_path = item_path[len(proj_path) + 1:]
                obs.trigger("LoadModel", item_path, SCENE_GEO)

    def show_in_explorer(self, path):
        path = os.path.realpath(path)
        os.startfile(path)

    def add_dir(self):
        def on_ok(text):
            if text == "":
                return

            curr_dir = self.GetItemData(self.GetSelection())
            new_dir = curr_dir + "/" + text
            os.mkdir(new_dir)
            self.AppendItem(self.GetSelection(), text, data=new_dir, image=self.image_index["folder"])

        wx_main = object_manager.get("WxMain")
        dm = wx_main.dialogue_manager
        dm.create_dialog("TextEntryDialog", "New Directory", descriptor_text="Enter name", ok_call=on_ok)

    def rename_item(self):
        def on_ok(text):
            if text == "" or text in self.name_to_item:
                print("FileRenameError: incorrect name entry or name already exits")
                return

            selection = self.GetSelection()

            old_dir_path = self.GetItemData(selection)
            old_dir_name = old_dir_path.split("/")[-1]
            new_dir = old_dir_path[:len(old_dir_path) - len(old_dir_name) - 1]
            new_dir = new_dir + "/" + text

            # if the selected item is a library item, then remove existing library entry,
            # and create a new one with existing data as of original entry
            item_text = self.GetItemText(selection)
            if item_text in self.libraries.keys():
                # also make sure libraries does not have an existing entry matching new text
                if text not in self.libraries.keys():
                    del self.libraries[item_text]
                    self.libraries[text] = old_dir_path
                else:
                    print("ProjectBrowser: rename op failed")
            else:
                os.rename(old_dir_path, new_dir)
                self.SetItemData(self.GetSelection(), new_dir)

            # update tree controls
            self.SetItemText(self.GetSelection(), text)

        wx_main = object_manager.get("WxMain")
        dm = wx_main.dialogue_manager
        dm.create_dialog("TextEntryDialog",
                         "Rename Item", descriptor_text="Rename Selection", ok_call=on_ok,
                         starting_text=self.GetItemText(self.GetSelection()))

    def duplicate(self, *args):
        def _duplicate(original_file, new_file_name):
            # join new_file's_name with tail of original file 
            # to get complete destination for new_file
            head, tail = os.path.split(original_file)
            new_file = head + "//" + new_file_name
            shutil.copy(original_file, new_file)
            print("duplicated", new_file)

        selections = self.GetSelections()

        i = 0
        for sel in selections:
            name = self.GetItemText(sel)
            # item's name includes full file name name with extension as on disk
            # e.g CharacterController.py, so modify file's name to a unique name
            # before duplicating it
            # name, ext = name.split(".")  # split file_name and extension
            item = name.split(".")  # split file_name and extension
            new_file = item[0] + str(i) + "." + item[len(item) - 1]  # and create a unique one

            path = self.GetItemData(sel)
            try_execute(_duplicate, path, new_file)
            i += 1

    def remove_item(self, *args):
        def on_ok():
            selections = self.GetSelections()
            for item in selections:
                item_text = self.GetItemText(item)
                item_path = self.GetItemData(item)

                if item_text in self.libraries.keys():
                    del self.libraries[item_text]
                    obs.trigger("OnRemoveLibrary", item_path)
                    obs.trigger("DirectoryEvent")
                else:
                    result = try_execute(os.remove, item_path)

                    if result:
                        del self.name_to_item[item_text]  # remove from name_to_items
                        self.Delete(item)

        wx_main = object_manager.get("WxMain")
        dm = wx_main.dialogue_manager
        dm.create_dialog("YesNoDialog", "Delete Item", descriptor_text="Confirm remove selection(s) ?", ok_call=on_ok)

    def create_asset(self, _type):
        def on_ok(text):
            if text == "":
                return

            path = self.GetItemData(self.GetSelection())
            path = path + "/" + text

            if os.path.exists(path):
                print("path already exists")
                return

            obs.trigger("CreateAsset", _type, path)

        wx_main = object_manager.get("WxMain")
        dm = wx_main.dialogue_manager
        dm.create_dialog("TextEntryDialog", "CreateNewAsset", descriptor_text="New Asset Name", ok_call=on_ok)

    def set_py_mod_active(self, *args):
        item_name = self.GetItemData(self.GetSelection()).split(".")[0].split("/")[-1]
        obs.trigger("SetModEnabledStatus", item_name)

    def import_assets(self, *args):
        def create_wild_card(wild_card=""):
            for ext in EXTENSIONS:
                wild_card += "*" + "." + ext + ";"
            return wild_card

        def copy_item(src_item, dst):
            shutil.copyfile(src_item, dst)

        # create wildcard from supported extensions
        wd = "import assets |"
        wd = create_wild_card(wd)

        style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE
        with wx.FileDialog(self, "Import Assets", wildcard=wd, style=style) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed loading the file chosen by the user
            src_paths = fileDialog.GetPaths()
            dst = self.GetItemData(self.GetSelection())
            for path in src_paths:
                x = try_execute(copy_item, path, dst + "\\" + path.split("\\")[-1])

    def get_selected_path(self):
        """Get the selected path"""
        sel = self.GetSelection()
        path = self.GetItemPyData(sel)
        return path

    def get_selected_paths(self):
        """Get a list of selected paths"""
        selections = self.GetSelections()
        paths = [self.GetItemPyData(sel) for sel in selections]
        return paths

    def get_item_by_name(self, item_name=""):
        if self.name_to_item.__contains__(item_name):
            return self.name_to_item[item_name]
        return None

    def get_libraries(self):
        return self.libraries
