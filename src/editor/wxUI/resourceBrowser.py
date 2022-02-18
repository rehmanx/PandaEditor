import os
import shutil
import wx
import wx.lib.agw.customtreectrl as customtree

from editor.colourPalette import ColourPalette as Colours
from editor.constants import object_manager, obs, SCENE_GEO, FILE_EXTENSIONS_ICONS_PATH
from editor.utils.exceptionHandler import try_execute


# icons / thumbnails names
FOLDER_ICON = FILE_EXTENSIONS_ICONS_PATH + "\\" + "folder16.png"

PY_FILE_ICON = FILE_EXTENSIONS_ICONS_PATH + "\\" + "pyFile32.png"
USER_MOD_ICON = FILE_EXTENSIONS_ICONS_PATH + "\\" + "pyFile32.png"
ED_TOOL_ICON = FILE_EXTENSIONS_ICONS_PATH + "\\" + "pyFile32.png"

EGG_FILE_ICON = FILE_EXTENSIONS_ICONS_PATH + "\\" + "pandaIcon.png"

SOUND_FILE_ICON = FILE_EXTENSIONS_ICONS_PATH + "\\" + "file_extension_sound.png"
TEXT_FILE_ICON = FILE_EXTENSIONS_ICONS_PATH + "\\" + "file_extension_txt.png"
IMAGE_FILE_ICON = FILE_EXTENSIONS_ICONS_PATH + "\\" + "file_extension_bmp.png"
VIDEO_FILE_ICON = FILE_EXTENSIONS_ICONS_PATH + "\\" + "file_extension_video.png"

COLLAPSE_ICON = FILE_EXTENSIONS_ICONS_PATH + "\\" + "page_white.png"
EXPAND_ICON = FILE_EXTENSIONS_ICONS_PATH + "\\" + "page_white.png"

# supported extensions
EXTENSIONS = {"folder": FOLDER_ICON,

              "egg": EGG_FILE_ICON,
              "bam": EGG_FILE_ICON,
              "pz": EGG_FILE_ICON,

              "tiff": IMAGE_FILE_ICON,
              "tga": IMAGE_FILE_ICON,
              "jpg": IMAGE_FILE_ICON,
              "png": IMAGE_FILE_ICON,

              "py": PY_FILE_ICON,

              "mp4": VIDEO_FILE_ICON,
              "mp3": IMAGE_FILE_ICON,
              }

# extension to icon map


# event ids for different event types
EVT_NEW_DIR = wx.NewId()
EVT_RENAME_ITEM = wx.NewId()
EVT_DUPLICATE_ITEM = wx.NewId()
EVT_REMOVE_ITEM = wx.NewId()
EVT_SHOW_IN_EXPLORER = wx.NewId()

EVT_CREATE_PY_MOD = wx.NewId()
EVT_CREATE_P3D_USER_MOD = wx.NewId()
EVT_CREATE_ED_TOOL = wx.NewId()

EVT_LOAD_MODEL = wx.NewId()

EVT_APPEND_LIBRARY = wx.NewId()
EVT_IMPORT_ASSETS = wx.NewId()


def build_menu(menu, items):
    for i in range(len(items)):
        _items = items[i]

        if _items == "":
            menu.AppendSeparator()
            continue

        menu_item = wx.MenuItem(menu, _items[0], _items[1])
        # menu_item.SetBitmap(wx.Bitmap('exit.png'))
        menu.Append(menu_item)


