# -*- coding: utf-8 -*-
"""
Created on Fri Nov 16 10:45:05 2018

@author: mhunter2
"""

from psana import *
ds = DataSource('exp=cxils8717:run=71:smd')
energy = Detector('EBeam')
for evt in ds.events():
    eval = energy(evt
#    if eval is None: continue
    evtId = evt.get(EventId)
    seconds= evt.Id.time()[0]
    print seconds, eval