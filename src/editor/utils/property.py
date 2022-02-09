from editor.utils.exceptionHandler import try_execute


class Property:
    def __init__(self, name, value, _type=None):
        self.name = name
        self.val = value
        self._type = _type

        self.is_valid = False

        if _type is None:
            self._type = type(value)
        else:
            self._type = _type

    def get_name(self):
        return self.name

    def get_value(self):
        return self.val

    def get_type(self):
        return self._type

    def set_value(self, val):
        self.val = val

    def set_name(self, name: str):
        self.name = name

    def validate(self):
        if type(self.name) is not str:
            self.is_valid = False
            return
        self.is_valid = True


class FuncProperty(Property):
    def __init__(self, name, value, _type=None, obj=None, setter=None, getter=None):
        self.obj = obj
        self.setter = setter
        self.getter = getter

        super().__init__(name=name, value=value, _type=_type)

    def validate(self):
        if hasattr(self.obj, self.name):
            self.is_valid = True
            return

        if self.setter is None or self.getter is None:
            self.is_valid = False

        super().validate()

    def get_object(self):
        return self.obj

    def get_getter(self):
        return self.getter

    def get_setter(self):
        return self.setter

    def get_value(self, *args, **kwargs):
        if hasattr(self.obj, self.name):
            return getattr(self.obj, self.name)

        elif self.get_getter() is not None:
            getter = self.get_getter()
            return getter()

        else:
            return self.val

    def set_value(self, val, *args, **kwargs):
        if hasattr(self.obj, self.name):
            setattr(self.obj, self.name, val)

        elif self.get_getter() is not None:
            try_execute(self.setter, val, *args, **kwargs)

        else:
            self.val = val


class EmptySpace(Property):
    def __init__(self, x, y):
        super().__init__(name="", value=None, _type="space")

        self.x = x  # horizontal spacing
        self.y = y  # vertical spacing

    def validate(self):
        if type(self.x) is not int or type(self.y) is not int:
            self.is_valid = False
            return

        super().validate()


class Label(Property):
    def __init__(self, name, is_bold=False, text_color=None):
        super().__init__(name=name, value=None, _type="label")

        self.is_bold = is_bold
        self.text_color = text_color

    def validate(self):
        if type(self.is_bold) is not bool:
            self.is_valid = False
            return
        super().validate()


class ListProperty(FuncProperty):
    class ListItemInfo:
        def __init__(self, name, index):
            self.name = name
            self.index = index

    def __init__(self, name, value, obj, lst_item_info):
        FuncProperty.__init__(self, name, value, list, obj)
        self.list_item_info = lst_item_info

    def set_value(self, val, *args, **kwargs):
        list_obj = getattr(self.obj, self.list_item_info.name)
        list_obj[self.list_item_info.index] = val

    def get_value(self):
        list_obj = getattr(self.obj, self.list_item_info.name)
        return list_obj[self.list_item_info.index]

    def get_list_item_info(self):
        return self.list_item_info


class ButtonProperty(Property):
    def __init__(self, name, func):
        self.func = func

        super().__init__(name=name, value=None)

        self._type = "button"

    def validate(self):
        if self.func is None:
            self.is_valid = False
            return

        super().validate()

    def get_func(self):
        return self.func

    def execute(self):
        try_execute(self.func)


class ChoiceProperty(FuncProperty):
    def __init__(self, name, choices, value=0, obj=None, setter=None, getter=None):
        self.choices = choices

        super().__init__(name=name, value=value, _type="choice", obj=obj, setter=setter, getter=getter)

    def validate(self):
        # choices must be greater than 1
        if len(self.choices) <= 1:
            self.is_valid = False
            return

        # all choices must be string
        for item in self.choices:
            if type(item) is not str:
                self.is_valid = False
                return

        # value must be int
        if type(self.val) is not int:
            self.is_valid = False
            return

        # here obj is None check (obj has priority over setter/getter) for getter and setter
        if self.obj is not None:
            self.is_valid = True
            return

        if self.setter is None or self.getter is None:
            self.is_valid = False
            return

        super().validate()

    def get_choices(self):
        return self.choices

    def set_value(self, val: int, *args, **kwargs):
        if type(val) is not int:
            print("error in edUI.ChoiceProperty.set_value arg val must be of type int")
            return

        super(ChoiceProperty, self).set_value(val, *args, **kwargs)


class Slider(FuncProperty):
    def __init__(self, name, value, min_value, max_value, obj=None, setter=None, getter=None):
        FuncProperty.__init__(self, name=name, obj=obj, value=value, setter=setter, getter=getter)

        self._type = "slider"

        self.min_value = min_value
        self.max_value = max_value

        if self.is_valid:
            if self.value < self.min_value:
                self.value = self.min_value
            if self.value > self.max_value:
                self.value = self.max_value

    def validate(self):
        # value must be int
        if type(self.val) is not int:
            self.is_valid = False
            return

        # min max range should also be int
        if type(self.min_value) is not int or type(self.max_value) is not int:
            self.is_valid = False
            return

        # here if obj is None check (obj has priority over setter/getter) for getter and setter
        if self.obj is not None:
            self.is_valid = True
            return

        if self.setter is None or self.getter is None:
            self.is_valid = False
            return

        super().validate()


class StaticBox(Property):
    def __init__(self, name, controls=None):
        Property.__init__(self, name, value=None, _type="static_box")

        self.controls = controls
