import os
import traceback
from panda3d.core import Vec3


class Property:
    class ListItemInfo:
        def __init__(self, name, index):
            self.name = name
            self.index = index

    # TO:DO - different constructors
    def __init__(self, name, value=None, type=None, obj=None, setter=None, getter=None,
                 choices=None, list_item_info=None, initial_value=None):
        self.object = obj
        self.name = name
        self.val = value
        self.__initial_value__ = initial_value

        self.setter = setter
        self.getter = getter

        self.type = type

        self.choices = choices

        self.list_item_info = list_item_info
        self.is_list_item = self.list_item_info is not None

        self.is_valid = False

    def is_property_valid(self):
        return True

    def has_initial_value(self):
        return self.__initial_value__ is not None

    def get_object(self):
        return self.object

    def get_name(self):
        return self.name

    def get_initial_value(self):
        return self.__initial_value__

    def get_value(self):
        return self.val

    def get_type(self):
        return self.type

    def get_setter(self):
        return self.setter

    def get_getter(self):
        return self.getter

    def get_choices(self):
        return self.choices

    def get_list_item_info(self):
        return self.list_item_info

    def set_value(self, val):
        self.val = val

    def is_list_item(self):
        return self.is_list_item

    def is_valid(self):
        return self.is_valid


class ObjectData:
    def __init__(self, obj_name):
        self.obj_name = obj_name
        self.properties = []

    def add_property(self, prop):
        self.properties.append((prop.get_name(), prop.get_value()))


def get_dir_items(_dir, file_types=()):
    def get_items(dir_path=None):
        dir_files = os.listdir(dir_path)

        for file in dir_files:
            file_path = dir_path + "/" + file

            if os.path.isdir(file_path):
                get_items(file_path)
            elif os.path.isfile(file_path) and file_path.split(".")[-1] in file_types:
                items.append((file_path, file))

    items = []
    get_items(_dir)
    return items


def euler_from_hpr(hpr):
    euler = Vec3(hpr.y, hpr.z, hpr.x)
    return euler


def hpr_from_euler(euler):
    hpr = Vec3(euler.z, euler.x, euler.y)
    return hpr


# convert from one range to another
def convert_to_range(old_min, old_max, new_min, new_max, value):
    oldRange = old_max - old_min
    if oldRange == 0:
        newValue = new_min
        return newValue
    else:
        newRange = new_max - new_min
        newValue = (((value - old_min) * newRange) / oldRange) + new_min
        return newValue


# clamp angle to pi, -pi range
def clamp_angle(angle, min_val, max_val):
    if angle < -360:
        angle += 360
    if angle > 360:
        angle -= 360
    clamp = max(min(angle, max_val), min_val)
    return clamp


def clamp_value(val, min, max):
    n = (val - min) / (max - min)
    return n

'''
def try_execute_function(func, *args, **kwargs):
    obj_name = kwargs.pop("object_name", None)

    try:
        func(*args, **kwargs)
    except Exception as exc:
        tb_str = traceback.format_exception(etype=type(exc), value=exc, tb=exc.__traceback__)
        for x in tb_str:
            print(x)
        return False

    return True
'''


# -------------------------***----------------------------#
def add(val1, val2):
    return val1 + val2


def multiply(val1, val2):
    return val1 * val2


def difference(val1, val2):
    return val1 - val2


def divide(val1, val2):
    return val1 / val2


sign_to_func = {"-": difference,
                "+": add,
                "*": multiply,
                "/": divide}


def eval_str_eq(self, eq, res=None, sign=None, index_last_sign=0):
    i = 0
    for item in eq:
        if item in ("/", "*", "+", "-"):

            x = eq[:i]
            val = float(x)

            if res is None:
                res = val
            else:
                if sign_to_func.__contains__(sign):
                    func = sign_to_func[sign]
                    res = func(res, val)

            sign = item

            i += 1
            break
        index_last_sign += 1
        i += 1

    if len(eq[i:]) > 0:
        eval_str_eq(self, eq[i:], res, sign, index_last_sign)
        return

    func = sign_to_func[sign]
    res = func(res, float(eq))
    if hasattr(self, "result"):
        setattr(self, "result", res)


def eval_eq(mod, eq):
    if len(eq) > 0 and eq[0] in sign_to_func.keys() or eq[-1] in sign_to_func.keys():
        print("string equation evaluation failed -- !")
        return

    res = None
    try:
        val = float(eq)
        if hasattr(mod, "result"):
            setattr(mod, "result", val)
        res = True
    except Exception as ex:
        print("string equation evaluation failed -- !")
        print(ex)
        res = False
        pass

    if not res:
        try:
            eval_str_eq(mod, eq)
            res = True
        except Exception as ex:
            print("string equation evaluation failed -- !")
            print(ex)
            res = False
            pass

    return res


# -------------------------***----------------------------#
