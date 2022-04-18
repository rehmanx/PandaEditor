import editor.constants as constant
import editor.utils as ed_utils
from direct.showbase.DirectObject import DirectObject


def execute(*args, **kwargs):
    foo = args[len(args) - 1]
    args = args[:len(args) - 1]
    ed_utils.try_execute(foo, *args, **kwargs)


def stop_execution(is_ed_plugin):
    if is_ed_plugin:
        constant.obs.trigger("UserModuleEvent", "PluginExecutionFailed")
    else:
        constant.obs.trigger("ProjectEvent", "SwitchEdState", 0)


class PModBase(DirectObject):
    def __init__(self, *args, **kwargs):
        DirectObject.__init__(self)

        self._name = kwargs.pop("name", None)
        self._win = kwargs.pop("win", None)
        self._mouse_watcher_node = kwargs.pop("mouse_watcher_node", None)
        self._le = kwargs.pop("level_editor", None)
        self._render = kwargs.pop("render", None)
        self._render2d = kwargs.pop("render2d", None)
        self._game_cam = kwargs.pop("game_cam", None)

        self._task = None
        self._late_task = None
        self._sort = 2  # default sort value for user modules
        self._late_update_sort = -1

        self._enabled = True  # is this module enabled
        self._initialized = True
        self._error = False  # set this to true if there is an error
        self._editor_plugin = False  # is it editor plugin ?

        self._user_properties = []
        self._hidden_properties = []
        self._properties = []

        # to be discarded variables
        # these variables will not be saved
        self._discarded_attrs = [
            "_MSGRmessengerId",

            "_name",
            "_le",
            "_render",
            "_mouse_watcher",
            "_win",

            "_task",
            "_late_task",
            "_sort",
            "_late_update_sort",

            "_enabled",
            "_initialized",
            "_error",
            "_editor_plugin",

            "_user_properties",
            "_properties",

            "_discarded_attrs"]

    def is_ed_plugin(self, value: bool):
        self._editor_plugin = value

    def start(self, sort=None, late_update_sort=None, priority=None):
        if sort is not None:
            self._sort = sort

        if late_update_sort is not None:
            self._late_update_sort = late_update_sort

        def _start():
            self.on_start()

            # start the object's update loop
            if not self.is_running(0):
                self._task = taskMgr.add(self.update,
                                         "{0} Update".format(self._name),
                                         sort=self._sort,
                                         priority=priority)

            # start the object's late update loop
            if not self._editor_plugin and not self.is_running(1):
                self._late_task = taskMgr.add(self.late_update,
                                              "{0} LateUpdate".format(self._name),
                                              sort=self._late_update_sort,
                                              priority=None)

        res = ed_utils.try_execute(_start)
        if res is not True:
            stop_execution(self._editor_plugin)
            return False

    def on_start(self):
        pass

    def update(self, task):
        res = ed_utils.try_execute(self.on_update)
        if res is True:
            return task.cont
        else:
            stop_execution(self._editor_plugin)
            return False

    def on_update(self):
        pass

    def late_update(self, task):
        res = ed_utils.try_execute(self.on_late_update)
        if res is True:
            return task.cont
        else:
            stop_execution(self._editor_plugin)
            return False

    def on_late_update(self):
        pass

    def stop(self):
        # remove the object's task from the task manager
        if self._task in taskMgr.getAllTasks():
            taskMgr.remove(self._task)
            self._task = None

        if self._late_task in taskMgr.getAllTasks():
            taskMgr.remove(self._late_task)
            self._late_task = None

        self.on_stop()

    def on_stop(self):
        pass

    def is_running(self, task=0):
        """ Return True if the object's task can be found in the task manager, False otherwise"""

        if task == 0:
            return self._task in taskMgr.getAllTasks()
        elif task == 1:
            return self._late_task in taskMgr.getAllTasks()

        return False

    def get_savable_atts(self):
        attrs = []
        for name, val in self.__dict__.items():
            if self._discarded_attrs.__contains__(name) or hasattr(PModBase("", None), name):
                continue
            attrs.append((name, val))

        return attrs

    def get_attr(self, attr):
        if attr in self.__dict__.keys():
            return self.__dict__[attr]
        return None

    def get_properties(self):
        self._properties = []

        for name, value in self.get_savable_atts():
            if name in self._hidden_properties:
                # hidden variables should be ignored
                continue

            if name[0] == "_":
                # private variables should be ignored
                continue

            prop = ed_utils.EdProperty.ObjProperty(name=name, value=value, _type=type(value), obj=self)
            self._properties.append(prop)

        self._properties.extend(self._user_properties)

        return self._properties

    def is_discarded_attr(self, name):
        if name in self._discarded_attrs:
            return True
        return False

    def add_property(self, prop):
        if not self._user_properties.__contains__(prop):
            self._user_properties.append(prop)

    def add_hidden_variable(self, prop):
        if not self._hidden_properties.__contains__(prop):
            self._hidden_properties.append(prop)

    def add_discarded_attr(self, attr: str):
        if not self._discarded_attrs.__contains__(attr):
            self._discarded_attrs.append(attr)

    def update_properties(self):
        for prop in self._properties:
            name = prop.get_name()
            if hasattr(self, name):
                value = getattr(self, name)
                prop.set_value(value)

    def accept(self, event, method, extra_args=None):
        if extra_args is None:
            extra_args = []
        if type(extra_args) is not list:
            print("unable to accept event {0} from {1} argument extra_args must be of type list".format(
                event, self._name))
            return

        xx = extra_args.copy()
        xx.append(method)
        super(PModBase, self).accept(event, execute, extraArgs=xx)
