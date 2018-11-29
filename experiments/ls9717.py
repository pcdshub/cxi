import os
import time
import os.path
import logging
import subprocess
import epics
from ophyd import (FormattedComponent as FCpt, EpicsSignal, EpicsSignalRO,
                   Device, Component as Cpt)
from hutch_python.utils import safe_load
import pcdsdevices.utils as key_press
with safe_load('elog'):
    from cxi.db import elog

logger = logging.getLogger(__name__)

class User:
    """Generic User Object"""
    def __init__(self):
        self.sc1_mesh_raw = EpicsSignal(name='sc1_mesh_raw',
                                    read_pv='CXI:SC1:AIO:04:RAW:ANALOGIN',
                                    write_pv='CXI:SC1:AIO:04:ANALOGOUT')
        self.sc1_mesh_scale = EpicsSignal(name='sc1_mesh_scale',
                                    read_pv='CXI:SC1:AIO:04:SCALE')
        

    def get_sc1_mesh_voltage(self):
        """
        Get the current power supply voltage
        """
        return self.sc1_mesh_raw.get()

    def set_sc1_mesh_voltage(self, sigIn, wait=True, do_print=True):
        """
        Set voltage on power supply to an absolute value

        Parameters
        ----------
        sigIn: int or float
            Power supply voltage in Volts
        """
        if do_print:
            print('Setting voltage...')
        sigInScaled = sigIn / self.sc1_mesh_scale.get() # in V
        self.sc1_mesh_raw.put(sigInScaled)
        if wait:
            time.sleep(2.5)
        finalVolt = self.sc1_mesh_raw.get()
        finalVoltSupply = finalVolt*self.sc1_mesh_scale.get()
        if do_print:
            print('Power Supply Setpoint: %s V' % sigIn)
            print('Power Supply Voltage: %s V' % finalVoltSupply)

    def set_sc1_rel_mesh_voltage(self, deltaVolt, wait=True, do_print=True):
        """
        Increase/decrease power supply voltage by a specified amount

        Parameters
        ----------
        deltaVolt: int or float
            Amount to increase/decrease voltage (in Volts) from
            its current value. Use positive value to increase
            and negative value to decrease
        """
        if do_print:
            print('Setting voltage...')
        curr_set = self.sc1_mesh_raw.get_setpoint()
        curr_set_supply = curr_set * self.sc1_mesh_scale.get()
        if do_print:
            print('Previous Power Supply Setpoint: %s V' % curr_set_supply)
        new_voltage = round(curr_set_supply + deltaVolt)
        self.set_sc1_mesh_voltage(new_voltage, wait=wait, do_print=do_print)

    def tweak_mesh_voltage(self, deltaVolt):
        """
        Continuously Increase/decrease power supply voltage by
        specifed amount using arrow keys

        Parameters
        ----------
        deltaVolt: int or float
            Amount to change voltage (in Volts) from its current value at
            each step. After calling with specified step size, use arrow keys
            to keep changing
        ^C:
            exits tweak mode
        """
        print('Use arrow keys (left, right) to step voltage (-, +)')
        while True:
            key = key_press.get_input()
            if key in ('q', None):
                return
            elif key == key_press.arrow_right:
                self.set_sc1_rel_mesh_voltage(deltaVolt, wait=False,
                                          do_print=False)
            elif key == key_press.arrow_left:
                self.set_sc1_rel_mesh_voltage(-deltaVolt, wait=False,
                                          do_print=False)


post_template = """\
Run Number: {} {}

Acquiring {} events at {}

"""

