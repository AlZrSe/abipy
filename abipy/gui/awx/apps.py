from __future__ import print_function, division

import abc
import wx

from .tools import PRINT, WARNING

__all__ = [
    "App",
]


class App(wx.App):
    __metaclass__ = abc.ABCMeta

    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)
        
        # This catches events when the app is asked to activate by some other process
        self.Bind(wx.EVT_ACTIVATE_APP, self.OnActivate)

    def OnInit(self): 
        return True

    @property
    def appname(self):
        return self.__class__.__name__

    def __repr__(self):
        return "<%s at %s>" % (self.appname, id(self))

    def BringWindowToFront(self):
        try: # it's possible for this event to come when the frame is closed
            self.GetTopWindow().Raise()
        except:
            pass
        
    def OnActivate(self, event):
        # if this is an activate event, rather than something else, like iconize.
        if event.GetActive():
            self.BringWindowToFront()
        event.Skip()
    
    @abc.abstractmethod
    def MacOpenFile(self, filename):
        """Called for files droped on dock icon, or opened via finders context menu"""
        #if filename.endswith(".py"):
        #    return
        # Code to load filename.
        #PRINT("%s dropped on app %s" % (filename, self.appname)) 
        
    def MacReopenApp(self):
        """Called when the dock icon is clicked."""
        self.BringWindowToFront()

    #def MacNewFile(self):
    #    pass

    #def MacPrintFile(self, filepath):
    #    pass
