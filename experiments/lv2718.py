from ophyd import EpicsSignal, EpicsSignalRO
from ophyd import EpicsMotor
from pcdsdevices.device_types import IMS, Newport
from cxi.db import cxi_pulsepicker as pp, seq
from cxi.db import bp, bpp, bps
import logging
import numpy as np
import time

logger = logging.getLogger(__name__)

class User:
    #diode_x = Newport('CXI:BER:MCN:06', name='diode_x')
    #diode_y = Newport('CXI:BER:MCN:06', name='diode_y')
    crystal_th = Newport('CXI:BER:MCN:03', name='crystal_th')
    chamber_z = Newport('CXI:BER:MCN:04', name='chamber_z')
    chamber_x = Newport('CXI:BER:MCN:05', name='chamber_x')
    sample_x = Newport('CXI:BER:MCN:06', name='sample_x')
    sample_y = Newport('CXI:BER:MCN:07', name='sample_y')
    sample_z = Newport('CXI:BER:MCN:08', name='sample_z')
    pp_delay = EpicsSignal('CXI:R48:EVR:41:TRIG0:TDES', name='pp_delay')

    def imprint_burst(self, motor1, start1, stop1, motor2, start2, stop2, steps):
        """
        Parameters:
        ----------
        motor1: str
            IMS Motor Base1 to Scan ('')

        start1: int/float
            Start value for the scan

        stop1: int/float
            Stop value for the scan

        motor2: str
            Motor Base2 to Scan ('')

        start2: int/float
            Start value for the scan

        stop2: int/float
            Stop value for the scan

        steps: int
            Number of steps in the scan

        """
        burst_shots = EpicsSignal('PATT:SYS0:1:MPSBURSTCNTMAX')
        burst_request = EpicsSignal('PATT:SYS0:1:BYKIKCTRL')
        if burst_shots.get() != 1:
            logger.info('setting burst shots request to 1')
            burst_shots.put(1)

        #seq_run = EpicsSignal('ECS:SYS0:5:PLYCTL')
        time.sleep(0.2)
        steps1 = np.linspace(start1, stop1, steps)
        steps2 = np.linspace(start2, stop2, steps)
        for step1, step2 in zip(steps1, steps2):
            logger.info(f'Setting %s to %0.3d and %s to %0.3d', motor1, step1, motor2, step2)
            motor1.mv(step1)
            motor2.mv(step2)
            motor1.wait()
            motor2.wait()
            time.sleep(0.2)
            logger.info(f'Motors at desired positions %s at %0.3d, %s at %0.3d. Requesting burst...', motor1.name, motor1.position, motor2.name, motor2.position)
            burst_request.put(1)
            time.sleep(0.2)

        logger.info('Scan Finished')

 
    def pp_delay_scan(self, start=1600, stop=9501600, steps=96, sleep_time=1):
        def step_sleep(detectors, motor, step):
            yield from bps.one_1d_step(detectors, motor, step)
            yield from bps.sleep(sleep_time)

        yield from bp.scan([seq],self.pp_delay,start,stop,steps,per_step=step_sleep)


    @bpp.daq_step_scan_decorator
    def daq_pp_delay_scan(self, start=1600, stop=9501600, steps=96, sleep_time=1):
        def step_sleep(detectors, motor, step):
            yield from bps.one_1d_step(detectors, motor, step)
            yield from bps.sleep(sleep_time)
  
        yield from bp.scan([seq],self.pp_delay,start,stop,steps,per_step=step_sleep)
