from __future__ import division, print_function

from pymatgen.io.abinitio.workflow import Workflow as pmWorkflow

class Workflow(pmWorkflow):
    """Hook used to add and test additional features to the pymatgen workflow."""

    #def wxshow_inputs(self):
    #    """Open a noteboox dysplaying the input files of the workflow."""
    #    from abipy.gui.wxapps import wxapp_showfiles
    #    wxapp_showfiles(dirpath=self.workdir, walk=True, wildcard="*.abi").MainLoop()

    #def wxshow_outputs(self):
    #    """Open a noteboox dysplaying the output files of the workflow."""
    #    from abipy.gui.wxapps import wxapp_showfiles
    #    wxapp_showfiles(dirpath=self.workdir, walk=True, wildcard="*.abo").MainLoop()

    #def wxshow_logs(self):
    #    """Open a noteboox dysplaying the log files of the workflow."""
    #    from abipy.gui.wxapps import wxapp_showfiles
    #    wxapp_showfiles(dirpath=self.workdir, walk=True, wildcard="*.log").MainLoop()

    #def wxbrowse(self):
    #    import abipy.gui.wxapps as wxapps
    #    wxapps.wxapp_listbrowser(dirpaths=self.workdir).MainLoop()

    #def wxshow_events(self):
    #    """Open a noteboox dysplaying the events (warnings, comments, warnings) of the workflow."""
    #    from abipy.gui.wxapps import wxapp_showevents
    #    wxapp_showfiles(dirpath=work.workdir, walk=True, wildcard="*.abo").MainLoop()
    #    AbinitEventsNotebookFrame(awx.Frame):
