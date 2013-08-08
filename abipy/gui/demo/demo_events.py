#!/usr/bin/env python
import os
import abipy
import abipy.data

import abipy.gui.wxapps as wxapps

filenames = [os.path.join(abipy.data.dirpath, f) for f in  ["t01.about", "t02.about"]]
wxapps.wxapp_events(filenames).MainLoop()
