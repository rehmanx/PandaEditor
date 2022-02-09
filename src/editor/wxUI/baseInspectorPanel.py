import wx
import editor.wxUI.wxCustomProperties as wxProperty

from wx.lib.scrolledpanel import ScrolledPanel
from panda3d.core import Vec2, Vec3, LColor, LPoint3f, LVecBase3f
from editor.wxUI.wxFoldPanel import WxFoldPanelManager
from editor.colourPalette import ColourPalette as Colours


class BaseInspectorPanel(ScrolledPanel):
    def __init__(self, parent, *args, **kwargs):
        ScrolledPanel.__init__(self, parent, *args, **kwargs)
        self.SetBackgroundColour(Colours.NORMAL_GREY)
        self.SetWindowStyleFlag(wx.BORDER_SUNKEN)

        self.wxMain = parent

        self._is_active = True
        self.selected_object = None
        self._layout_auto = False

        self.property_and_type = {
            int: wxProperty.IntProperty,  # -1
            float: wxProperty.FloatProperty,  # -2
            str: wxProperty.StringProperty,  # -3
            bool: wxProperty.BoolProperty,  # -4

            # list: wxProperty.ContainerProperty,  # -5

            Vec3: wxProperty.Vector3Property,  # -6
            Vec2: wxProperty.Vector2Property,  # -7
            LColor: wxProperty.ColorProperty,  # -8

            LPoint3f: wxProperty.Vector3Property,
            LVecBase3f: wxProperty.Vector3Property,

            "label": wxProperty.LabelProperty,  # -9
            "choice": wxProperty.EnumProperty,  # -10
            "button": wxProperty.ButtonProperty,  # -11
            "slider": wxProperty.SliderProperty,  # -12
            "space": wxProperty.EmptySpace,  # -13

            "static_box": wxProperty.StaticBox,  # -14
        }
        self.property_and_name = {}

        # offset
        self.offset = 8  #

        # set up a WxFoldPanelManager
        self.fold_manager = WxFoldPanelManager(self)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.fold_manager, 0, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.Bind(wx.EVT_SIZE, self.on_event_size)

    def enable(self):
        print("base inspector panel enabled")
        """on enbale is called as soon as this panel is added in editor"""
        if self._layout_auto and self.selected_object is not None:
            self.layout_object_properties(self.selected_object)

    def disable(self):
        print("base inspector panel disable")
        """on disable is called as soon as this panel is closed in editor"""
        pass

    def remove(self):
        print("base inspector panel removed")
        """on remove is called as soon as this panel is removed permanently"""
        pass

    def layout_object_properties(self, obj):
        self.reset()
        self.selected_object = obj
        self._is_active = True

        properties = obj.get_properties()

        # create a fold panel
        name = self.selected_object.get_name()
        name = name[0].upper() + name[1:]
        fold_panel = self.fold_manager.add_panel(name)

        for prop in properties:
            prop.validate()
            if prop.is_valid:
                self.create_wx_prop_object(prop, fold_panel, self.offset)
            else:
                print("{0} property validation failed".format(prop.name))

        # fold_panel.update_controls(False)
        fold_panel.update_controls()
        self.fold_manager.expand(fold_panel)
        self.sizer.Layout()

    def create_wx_prop_object(self, _property, parent, hoffset):
        wx_property = None

        if self.property_and_type.__contains__(_property.get_type()):
            wx_property = self.property_and_type[_property.get_type()]
            wx_property = wx_property(parent, _property, h_offset=hoffset)

            # wx_property.
            wx_property.create_control()
            wx_property.on_control_created()

            self.property_and_name[_property.get_name()] = wx_property
            parent.add_control(wx_property)

        return wx_property

    def update_properties_panel(self, obj=False):
        if obj:
            self.selected_object = obj

        for key in self.property_and_name.keys():
            wx_prop = self.property_and_name[key]

            if wx_prop.property.get_type() in ["button", "choice"]:
                continue

            if wx_prop._can_set_value:
                wx_prop.set_control_value(wx_prop.property.get_value())

    def refresh(self, obj=None):
        if obj is not None:
            self.selected_object = obj
        else:
            return

        self.layout_object_properties(self.selected_object)

    def reset(self):
        # TO:DO rewrite this function, fold_manager should clear all of its control
        # objects
        self.sizer.Clear(True)
        self.fold_manager = WxFoldPanelManager(self)
        self.sizer.Add(self.fold_manager, 1, wx.EXPAND)
        self.Refresh()

        self.selected_object = None
        self.property_and_name.clear()

    def get_object(self):
        if self.is_active():
            return self.selected_object
        return False

    def is_active(self):
        return self._is_active

    def set_active(self, val: bool):
        self._is_active = val

    def set_layout_auto(self, val: bool):
        self._layout_auto = val

    def set_object(self, obj):
        self.selected_object = obj

    def on_event_size(self, evt):
        self.fold_manager.SetMinSize((self.GetSize().x - 20, self.fold_manager.get_size_y()))
        evt.Skip()
