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


