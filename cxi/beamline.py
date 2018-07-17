from hutch_python.utils import safe_load
from devices import Injector

# from cxi.db import cxi
from cxi.db import cxi_pulsepicker
from cxi.db import daq

try:
    def daq_repeat(seconds=10):
        while True:
            daq.begin(duration=seconds, wait=True)
            daq.end_run()

except KeyboardInterrupt:
    daq.end_run()

def daq_fixed_runs(runtime, darktime = 0):
#   print "Run time =" run_time
#   print "Dark time =" dark_time
    while True:
        if darktime > 0:
            cxi.pulsepicker.open(wait=True)
            daq.record(duration=run_time, wait=True)
            daq.end_run()

        else:
            cxi.pulsepicker.close(wait=True)
            daq.record(duration=darktime, wait=True)
            cxi.pulsepicker.open(wait=True)
            daq.record(duration=runtime,wait=True)
            daq.end_run()
            
with safe_load('PI1'):
    PI1 = {'injector_name': 'PI1 Injector',
           'coarseX_name': 'CXI:PI1:MMS:01',
           'coarseY_name': 'CXI:PI1:MMS:02',
           'coarseZ_name': 'CXI:PI1:MMS:03',
           'fineX_name': 'CXI:USR:MMS:01',
           'fineY_name': 'CXI:USR:MMS:02',
           'fineZ_name': 'CXI:USR:MMS:03'}
    injector_PI1 = Injector(**PI1)
    
with safe_load('PI2'):
    PI2 = {'injector_name': 'PI2 Injector',
           'coarseX_name': 'CXI:PI2:MMS:01',
           'coarseY_name': 'CXI:PI2:MMS:02',
           'coarseZ_name': 'CXI:PI2:MMS:03',
           'fineX_name': 'CXI:PI2:MMS:04',
           'fineY_name': 'CXI:PI2:MMS:05',
           'fineZ_name': 'CXI:PI2:MMS:06'}
    injector_PI2 = Injector(**PI2)
    
with safe_load('PI3'):
    PI3 = {'injector_name': 'PI3 Injector',
           'coarseX_name': 'CXI:PI3:MMS:01',
           'coarseY_name': 'CXI:PI3:MMS:02',
           'coarseZ_name': 'CXI:PI3:MMS:03',
           'fineX_name': 'CXI:PI3:MMS:04',
           'fineY_name': 'CXI:PI3:MMS:05',
           'fineZ_name': 'CXI:PI3:MMS:06'}
    injector_PI3 = Injector(**PI3)    

