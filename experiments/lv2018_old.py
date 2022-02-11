from ophyd import EpicsSignal, EpicsSignalRO
from ophyd import EpicsMotor
from pcdsdevices.device_types import IMS, Newport
from cxi.db import cxi_pulsepicker
import logging
import numpy as np
import time

logger = logging.getLogger(__name__)

class User:
    def imprint(self, pv_ims, start1, stop1, pv_newport, start2, stop2, steps):
        """
        Parameters:
        ----------
        pv_ims: str
            IMS Motor Base1 to Scan ('')

        start1: int/float
            Start value for the scan

        stop1: int/float
            Stop value for the scan

        pv_newport: str
            Motor Base1 to Scan ('')

        start2: int/float
            Start value for the scan

        stop2: int/float
            Stop value for the scan

        steps: int
            Number of steps in the scan

        """
        burst_shots = EpicsSignal('PATT:SYS0:1:MPSBURSTCNTMAX')
        burst_request = EpicsSignal('PATT:SYS0:1:MPSBURSTCTRL')
        if burst_shots.get() != 1:
            logger.info('setting burst shots request to 1')
            burst_shots.put(1)

        logger.info('setting pulse picker to burst mode')
        if cxi_pulsepicker.mode.get() != 3:
            logger.info('pulse picker not in burst mode, setting now')
            cxi_pulsepicker.burst()

        while cxi_pulsepicker.mode.get() != 3:
            time.sleep(0.1)

        try:
            motor1 = EpicsSignal(f'{pv_ims}')
            motor1_rbk = EpicsSignalRO(f'{pv_ims}.RBV')
            motor2 = Newport(prefix=pv_newport, name='newport motor')
        except Exception as e:
            logger.warning(f'Unable to get pv: {e}')
        time.sleep(0.2)
        steps1 = np.linspace(start1, stop1, steps)
        steps2 = np.linspace(start2, stop2, steps)
        for step1, step2 in zip(steps1, steps2):
            logger.info(f'Setting {pv_ims} to {step1} and {motor2.prefix} to {step2}')
            motor1.put(step1)
            motor2.mv(step2, wait=True)
            while abs(motor1_rbk.get() - step1) > 0.001:
                time.sleep(0.1)
            logger.info(f'Motors at desired positions {pv_ims} at {motor1_rbk.get()}, {motor2.prefix} at {motor2.get()} request burst')
            burst_request.put(1)

        logger.info('Scan Finished')

