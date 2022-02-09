import math
import panda3d.core as pm
import random

from editor.p3d.pModBase import PModBase
from editor.utils import Math
from editor.assetsHandler import AssetsHandler as ResourceHandler


class CharacterController(PModBase):
    def __init__(self, *args, **kwargs):
        PModBase.__init__(self, *args, **kwargs)
        self._sort = 2

        self.walkSpeed = 300
        self.runSpeed = 60
        self.turnSpeed = 80
        self.strafeSpeed = 20

        self.velocity = pm.Vec3(0, 0)
        self.moveInput =  pm.Vec2(0, 0)

        self.shouldMove = False
        self.isMoving = False

    # on_start method is called once
    def on_start(self):
        self.input = self.le.get_mod_instance("InputManager")
        self.player = self.le.find("cube.fbx")

        '''
        for i in range(5500):
            x = self.le.duplicate_object([ResourceHandler.ASSETS_3D["box.egg.pz"]])
            x[0].reparent_to(self.le.runtime_np_parent)
            x[0].setScale(10)

            x[0].setPos(random.randrange(800), random.randrange(800), random.randrange(800))
        '''

    # update method is called every frame
    def on_update(self):
        self.GetInput()
        self.Move()
        self.Turn()
        
    def GetInput(self):
        self.moveInput.y = 0
        self.moveInput.x = 0
        
        if self.input.key_map["w"] > 0:
            self.moveInput.y = 1
        elif self.input.key_map["s"] > 0:
            self.moveInput.y = -1

        if self.input.key_map["a"] > 0:
            self.moveInput.x = -1
        elif self.input.key_map["d"] > 0:
            self.moveInput.x = 1

        self.shouldMove = abs(self.moveInput.x) > 0 or abs(self.moveInput.y) > 0

    def Move(self):
        if self.shouldMove:
            moveDirection = pm.Vec3(self.moveInput.x, self.moveInput.y, 0)
            moveDirection.normalized()
            self.velocity = (moveDirection * self.walkSpeed) * globalClock.getDt()
            self.player.setPos(self.player, self.velocity)

    def Turn(self):
        input = self.input.mouseInput.x
        if abs(input) > 0:
            turn = (input * self.turnSpeed) * globalClock.getDt()
            turn += self.player.getH() 
            turn = Math.clamp_angle(turn, -360, 360)
            self.player.setH(turn)

    def Jump(self):
        pass
        
