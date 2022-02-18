import panda3d.core as pm
from editor.p3d.object import Object
from editor.p3d.marquee import Marquee
from editor.p3d.mousePicker import MousePicker
from editor.constants import TAG_IGNORE, TAG_PICKABLE


class Selection(Object):
    BBOX_TAG = 'bbox'

    def __init__(self, *args, **kwargs):
        Object.__init__(self, *args, **kwargs)
        self.rootNp.set_python_tag(self.rootNp, TAG_IGNORE)

        self.append = False
        self.selected_nps = []

        # Create a marquee
        self.marquee = Marquee('marquee', *args, **kwargs)

        # Create node picker - set its collision mask to hit both geom nodes
        # and collision nodes
        bitMask = pm.GeomNode.getDefaultCollideMask() | pm.CollisionNode.getDefaultCollideMask()
        self.picker = MousePicker('picker', *args, fromCollideMask=bitMask, **kwargs)

    def get_nodepath_under_mouse(self):
        """
        Returns the closest node under the mouse, or None if there isn't one.
        """
        self.picker.on_update(None)
        picked_np = self.picker.GetFirstNodePath()
        return picked_np

    def get_selections(self):
        return self.selected_nps

    @staticmethod
    def get_pickable_np(np):
        pick_np = np.findNetPythonTag(TAG_PICKABLE)
        if not pick_np.isEmpty():
            pick_np = pick_np.findNetPythonTag(TAG_PICKABLE)
            return pick_np.getPythonTag(TAG_PICKABLE)
        return None

    def set_selected(self, nps):            
        self.selected_nps.clear()
        self.selected_nps = nps
        for np in self.get_selections():
            np.showTightBounds()
        
    def deselect(self, nps):
        pass
    
    def deselect_all(self):
        for np in self.get_selections():
            np.hideBounds()
        self.selected_nps.clear()
    
    def start_drag_select(self, append=False):
        """
        Start the marquee and put the tool into append mode if specified.
        """
        if self.marquee.mouseWatcherNode.hasMouse():
            self.append = append
            self.marquee.Start()

    def stop_drag_select(self):
        """
        Stop the marquee and get all the node paths under it with the correct
        tag. Also append any node which was under the mouse at the end of the
        operation.
        """
        self.marquee.Stop()

        # Find all node paths below the root node which are inside the marquee
        # AND have the TAG_PICKABLE tag.

        if self.append:
            pass
        else:
            # deselect last selected nps
            for np in self.selected_nps:
                np.hideBounds()
            self.selected_nps = []

        for pick_np in self.rootNp.findAllMatches('**'):
            if pick_np is not None:
                if self.marquee.IsNodePathInside(pick_np) and pick_np.hasNetPythonTag(TAG_PICKABLE):

                    pickable_np = self.get_pickable_np(pick_np)
                    if pickable_np is not None and pickable_np not in self.selected_nps:
                        self.selected_nps.append(pickable_np)
                        pickable_np.showTightBounds()

        # Add any node path which was under the mouse to the selection.
        np = self.get_nodepath_under_mouse()
        if np is not None:
            np = self.get_pickable_np(np)

        if np is not None and np not in self.selected_nps:
            np.showTightBounds()
            self.selected_nps.append(np)

        return self.selected_nps

    def update(self):
        pass
