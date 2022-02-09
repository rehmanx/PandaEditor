from direct.showbase import ShowBase as SB
from panda3d.core import NodePath, Camera, OrthographicLens, PGTop, BitMask32
from editor.p3d import EditorCamera, CAM_USE_DEFAULT, CAM_DEFAULT_STYLE, CAM_VIEWPORT_AXES


class ShowBase(SB.ShowBase):
    def __init__(self, ed_wx_win):
        SB.ShowBase.__init__(self)

        self.ed_wx_win = ed_wx_win
        
        self.forcedAspectWins = []

        self.edRender = None
        self.edRender2d = None
        self.ed_camera = None

    def finish_init(self):
        self.setup_editor_win()
        self.setup_editor_window()
        
        # Add the editor window, camera and pixel 2d to the list of forced
        # aspect windows so aspect is fixed when the window is resized.
        self.forcedAspectWins = []
        self.forcedAspectWins.append((self.win, self.ed_camera, self.edPixel2d))
        
        # turn on per pixel lightning
        self.edRender.setShaderAuto()
                                      
    def setup_editor_win(self):
        self.ed_wx_win.Initialize(useMainWin=True)
        
    def setup_editor_window(self):
        # clear existing/default 2d and 3d display regions
        self.dr = self.cam.node().getDisplayRegion(0)
        self.dr.setClearColorActive(True)
        self.dr.setClearColor(self.getBackgroundColor())
        self.dr.setActive(False)
        self.dr.setSort(20)

        self.dr2d = self.cam2d.node().getDisplayRegion(0)
        self.dr2d.setActive(False)
        self.dr2d.setSort(21)


        # create editor root node behind render node so we can keep editor only
        # nodes out of the scene
        self.edRender = NodePath('edRender')
        self.render.reparentTo(self.edRender)

        self.ed_win = self.ed_wx_win.GetWindow()

        # Setup mouse watcher for the editor window
        buttonThrowers, pointerWatcherNodes = self.setupMouseCB(self.ed_win)
        self.edMouseWatcher = buttonThrowers[0].getParent()
        self.edMouseWatcherNode = self.edMouseWatcher.node()
        self.edMouseWatcherParent = self.edMouseWatcher.getParent()

        # create new 3d display region
        self.edDr = self.ed_win.makeDisplayRegion(0, 1, 0, 1)
        self.edDr.setClearColorActive(True)
        self.edDr.setClearColor((0.6, 0.6, 0.6, 1.0))

        # create new 2d display region
        self.edDr2d = self.win.makeDisplayRegion()
        self.edDr2d.setSort(20)
        self.edDr2d.setActive(True)
        
        # create a new 2d scene graph
        self.edRender2d = NodePath('edRender2d')
        self.edRender2d.setDepthTest(False)
        self.edRender2d.setDepthWrite(False)
        
        # create a 2d camera for 2d display region
        myCamera2d = NodePath(Camera('myCam2d'))
        lens = OrthographicLens()
        lens.setFilmSize(2, 2)
        lens.setNearFar(-1000, 1000)
        myCamera2d.node().setLens(lens)
        
        myCamera2d.reparentTo(self.edRender2d)
        self.edDr2d.setCamera(myCamera2d)

        xsize, ysize = self.getSize()
        # aspectRatio = self.getAspectRatio()
        self.edPixel2d = self.edRender2d.attachNewNode(PGTop('myAspect2d'))
        self.edPixel2d.setPos(-1, 0, 1)
        if xsize > 0 and ysize > 0:
            self.edPixel2d.setScale(2.0 / xsize, 1.0, 2.0 / ysize)
        # myAspect2d.setScale(1.0 / aspectRatio, 1.0, 1.0)
        self.edPixel2d.node().setMouseWatcher(self.mouseWatcherNode)
        
        # create a new 3d camera
        self.ed_camera = EditorCamera(
            'camera',
            style=CAM_VIEWPORT_AXES,
            speed=0.5,
            pos=(300, 150+300, 100+300),
            rootNp=self.edRender,
            rootP2d=self.edPixel2d,
            win=self.ed_win,
            mouseWatcherNode=self.edMouseWatcherNode
        )
        self.ed_camera.reparentTo(self.edRender)
        self.ed_camera.Start()
        # self.ed_camera.node().setCameraMask(BitMask32.bit(1))
        self.edDr.setCamera(self.ed_camera)

    def update_aspect_ratio(self):
        for win, cam, pixel2d, in self.forcedAspectWins:
            aspectRatio = self.getAspectRatio(win)
            cam.node().getLens().setAspectRatio(aspectRatio)

            # Fix pixel2d scale for new window size
            # Temporary hasattr for old Pandas
            if not hasattr(win, 'getSbsLeftXSize'):
                pixel2d.setScale(2.0 / win.getXSize(), 1.0, 2.0 / win.getYSize())
            else:
                pixel2d.setScale(2.0 / win.getSbsLeftXSize(), 1.0, 2.0 / win.getSbsLeftYSize())

    def windowEvent(self, *args, **kwargs):
        """
        Overridden so as to fix the aspect ratio of the editor camera and
        editor pixel2d.
        """
        SB.ShowBase.windowEvent(self, *args, **kwargs)
        self.update_aspect_ratio()