class ResourceBrowser(customtree.CustomTreeCtrl):
    def __init__(self, parent, wx_main, *args, **kwargs):
        customtree.CustomTreeCtrl.__init__(self, parent, *args, **kwargs)

        self.wx_main = wx_main
        object_manager.add_object("ProjectBrowser", self)
        self.organize_tree = True  # organize a tree based on file_extensions

        # ---------------------------------------------------------------------------- #
        self.SetBackgroundColour(Colours.NORMAL_GREY)
        self.SetWindowStyleFlag(wx.BORDER_SUNKEN)

        agw_win_styles = wx.TR_DEFAULT_STYLE | wx.TR_SINGLE | wx.TR_MULTIPLE | wx.TR_HIDE_ROOT
        agw_win_styles |= wx.TR_TWIST_BUTTONS  # | wx.TR_NO_LINES

        self.SetAGWWindowStyleFlag(agw_win_styles)
        self.SetIndent(10)
        self.SetSpacing(10)

        self.SetBorderPen(wx.Pen((0, 0, 0), 0, wx.TRANSPARENT))
        self.EnableSelectionGradient(True)
        self.SetGradientStyle(True)
        self.SetFirstGradientColour(wx.Colour(46, 46, 46))
        self.SetSecondGradientColour(wx.Colour(123, 123, 123))

        # ---------------------------------------------------------------------------- #
        self.image_index = {}  # associates an extension which indexes into tree image_list
        self.image_list = wx.ImageList(16, 16)  # create an image list for tree control to use

        i = 0
        for ext in EXTENSIONS.keys():
            self.image_index[ext] = i
            icon_bitmap = wx.Bitmap(EXTENSIONS[ext])  # create a bitmap
            self.image_list.Add(icon_bitmap)  # and append it to image list
            i = i + 1

        self.SetImageList(self.image_list)
        # ---------------------------------------------------------------------------- #

        self.root_node = self.AddRoot("RootNode", image=self.image_index["folder"], data="")
        self.root_path = ""

        # for drag drop operations
        self.mouse_left_down = False
        self.is_dragging = False

        # ---------------------------------------------------------------------------- #
        self.libraries = {}  # all current loaded libraries
        self.resources = {}  # maps and saves all loaded resources e.g [py] = {all .py resources}...
        self.name_to_item = {}  # maps a file's or directory's name to it's corresponding tree item
        # e.g. name_to_item[file_name] = item

        # ---------------------------------------------------------------------------- #
        # file menus associates a file extension with, or an extension with a function,
        # which creates its menus, to be used in popup menus
        self.file_menus = {"directory": [self.create_directory_menu_items, self.create_generic_menu_items],
                           "py": [self.create_generic_menu_items],
                           "generic": [self.create_generic_menu_items],
                           "pz": [self.create_generic_menu_items],
                           "egg": [self.create_generic_menu_items]}

        self.event_map = {
            EVT_NEW_DIR: (self.on_file_op, "add_folder"),
            EVT_RENAME_ITEM: (self.on_file_op, "rename_item"),
            EVT_DUPLICATE_ITEM: (self.on_file_op, "duplicate"),
            EVT_REMOVE_ITEM: (self.on_file_op, "remove_item"),
            EVT_SHOW_IN_EXPLORER: (self.on_file_op, "show_in_explorer"),

            EVT_CREATE_PY_MOD: (self.create_asset, "py_mod"),
            EVT_CREATE_P3D_USER_MOD: (self.create_asset, "p3d_user_mod"),
            EVT_CREATE_ED_TOOL: (self.create_asset, "p3d_ed_tool"),

            EVT_APPEND_LIBRARY: (self.append_library, None),
            EVT_IMPORT_ASSETS: (self.import_assets, None),
        }

        # bind event handlers with corresponding method calls
        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.on_item_expanded)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.on_item_collapsed)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_item_selected)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_item_activated)

        self.Bind(wx.EVT_LEFT_DOWN, self.on_evt_left_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_evt_left_up)
        self.Bind(wx.EVT_MOTION, self.on_evt_mouse_move)

        self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.create_popup_menu)
        self.Bind(wx.EVT_MENU, self.on_select_context)

    # ****************** #
    files_and_extensions = {}  # temporarily saves all files with same extensions when organizing tree
    tmp_selections = []  #

    # **************** All methods bounded to different tree events **************** #
    def on_item_expanded(self, event):
        event.Skip()

    def on_item_collapsed(self, event):
        event.Skip()

    def on_item_selected(self, evt):
        selections = []
        for item in self.GetSelections():
            name = self.GetItemText(item)
            data = self.GetItemData(item)
            selections.append((name, data))

        obs.trigger("SelectTreeItem", selections)
        evt.Skip()

    def on_item_activated(self, evt):
        item_path = self.GetItemData(self.GetSelection())
        if os.path.isfile(item_path) and item_path.split(".")[-1] == "py":
            pass
            # self.open_file(item_path)
        evt.Skip()

    def on_evt_left_down(self, evt):
        self.mouse_left_down = True
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

    def on_select_context(self, event):
        if event.GetId() in self.event_map.keys():
            foo = self.event_map[event.GetId()][0]
            args = self.event_map[event.GetId()][1]
            foo(args)

        event.Skip()

    # **************** All methods for building tree items **************** #
    def build_tree(self, path, root_name: str = "", initial=True):
        """builds tree items from given path, provided a root node exists"""

        assert os.path.exists(path), "error: path does not exist"
        assert os.path.isdir(path), "error: path is not a directory"

        if initial:  # when first time a project is set up
            self.libraries.clear()

            self.resources.clear()
            for ext in EXTENSIONS.keys():
                self.resources[ext] = []

            self.name_to_item.clear()
            self.DeleteChildren(self.GetRootItem())
            self.root_path = path

            # setup a default project library
            parent_item = self.AppendItem(self.root_node, "Project", data=path, image=self.image_index["folder"])
            self.name_to_item["Project"] = parent_item
            self.libraries["Project"] = path

        else:
            # TO:DO make sure that root_name does not already exist via self.name_to_item
            # before appending a new library
            parent_item = self.AppendItem(self.root_node, root_name, data=path, image=self.image_index["folder"])
            self.libraries[root_name] = path

        self.UnselectAll()

        self.create_tree_from_dir(dir_path=path, parent=parent_item)

        self.ExpandAll()

    def rebuild_tree(self):
        """rebuild tree attempts to rebuild entire tree from current tree.libraries """
        print("rebuilding resources")

        # ------------- first clean up everything properly ------------- #
        # save the current selection to reselect it once the tree is reloaded
        selection = self.GetSelection()
        if selection:
            selection = self.GetItemText(selection)
        self.UnselectAll()

        # delete all children
        self.DeleteChildren(self.GetRootItem())

        # unload all resources
        self.resources.clear()

        # ------------- now start process of rebuilding everything ------------- #
        parent = self.name_to_item["Project"]
        self.name_to_item.clear()
        self.name_to_item["Project"] = parent
        del parent

        # create a new key for each resource type
        for ext in EXTENSIONS.keys():
            self.resources[ext] = []

        for key in self.libraries.keys():
            path = self.libraries[key]
            parent_item = self.AppendItem(self.root_node, key, data=path, image=self.image_index["folder"])
            self.create_tree_from_dir(path, parent_item)

        self.ExpandAll()
        self.Refresh()

        # self.update_resource_handler()

        # select tree item that was previously selected.
        if selection in self.name_to_item.keys():
            self.SelectItem(self.name_to_item[selection])

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

            elif os.path.isfile(file_path) and file != "__init__":
                append_item(file_path, file)

    def organize(self, _files):
        while len(_files) != 0:
            _file = _files.pop()
            extension = _file.split(".")[-1]
            if extension not in self.files_and_extensions.keys():
                self.files_and_extensions[extension] = []
            self.files_and_extensions[extension].append(_file)
            self.organize(_files)

    def append_library(self, name, path):
        self.libraries[name] = path
        return True

    # ----------------- All methods for building context menus ----------------- #
    def create_directory_menu_items(self, parent_menu):
        # add objects menu
        objects_items = [
            (EVT_CREATE_PY_MOD, "&Python Module", None),
            (EVT_CREATE_P3D_USER_MOD, "&User Module", None),
            (EVT_CREATE_ED_TOOL, "&Editor Plugin", None),
            (EVT_NEW_DIR, "&New Folder", None)
        ]
        objects_menu = wx.Menu()
        build_menu(objects_menu, objects_items)
        parent_menu.Append(wx.ID_ANY, "Add", objects_menu)

        # import assets menu
        import_assets_item = wx.MenuItem(parent_menu, EVT_IMPORT_ASSETS, "Import Assets")
        parent_menu.Append(import_assets_item)
        parent_menu.AppendSeparator()

        # show in explorer menu
        library_items = [(EVT_SHOW_IN_EXPLORER, "&Show In Explorer", None)]
        build_menu(parent_menu, library_items)

    def create_generic_menu_items(self, parent_menu):
        # others  menu
        misc_items = [(EVT_RENAME_ITEM, "&Rename", None),
                      (EVT_REMOVE_ITEM, "&Remove", None),
                      (EVT_DUPLICATE_ITEM, "&Duplicate", None)]
        build_menu(parent_menu, misc_items)

    # **************** file explorer operations **************** #
    def on_file_op(self, op, *args, **kwargs):
        def can_perform_operation():
            if self.GetSelection() == self.GetRootItem():
                return False
            return True

        if op == "add_folder":
            curr_dir = self.GetItemData(self.GetSelection())
            self.add_dir(curr_dir)

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

    @staticmethod
    def do_drag_drop(src_file: str, target_dir: str):
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

    @staticmethod
    def show_in_explorer(path):
        path = os.path.realpath(path)
        os.startfile(path)

    @staticmethod
    def add_dir(curr_directory):
        """adds a new directory and returns it"""

        def on_ok(_new_dir_name):
            if _new_dir_name == "":
                return

            curr_dir = curr_directory
            new_dir = curr_dir + "/" + _new_dir_name
            os.mkdir(new_dir)
            return _new_dir_name

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

        dm = self.wx_main.dialogue_manager
        dm.create_dialog("TextEntryDialog",
                         "Rename Item", descriptor_text="Rename Selection", ok_call=on_ok,
                         starting_text=self.GetItemText(self.GetSelection()))

    def duplicate(self, *args):
        def get_unique_file_name(_file_name, _ext, _original):
            """Provided a file_name, it's extension and original file this function returns
            a unique file_name with same name, extension and path as of original"""

            is_name_unique = False
            counter = 0
            max_count = 5

            _unique_name = ""

            head, tail = os.path.split(_original)

            while not is_name_unique:

                # to break free from while loop
                counter += 1
                if counter > max_count:
                    break

                # create a unique file name by adding a number to original file name
                _unique_name = _file_name + str(counter) + "." + _ext
                if not os.path.exists(head + "//" + _unique_name):
                    is_name_unique = True

            if is_name_unique:
                return _unique_name
            return False

        def _duplicate(original_file, new_file_name):
            head, tail = os.path.split(original_file)  # name and path of original file
            _new_file = head + "//" + new_file_name  # path of original + new file's name
            shutil.copy(original_file, _new_file)
            print("duplicated {0}".format(_new_file))

        selections = self.GetSelections()

        if len(selections) > 20:
            print("max 20 duplicates allowed...!")
            return

        for sel in selections:
            item = self.GetItemText(sel)

            file_name, extension = item.split(".")  # get file_name and extension
            path = self.GetItemData(sel)

            if os.path.isdir(path):
                print("duplicating a directory is currently not supported...!")
                pass

            unique_name = get_unique_file_name(file_name, extension, path)  # get a unique file name
            if unique_name:
                try_execute(_duplicate, path, unique_name)

            # new_file = file_name + str(i) + "." + extension  # and create a unique one
            # try_execute(_duplicate, path, new_file)

    def remove_item(self, *args):
        def on_ok():
            selections = self.GetSelections()
            for item in selections:
                item_text = self.GetItemText(item)
                item_path = self.GetItemData(item)

                if item_text == "Project":
                    print("cannot remove project path...!")
                    continue

                if item_text in self.libraries.keys():
                    del self.libraries[item_text]
                    obs.trigger("OnRemoveLibrary", item_path)
                else:
                    result = try_execute(os.remove, item_path)

                    if result:
                        del self.name_to_item[item_text]  # remove from name_to_items
                        self.Delete(item)

        dm = self.wx_main.dialogue_manager
        dm.create_dialog("YesNoDialog", "Delete Item", descriptor_text="Confirm remove selection(s) ?",
                         ok_call=on_ok)

    def create_asset(self, _type):
        def on_ok(text):
            if text == "":
                return

            path = self.GetItemData(self.GetSelection())
            path = path + "/" + text

            if os.path.exists(path):
                print("path already exists...!")
                return

            obs.trigger("CreateAsset", _type, path)

        wx_main = object_manager.get("WxMain")
        dm = wx_main.dialogue_manager
        dm.create_dialog("TextEntryDialog", "CreateNewAsset", descriptor_text="New Asset Name", ok_call=on_ok)

    def import_assets(self, *args):
        def create_wild_card(wild_card=""):
            for ext in EXTENSIONS:
                wild_card += "*" + "." + ext + ";"
            return wild_card

        def copy_item(src_item, _dst):
            shutil.copyfile(src_item, _dst)

        # create wildcard from supported extensions
        wd = "import assets |"
        wd = create_wild_card(wd)

        style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE
        with wx.FileDialog(self, "Import Assets", wildcard=wd, style=style) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind

            # Proceed to import the selected files
            selected_file_paths = fileDialog.GetPaths()  # paths of all selected files
            target_destination = self.GetItemData(self.GetSelection())  # destination to copy to

            for path in selected_file_paths:
                file_name = path.split("\\")[-1]  # get file name
                new_path = target_destination + "\\" + file_name  # create a new path

                if os.path.exists(new_path):
                    print("copy error file {0} already exists...!".format(file_name))
                    pass

                try_execute(copy_item, path, new_path)  # copy file from path to new_path

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
