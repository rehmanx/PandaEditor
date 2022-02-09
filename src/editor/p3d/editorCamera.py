from panda3d.core import Vec2, Vec3
from editor.p3d.camera import *
from editor.p3d.mouse import *


class EditorCamera(Camera):
    """Base editor camera class."""

    def __init__(self, *args, **kwargs):
        self.speed = kwargs.pop('speed', 1)
        kwargs['pos'] = kwargs.pop('pos', (-0, -0, 0))
        kwargs['style'] = kwargs.pop('style', CAM_USE_DEFAULT | CAM_VIEWPORT_AXES)
        Camera.__init__(self, *args, **kwargs)

        # Create mouse
        base.disableMouse()
        self.mouse = Mouse('EdCamMouse', *args, **kwargs)
        self.mouse.Start()

    def on_update(self):
        """
        Task to control mouse events. Gets called every frame and will update
        the scene accordingly.
        """
        Camera.on_update(self)
        # Return if no mouse is found or alt not down
        if not self.mouseWatcherNode.hasMouse() or MOUSE_ALT not in self.mouse.modifiers:
            return

        # ORBIT - If left mouse down
        if self.mouse.buttons[0]:
            self.Orbit(Vec2(self.mouse.dx * self.speed, self.mouse.dy * self.speed))

        # DOLLY - If middle mouse down
        elif self.mouse.buttons[1]:
            self.Move(Vec3(self.mouse.dx * self.speed, 0, -self.mouse.dy * self.speed))

        # ZOOM - If right mouse down
        elif self.mouse.buttons[2]:
            self.Move(Vec3(0, -self.mouse.dx * self.speed, 0))
