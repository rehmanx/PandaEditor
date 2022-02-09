import editor.constants as constant
from editor.p3d.singleTask import SingleTask
from editor.utils.exceptionHandler import try_execute
from editor.utils import EdProperty


def execute(*args, **kwargs):
    foo = args[len(args) - 1]
    args = args[:len(args) - 1]
    try_execute(foo, *args, **kwargs)


def stop_execution():
    constant.obs.trigger("ProjectEvent", "SwitchEdState", 0)


class PModBase(SingleTask):
    def __init__(self, *args, **kwargs):
        SingleTask.__init__(self, *args, **kwargs)

        self.le = args[1]
        self.__enabled = True
        self.__user_properties = []
        self.__properties = []
        self.__initialized = True
        self.__are_sub_objects_valid = False

        # default sort value for user modules
        self._sort = 3

        # to be discarded attributes
        self.__discarded_attrs = ["tag",  # tag is defined base class "Object"
                                  "_MSGRmessengerId",
                                  "_sort",
                                  "_PModBase__enabled",
                                  "_PModBase__user_properties",
                                  "_PModBase__properties",
                                  "_PModBase__initialized",
                                  "_PModBase__are_sub_objects_valid",
                                  "_PModBase__discarded_attrs"]

    def Start(self, sort=None, priority=None):
        res = try_execute(super(PModBase, self).Start, sort, priority)
        if res is not True:
            stop_execution()
            return False

    def Update(self, task):
        res = try_execute(super(PModBase, self).Update, task)
        if res is True:
            return task.cont
        else:
            stop_execution()
            return False

    def LateUpdate(self, task):
        res = try_execute(super(PModBase, self).LateUpdate, task)
        if res is True:
            return task.cont
        else:
            stop_execution()
            return False

    def Stop(self):
        res = try_execute(super(PModBase, self).Stop)
        if res is not True:
            stop_execution()
            return False

    def get_displayable_attrs(self):
        attrs = []
        for item in self.__dict__.keys():
            if item[0] == "_" or self.__discarded_attrs.__contains__(item) or hasattr(PModBase("", None), item):
                continue
            attrs.append(item)

        return attrs

    def get_savable_atts(self):
        attrs = []
        for name, val in self.__dict__.items():
            if self.__discarded_attrs.__contains__(name) or hasattr(PModBase("", None), name):
                continue
            attrs.append((name, val))
        return attrs

    def get_discarded_attrs(self):
        return self.__discarded_attrs

    def get_attr(self, attr):
        if attr in self.__dict__.keys():
            return self.__dict__[attr]
        return None

    def get_properties(self):
        self.__properties = []

        # an error catch here is necessary, if for example the user
        # has not properly initialized PModBase base class

        try:
            for attr in self.get_displayable_attrs():
                name = attr
                value = getattr(self, name)
                _type = type(value)
                prop = EdProperty.FuncProperty(name=name, value=value, obj=self)
                self.__properties.append(prop)

        except AttributeError as e:
            self.__properties = []
            print(e)

        self.__properties.extend(self.__user_properties)

        return self.__properties

    def is_discarded_attr(self, name):
        if name in self.__discarded_attrs:
            return True
        return False

    def add_property(self, prop):
        if not self.__user_properties.__contains__(prop):
            self.__user_properties.append(prop)

    def add_discarded_attr(self, attr: str):
        if not self.__discarded_attrs.__contains__(attr):
            self.__discarded_attrs.append(attr)

    def set_enabled(self, val: bool):
        self.__enabled = val

    def is_enabled(self):
        return self.__enabled

    def are_sub_objects_valid(self):
        try:
            sub_objs = self.get_sub_objects()
            for obj in sub_objs:
                y = obj.__initialized
        except Exception as ex:
            print("sub objects validation failed for object " + self.get_name())
            print(ex)
            self.__are_sub_objects_valid = False
            return False

        # print("sub objects validated for object " + self.get_name())
        self.__are_sub_objects_valid = True
        return True

    def get_sub_objects(self):
        return []

    def update_properties(self):
        for prop in self.__properties:
            name = prop.get_name()
            if hasattr(self, name):
                value = getattr(self, name)
                prop.set_value(value)

    def accept(self, event, method, extra_args=[]):
        if type(extra_args) is not list:
            print("unable to accept event {0} from {1} argument extra_args must be of type list".format(
                event, self.get_name()))
            return

        xx = extra_args.copy()
        xx.append(method)
        super(SingleTask, self).accept(event, execute, extraArgs=xx)
