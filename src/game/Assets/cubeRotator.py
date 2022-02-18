from editor.p3d.pModBase import PModBase
from editor.assetsHandler import AssetsHandler as ResourceHandler


class CubeRotator(PModBase):
    def __init__(self, *args, **kwargs):
        PModBase.__init__(self, *args, **kwargs)
        
        self.rotateSpeed = -11
        self.vagina = "hips"
        self.fuck = ""

        self.accept("a", self.rc, [5])

    def rc(self, a):
        print("cube rotator speed {0}".format(a))
        
    def on_start(self):
        self.__cube = self.le.find("cube.fbx")
    
    def on_update(self):
        self.rotate_cube()

    def on_late_update(self):
        pass
        
    def on_stop(self):
        pass
    
    def rotate_cube(self):
        h = self.__cube.getH()
        h += self.rotateSpeed * globalClock.getDt()
        if h > 360:
            h = 0
        self.__cube.setH(h)
