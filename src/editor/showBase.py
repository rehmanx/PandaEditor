from direct.showbase import ShowBase as SB
from panda3d.core import NodePath, Camera, OrthographicLens, PGTop, BitMask32
from editor.p3d import EditorCamera, CAM_USE_DEFAULT, CAM_DEFAULT_STYLE, CAM_VIEWPORT_AXES
from editor.constants import ED_GEO_MASK, GAME_GEO_MASK


class ShowBase(SB.ShowBase):
    def __init__(self, ed_wx_win):
        SB.ShowBase.__init__(self)

        self.ed_wx_win = ed_wx_win  # wx python window
        self.ed_win = None  # Panda3d editor window we will render into

        self.edRender = None
        self.edRender2d = None
        self.ed_camera = None

        self.player_camera = None

        self.dr = None  # default 3d display region
        self.dr2d = None  # default 2d display region
        self.edDr = None  # editor 3d display region that will replace default 3d display region
        self.edDr2d = None  # editor 2d display region that will replace default 2d display region
        self.ed_pixel_2d = None

        self.ed_mouse_watcher = None  # editor mouse watcher for editor display region
        self.ed_mouse_watcher_node = None

        self.forcedAspectWins = []

    def finish_init(self):
        self.init_editor_win()
        self.setup_editor_window()
        
        # Add the editor window, camera and pixel 2d to the list of forced
        # aspect windows so aspect is fixed when the window is resized.
        self.forcedAspectWins = []
        self.forcedAspectWins.append((self.win, self.ed_camera, self.ed_pixel_2d))
        
        # turn on per pixel lightning
        self.edRender.setShaderAuto()
                                      
    def init_editor_win(self):
        self.ed_wx_win.Initialize(useMainWin=True)
        
    def setup_editor_window(self):
        """set up an editor rendering, it included setting up 2d and 3d display regions,
        an editor scene graph and editor mouse watchers"""

        # clear existing / default 3d display regions
        self.dr = self.cam.node().getDisplayRegion(0)
        self.dr.setClearColorActive(True)
        self.dr.setClearColor(self.getBackgroundColor())
        self.dr.setActive(False)
        self.dr.setSort(20)

        # clear existing / default 2d display regions
        self.dr2d = self.cam2d.node().getDisplayRegion(0)
        self.dr2d.setActive(False)
        self.dr2d.setSort(21)

        # Setup mouse watcher for the editor window
        self.ed_win = self.ed_wx_win.GetWindow()
        button_throwers, pointer_watcher_nodes = self.setupMouseCB(self.ed_win)
        self.ed_mouse_watcher = button_throwers[0].getParent()
        self.ed_mouse_watcher_node = self.ed_mouse_watcher.node()
        ed_mouse_watcher_parent = self.ed_mouse_watcher.getParent()

        # ------------------ 2d rendering setup ------------------ #
        # create new 2d display region
        self.edDr2d = self.win.makeDisplayRegion()
        self.edDr2d.setSort(20)
        self.edDr2d.setActive(True)
        
        # create a new 2d scene graph
        self.edRender2d = NodePath('edRender2d')
        self.edRender2d.setDepthTest(False)
        self.edRender2d.setDepthWrite(False)
        
        # create a 2d camera for 2d display region
        my_camera_2d = NodePath(Camera('myCam2d'))
        lens = OrthographicLens()
        lens.setFilmSize(2, 2)
        lens.setNearFar(-1000, 1000)
        my_camera_2d.node().setLens(lens)
        
        my_camera_2d.reparentTo(self.edRender2d)
        self.edDr2d.setCamera(my_camera_2d)

        x_size, y_size = self.getSize()
        # aspectRatio = self.getAspectRatio()
        self.ed_pixel_2d = self.edRender2d.attachNewNode(PGTop('myAspect2d'))
        self.ed_pixel_2d.setPos(-1, 0, 1)
        if x_size > 0 and y_size > 0:
            self.ed_pixel_2d.setScale(2.0 / x_size, 1.0, 2.0 / y_size)
        # myAspect2d.setScale(1.0 / aspectRatio, 1.0, 1.0)
        self.ed_pixel_2d.node().setMouseWatcher(self.mouseWatcherNode)

        # ------------------ 3d rendering setup ------------------ #
        # create editor root node behind render node, so we can keep editor only
        # nodes out of the scene
        self.edRender = NodePath('edRender')
        self.render.reparentTo(self.edRender)

        # create new 3d display region
        self.edDr = self.ed_win.makeDisplayRegion(0, 1, 0, 1)
        self.edDr.setClearColorActive(True)
        self.edDr.setClearColor((0.6, 0.6, 0.6, 1.0))

        # create a new 3d camera
        self.ed_camera = EditorCamera(
            'camera',
            style=CAM_VIEWPORT_AXES,
            speed=0.5,
            pos=(300, 150+300, 100+300),
            rootNp=self.edRender,
            rootP2d=self.ed_pixel_2d,
            win=self.ed_win,
            mouseWatcherNode=self.ed_mouse_watcher_node
        )

        self.ed_camera.node().setCameraMask(ED_GEO_MASK)
        self.ed_camera.reparentTo(self.edRender)
        self.ed_camera.Start()
        self.set_ed_dr_camera(self.ed_camera)

    def setup_game_window(self):
        pass

    def set_ed_dr_camera(self, cam):
        """set scene display region's camera"""
        self.edDr.setCamera(cam)

    def set_player_camera(self, cam):
        self.player_camera = cam

    def update_aspect_ratio(self):
        for win, cam, pixel2d, in self.forcedAspectWins:
            aspect_ratio = self.getAspectRatio(win)
            cam.node().getLens().setAspectRatio(aspect_ratio)
            if self.player_camera is not None:
                self.player_camera.node().getLens().setAspectRatio(aspect_ratio)

            # Fix pixel2d scale for new window size
            # Temporary hasattr for old Pandas
            if not hasattr(win, 'getSbsLeftXSize'):
                pixel2d.setScale(2.0 / win.getXSize(), 1.0, 2.0 / win.getYSize())
            else:
                pixel2d.setScale(2.0 / win.getSbsLeftXSize(), 1.0, 2.0 / win.getSbsLeftYSize())

    def windowEvent(self, *args, **kwargs):
        """ Overridden to fix the aspect ratio of the editor camera and
        editor pixel2d."""
        SB.ShowBase.windowEvent(self, *args, **kwargs)
        self.update_aspect_ratio()
