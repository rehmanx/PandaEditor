import editor.constants as constant
from editor.p3d import pModBase
from editor.utils.exceptionHandler import try_execute
from direct.showbase.ShowBase import taskMgr


class PToolBase(pModBase.PModBase):
    def __init__(self, *args, **kwargs):
        pModBase.PModBase.__init__(self, *args, **kwargs)
        self._sort = 2

        self.__tab_request = None

        self.add_discarded_attr("_PToolBase__tab_request")

    def enable(self):
        res = try_execute(self.on_enable)
        if res is False:
            constant.obs.trigger("EdToolExecutionFailed", self._name)
            return

        if self._task in taskMgr.getAllTasks():
            taskMgr.remove(self._task)
            self._task = None

        self._task = taskMgr.add(self.update, '%sEdToolUpdateTask-' % self._name, sort=self._sort)

    def update(self, task):
        res = try_execute(self.on_update)
        if res is True:
            return task.cont
        else:
            # remove task
            taskMgr.remove(self._task)
            self._task = None
            constant.obs.trigger("EdToolExecutionFailed", self._name)

    def on_enable(self):
        pass
    
    def on_update(self):
        pass

    def has_tab_request(self):
        return self.__tab_request is not None

    def get_tab_request(self):
        return self.__tab_request

    def request_unique_tab(self, menu=None, func=None):
        self.__tab_request = (menu, func)
