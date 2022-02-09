import math
from editor.p3d.pModBase import PModBase
from panda3d.core import Vec3, Vec2
from editor.utils import Math


class ThirdPersonCam(PModBase):
    def __init__(self, *args, **kwargs):
        PModBase.__init__(self, *args, **kwargs)
                
        self.targetPos = Vec3(0, 0, 0)
        self.debugMode = False
        self.zoom = 0
        
        # movement settings
        self.targetPosOffset = Vec3(0, 0, 90)
        self.lookSmooth = 100
        self.distanceToTarget = 150
        self.zoomSmooth = 100
        self.minZoom = 150
        self.maxZoom = 250
        
        # orbit settings
        self.xRotation = 0.0
        self.yRotation = 0.0
        self.maxXRotation = 0.0
        self.minXRotation = 0.0
        self.orbitSmooth = 50.0
        self.lockXOrbit = False
        self.lockYOrbit = False

        self.alist = ["apples, oranges"]

        self.fuck = ""

        # self.add_
    
    def on_start(self):
        self.target = self.le.find("cube.fbx") # find player
        self.input = self.le.get_mod_instance("InputManager") #
        self.cam = self.le.get_main_camera() # get main scene cam
        self.le.panda_app.set_mouse_mode("Absolute") # change mouse mode to absolute
        self.le.panda_app.auto_center_mouse(True)
        self.reset()

    def on_update(self):
        if self.input.key_map["r-up"] > 0:
            self.reset()

    def on_stop(self):
        self.le.panda_app.auto_center_mouse(False)

    def on_late_update(self):
        self.MoveToTarget()
        self.LookAtTarget()
        self.Orbit()
        self.Zoom()
        
    def reset(self):
        self.distanceToTarget = 150
        self.yRotation = 0
        self.MoveToTarget()
                    
    def MoveToTarget(self):        
        self.targetPos = self.target.getPos()
        self.targetPos.y -= self.distanceToTarget
        
        dist = self.target.getPos() - self.targetPos
        dist = dist.length()
        
        orbitRot = Vec3()
        # z rotation
        orbitRot.x = dist*math.cos(self.yRotation*(math.pi/180)) - dist*math.sin(self.yRotation*(math.pi/180)) 
        orbitRot.y = dist*math.sin(self.yRotation*(math.pi/180)) + dist*math.cos(self.yRotation*(math.pi/180)) 
        orbitRot.z = 0
        newPos = self.target.getPos() + self.targetPosOffset
        newPos += orbitRot
        self.cam.setPos(newPos)

    def LookAtTarget(self):
        self.cam.lookAt(self.target.getPos()+self.targetPosOffset)

    def Orbit(self):
        if not self.lockYOrbit:
            self.yRotation += self.input.mouseInput.x * self.orbitSmooth * globalClock.getDt()
            self.yRotation = Math.clamp_angle(self.yRotation, -360, 360)

        if not self.lockXOrbit:
            self.xRotation += self.input.mouseInput.y * self.orbitSmooth * globalClock.getDt()
            self.xRotation = Math.clamp_angle(self.xRotation, -360, 360)

    def Zoom(self):
        self.distanceToTarget += self.input.zoom * self.zoomSmooth * globalClock.getDt()

        if self.distanceToTarget < self.minZoom:
            self.distanceToTarget = self.minZoom

        elif self.distanceToTarget > self.maxZoom:
            self.distanceToTarget = self.maxZoom
