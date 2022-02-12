import statistics as stat
import subprocess
import sys
from time import sleep

import matplotlib.pyplot as plt
from epics import PV
from hutch_python.utils import safe_load
from ophyd import AreaDetector
from ophyd import Component as Cpt
from ophyd import Device, EpicsSignal, EpicsSignalRO
from pcdsdevices.device_types import IMS, PulsePicker
from pcdsdevices.sequencer import EventSequencer
from scipy import ndimage

#from cxi.db import daq
#from cxi.db import cxi
from cxi.db import camviewer, cxi_pulsepicker

seq = EventSequencer('ECS:SYS0:5', name='seq_5')

sc3_pulsepicker = PulsePicker('CXI:DS1:MMS:14', name='sc3_pulsepicker')
    
#defining the DS1 and DS2 z motors 
ds1_z_position = IMS('CXI:DS1:MMS:06', name = 'ds1_z_distance')
ds2_z_position = IMS('CXI:DS2:MMS:06', name = 'ds2_z_distance')

#defining pv for DsdCspad total intensity from shared memory
sc3_DsdCspad_intensity=PV('CXI:SC3:DIFFRACT:TOTAL_ADU')
sc1_DscCspad_intensity=PV('CXI:SC1:DIFFRACT:TOTAL_ADU')

#defining quick CSPAD optimization function
tot_intensity=0

from cxi.macros import Jet_chaser
from cxi.time_scans import Timetool
sc3_jet_chase = Jet_chaser('CXI',name = 'sc3_jet_chase')

def get_timetool():
    return Timetool.from_rc()

def sc1_stats():
    sc1 = EpicsSignalRO('CXI:SC1:INLINE:IMAGE1:ArrayData')
    while True:
        plt.imshow(sc1.get())
        plt.plot()
        sleep(0.1)    
    
#defining positions for the sc1_sample_x motor so that we can quickly move the x motor to the proper position
sc1_led = IMS('CXI:SC1:MMS:18', name='sc1_led')
sc1_sample_x = IMS('CXI:SC1:MMS:02',name='sc1_sample_x')

with safe_load('Foil_motors'):
#   foil_x = IMS('CXI:PI1:MMS:01', name = 'foil_x')
#   foil_y = IMS('CXI:PI1:MMS:02', name = 'foil_y')
   foil_x = IMS('CXI:SC2:MMS:06', name = 'foil_x')
   foil_y = IMS('CXI:SC2:MMS:05', name = 'foil_y')

with safe_load('MESH'):
    from pcdsdevices.analog_signals import Mesh
    mesh = Mesh('CXI:USR', 0, 1)


# load devices used for jet tracking testing
with safe_load('JT_testing_objects'):
  from jet_tracking.devices import JTFake, JTInput, JTOutput

  JT_input = JTInput(prefix='CXI:JTRK:REQ', name='JT_input')
  JT_output = JTOutput(prefix='CXI:JTRK:PASS', name='JT_output')
  JT_fake = JTFake(prefix='CXI:JTRK:FAKE', name='JT_fake')


if True:
    with safe_load('SC1_questar'):
        from jet_tracking.devices import JetCamera
        SC1_questar_ports = {'ROI_port': 'ROI1',
                             'ROI_stats_port': 'Stats1',
                             'ROI_image_port': 'IMAGE1'}
        SC1_questar = JetCamera(**SC1_questar_ports, prefix='CXI:SC1:INLINE', name='SC1_questar')

    with safe_load('SC1_params'):
        from jet_tracking.devices import InlineParams
        SC1_params = InlineParams(prefix='CXI:SC1:INLINE', name='SC1_params')

    with safe_load('SC1_diffract'):
        from jet_tracking.devices import Diffract
        SC1_diffract = Diffract(prefix='CXI:SC1:DIFFRACT', name='SC1_diffract')

    with safe_load('SC1_control'):
        from jet_tracking.jet_control import JetControl
        from cxi.db import cxi_pi2
        SC1_control = JetControl('SC1_control', cxi_pi1, SC1_questar, SC1_params,
                                 SC1_diffract)

if False:
    with safe_load('SC2_questar'):
        SC2_questar_ports = {'ROI_port': 'ROI1',
                             'ROI_stats_port': 'Stats1',
                             'ROI_image_port': 'IMAGE1'}
        SC2_questar = Questar(**SC2_questar_ports, prefix='CXI:SC2:INLINE', name='SC2_questar')

    with safe_load('SC2_offaxis'):
        SC2_offaxis_ports = {'ROI_port': 'ROI1',
                             'ROI_stats_port': 'Stats1',
                             'ROI_image_port': 'IMAGE1'}
        SC2_offaxis = Offaxis(**SC2_offaxis_ports, prefix='CXI:GIGE:06', name='SC2_offaxis')

    with safe_load('SC2_params'):
        from jet_tracking.devices import InlineParams
        SC2_params = InlineParams(prefix='CXI:SC2:INLINE', name='SC2_params')

    with safe_load('SC2_paroffaxis'):
        from jet_tracking.devices import OffaxisParams
        SC2_paroffaxis = OffaxisParams(prefix='CXI:SC2:OFFAXIS', name='SC2_paroffaxis')

    with safe_load('SC2_diffract'):
        from jet_tracking.devices import Diffract
        SC2_diffract = Diffract(prefix='CXI:SC2:DIFFRACT', name='SC2_diffract')

    with safe_load('SC2_control'):
        from jet_tracking.jet_control import JetControl
        from cxi.db import cxi_pi2
        SC2_control = JetControl('SC2_control', cxi_pi2, SC2_questar, SC2_params,
                                 SC2_diffract)


if True:
    with safe_load('SC3_questar'):
        SC3_questar_ports = {'ROI_port': 'ROI1',
                             'ROI_stats_port': 'Stats1',
                             'ROI_image_port': 'IMAGE1'}
        SC3_questar = Questar(**SC3_questar_ports, prefix='CXI:SC3:INLINE', name='SC3_questar')

    with safe_load('SC3_offaxis'):
        SC3_offaxis_ports = {'ROI_port': 'ROI1',
                             'ROI_stats_port': 'Stats1',
                             'ROI_image_port': 'IMAGE1'}
        SC3_offaxis = Offaxis(**SC3_offaxis_ports, prefix='CXI:GIGE:07', name='SC3_offaxis')

    with safe_load('SC3_params'):
        from jet_tracking.devices import InlineParams
        SC3_params = InlineParams(prefix='CXI:SC3:INLINE', name='SC3_params')

    with safe_load('SC3_paroffaxis'):
        from jet_tracking.devices import OffaxisParams
        SC3_paroffaxis = OffaxisParams(prefix='CXI:SC3:OFFAXIS', name='SC3_paroffaxis')

    with safe_load('SC3_diffract'):
        from jet_tracking.devices import Diffract
        SC3_diffract = Diffract(prefix='CXI:SC3:DIFFRACT', name='SC3_diffract')

    with safe_load('SC3_control'):
        from jet_tracking.jet_control import JetControl
        from cxi.db import cxi_pi3
        SC3_control = JetControl('SC3_control', cxi_pi3, SC3_questar, SC3_params,
                                 SC3_diffract)



with safe_load("imprint scans"):
    from cxi.imprint import imprint_row, sequencer, beam_stats

from cxi.macros import HPLC, GX_readback, Proportionair, safe_samplex

propA=Proportionair('CXI:SDS:PCM:A', name='propA')
propB=Proportionair('CXI:SDS:PCM:B', name='propB')
hplc1 = HPLC('CXI:SDS:LC20:01',name='hplc1')
hplc2 = HPLC('CXI:SDS:LC20:02',name='hplc2')


'''
Building the selector boxes with multiple inheritances
Building blocks will be reservoirs, valves, flow meters
'''

from cxi.macros import SelectorBoxValve
valve01 = Cpt(SelectorBoxValve,':VLV:01')
valve02 = Cpt(SelectorBoxValve,':VLV:02')


from cxi.macros import (FlowMeter, SelectorBox, SelectorBoxReservoir,
                        SelectorBoxReservoirStates, SelectorBoxValvePair)
selectorbox2 = SelectorBox('CXI:SDS:SEL:B', name = 'selectorbox2')
selectorbox1 = SelectorBox('CXI:SDS:SEL:A', name = 'selectorbox1')

class VacuumPump(Device):
    '''
    ilk is the interlock
    safe_operation returns the value of whether it is safe to start the turbo pump
    status_full_speed returns whether the pump is at full speed
    '''    
    
    safe_operation = Cpt(EpicsSignalRO,':RUN_OK')
    status_setpoint = Cpt(EpicsSignal,':RUN_SW')
    alt_status_setpoint = Cpt(EpicsSignal,':START_SW')
    status_full_speed = Cpt(EpicsSignalRO,':SP1_DI')
    alt_status_full_speed = Cpt(EpicsSignalRO, ':NORMAL_DI')
    status_value = Cpt(EpicsSignalRO,':RUN_DO')
    alt_status_value = Cpt(EpicsSignalRO, ':START_DO')
    fault_alarm = Cpt(EpicsSignalRO, ':FLTALM')
    fault_di = Cpt(EpicsSignalRO, ':FLT_DI')
    ilk_do = Cpt(EpicsSignalRO, ':ILK_DO')
    ilk_ok = Cpt(EpicsSignalRO,':ILK_OK')
    ilk_sw = Cpt(EpicsSignal,':ILK_SW')
    
    def turn_on(self):
        try:        
            self.status_setpoint.put(1)
            sleep(3)
            return self.status_value.get()
        except TimeoutError:
            self.alt_status_setpoint.put(1)
            sleep(3)
            if self.status_value.get()==1:
                print("There was a problem turning on this pump")
        
    def turn_off(self):
        try:        
            self.status_setpoint.put(0)
            sleep(3)
            return self.status_value.get()
        except TimeoutError:
            self.alt_status_setpoint.put(0)
            sleep(3)
        try:
            state = self.status_value.get() 
        except TimeoutError:
            state = self.alt_status_value.get()
        if state==1:
                print("There was a problem turning off this pump")
        
    def run_state(self):
        try:
            currStatus=self.status_value.get()
        except TimeoutError:
            currStatus=self.alt_status_value.get()
        try:
            currSpeed=self.status_full_speed.get()
        except TimeoutError:
            currSpeed=self.alt_status_full_speed.get()           
            if currStatus==0:
                print("The turbo pump is currently not running")
            else:
                if currSpeed==0:
                    print("The turbo pump is on and accelerating")
                else:
                    print("The turbo pump is on at full speed")
        subprocess.call(['/reg/neh/operator/cxiopr/bin/cxi-bash1.sh'])                 



class TurboPump(VacuumPump):
    pass    

#instantiating the sc3 and dsd turbos
sc1_turbo01 = TurboPump('CXI:SC1:PTM:01',name='sc1_turbo01')
sc1_turbo02 = TurboPump('CXI:SC1:PTM:02',name='sc1_turbo02')
sc1_turbo03 = TurboPump('CXI:SC1:PTM:03',name='sc1_turbo03')
sc3_turbo01 = TurboPump('CXI:SC3:PTM:01',name='sc3_turbo01')
sc3_turbo02 = TurboPump('CXI:SC3:PTM:02',name='sc3_turbo02')
sc3_turbo03 = TurboPump('CXI:SC3:PTM:03',name='sc3_turbo03')
dsd_turbo01 = TurboPump('CXI:DSD:PTM:01',name='dsd_turbo01')  

     
     
class Gauge(Device):
    pressure = Cpt(EpicsSignalRO,':PMON')
    alt_pressure = Cpt(EpicsSignalRO,':PRESS')
    pressure_status = Cpt(EpicsSignalRO,':PSTATMON')
    presure_log = Cpt(EpicsSignalRO,':PLOG')    
    status = Cpt(EpicsSignalRO,':STATMON')
    
    def get_pressure(self):
        try:
            pressure = self.pressure.get()
        except TimeoutError:
            pressure = self.alt_pressure.get()
        return pressure
    
    
    
class ColdCathode(Gauge):
#    gcc1 = Cpt(Gauge,'GCC:01:')
#    gcc1_state = Cpt(EpicsSignalRO,'GCC:01:STATE')
#    gcc1_status_setpoint = Cpt(EpicsSignal,'GCC:01:ENBL_SW')
    state = Cpt(EpicsSignalRO, ':STATE')
    status_setpoint = Cpt(EpicsSignal, ':ENBL_SW')
    
    def enable(self):
        self.status_setpoint.put(1,wait=True)
        try:
            return self.state.get()
        except TimeoutError:
            print("The 'state' PV couldn't be connected to so I will return the setpoint readback instead")
            return self.status_setpoint.get()
        
    def disable(self):
        self.status_setpoint.put(0,wait=True)
        try:
            return self.state.get()
        except TimeoutError:
            print("The 'state' PV couldn't be connected to so I will return the setpoint readback instead")
            return self.status_setpoint.get()
#        return self.gcc1_state.get()

#Instantiating the cold cathode gauges          
dg1_gcc01 = ColdCathode('CXI:DG1:GCC:01',name='dg1_gcc01')      
kb1_gcc01 = ColdCathode('CXI:KB1:GCC:01',name='kb1_gcc01')
kb1_gcc02 = ColdCathode('CXI:KB1:GCC:02',name='kb1_gcc02')
kb1_gcc03 = ColdCathode('CXI:KB1:GCC:03',name='kb1_gcc03')
kb2_gcc01 = ColdCathode('CXI:KB2:GCC:01',name='kb2_gcc01')
sc2_gcc01 = ColdCathode('CXI:SC2:GCC:01',name='sc2_gcc01') 
dsa_gcc01 = ColdCathode('CXI:DSA:GCC:01',name='dsa_gcc01')
dg2_gcc01 = ColdCathode('CXI:DG2:GCC:01',name='dg2_gcc01')
dsb_gcc01 = ColdCathode('CXI:DSB:GCC:01',name='dsb_gcc01')
sc1_gcc01 = ColdCathode('CXI:SC1:GCC:01',name='sc1_gcc01')  
dsc_gcc01 = ColdCathode('CXI:DSC:GCC:01',name='dsc_gcc01') 
sc3_gcc01 = ColdCathode('CXI:SC3:GCC:01',name='sc3_gcc01')
dsd_gcc01 = ColdCathode('CXI:DSD:GCC:01',name='dsd_gcc01')
dg3_gcc01 = ColdCathode('CXI:DG3:GCC:01',name='dg3_gcc01')
      
class Pirani(Gauge):
#    p1 = Cpt(Gauge,'GPI:01:')
    pass

#Instantiating the pirani gauges
dg1_pirani01 = Pirani('CXI:DG1:GPI:01',name='dg1_pirani01')
kb1_pirani01 = Pirani('CXI:KB1:GPI:01',name='kb1_pirani01')
kb1_pirani02 = Pirani('CXI:KB1:GPI:02',name='kb1_pirani02')
kb1_pirani03 = Pirani('CXI:KB1:GPI:03',name='kb1_pirani03')
kb2_pirani01 = Pirani('CXI:KB2:GPI:01',name='kb2_pirani01')
sc2_pirani01 = Pirani('CXI:SC2:GPI:01',name='sc2_pirani01')
dsa_pirani01 = Pirani('CXI:DSA:GPI:01',name='dsa_pirani01')
dg2_pirani01 = Pirani('CXI:DG2:GPI:01',name='dg2_pirani01')
dsb_pirani01 = Pirani('CXI:DSB:GPI:01',name='dsb_pirani01')
sc1_pirani01 = Pirani('CXI:SC1:GPI:01',name='sc1_pirani01')
dsc_pirani01 = Pirani('CXI:DSC:GPI:01',name='dsc_pirani01')
sc3_pirani01 = Pirani('CXI:SC3:GPI:01',name='sc3_pirani01')
dsd_pirani01 = Pirani('CXI:DSD:GPI:01',name='dsd_pirani01')
dg3_pirani01 = Pirani('CXI:DG3:GPI:01',name='dg3_pirani01')


#now defining the different types of valves at CXI

class Valve(Device):
    state = Cpt(EpicsSignal,':OPN_SW')
    valve_open = Cpt(EpicsSignalRO, ':OPN_DI')
    valve_closed = Cpt(EpicsSignalRO, ':CLS_DI')
    allowed_open =Cpt(EpicsSignalRO, ':OPN_OK')
    
    
    def close_valve(self):
        self.state.put(0,wait=True)
        sleep(1)
        state =  self.state.get()
        if state == 0:
            print("The valve is closed")
        else:
            print("The valve did not close")
        
    def open_valve(self):
        safe_state=self.allowed_open.get()
        if safe_state==1:
            self.state.put(1,wait=True)
            sleep(1)
            state =  self.state.get()
            if state == 1:
                print("The valve is open")
            else:
                print("The valve did not open")
        elif safe_state==0:
            print("The valve cannot be safely opened currently.  you must fix this before opening it.")
        else:
            print("The valve is in an undefined state")
            
    def rapid_open_toggle(self, siesta=0.1):
        self.state.put(1,wait=True)
        sleep(siesta)  
        self.state.put(0,wait=True)
        return self.state.get()
                
    def safe_state(self):
        safe_state=self.allowed_open.get()
        if safe_state == 1:
            print("The valve can be safely opened currently")
        elif safe_state==0:
            print("The valve cannot be safely opened currently")
        else:
            print("The valve is in an undefined state")
  
  
  
class ForelineValve(Valve):
    pass
  
#Instantiating the foreline valves  
sc1_foreline01 = ForelineValve('CXI:SC1:VIC:01',name='sc1_foreline01')
#the sc1 foreline valve numbering has been reindexed so that VCC04 is foreline02 to be consistent with turbo02
sc1_foreline02 = ForelineValve('CXI:SC1:VIC:04',name='sc1_foreline02')
sc1_foreline03 = ForelineValve('CXI:SC1:VIC:05',name='sc1_foreline03')

sc3_foreline01 = ForelineValve('CXI:SC3:VIC:01',name='sc3_foreline01')
sc3_foreline02 = ForelineValve('CXI:SC3:VIC:02',name='sc3_foreline02')
sc3_foreline03 = ForelineValve('CXI:SC3:VIC:03',name='sc3_foreline03')

dsd_foreline01 = ForelineValve('CXI:DSD:VIC:01',name='dsd_foreline01')


class VentValve(Valve):
    vcc01 = Cpt(Valve,':VCC:01')
    vcc02 = Cpt(Valve,':VCC:02')
    
        
sc1_ventline = VentValve('CXI:SC1',name='sc1_ventline')       
sc3_ventline = VentValve('CXI:SC3',name='sc3_ventline')
dsd_ventline = VentValve('CXI:DSD',name='dsd_ventline')



class GateValve(Valve):
    pass    

#instantiating the gate valves    
dg1_gatevalve_upstream = GateValve('CXI:DG1:VGC:01',name='dg1_gatevalve_upstream')
dg1_gatevalve_downstream = GateValve('CXI:DG1:VGC:02',name='dg1_gatevalve_downstream')
kb1_gatevalve_upstream = GateValve('CXI:KB1:VGC:01',name='k b1_gatevalve_upstream')
kb1_gatevalve_downstream = GateValve('CXI:KB1:VGC:02',name='kb1_gatevalve_downstream')
kb2_gatevalve_upstream = GateValve('CXI:KB2:VGC:01',name='kb2_gatevalve_upstream')
kb2_gatevalve_downstream = GateValve('CXI:KB2:VGC:02',name='kb2_gatevalve_downstream')
dg2_gatevalve_upstream = GateValve('CXI:DG2:VGC:01',name='dg2_gatevalve_upstream')
dg2_gatevalve_downstream = GateValve('CXI:DG2:VGC:02',name='dg2_gatevalve_downstream')
sc1_gatevalve_upstream = GateValve('CXI:SC1:VGC:01',name='sc1_gatevalve_upstream')
sc1_gatevalve_downstream = GateValve('CXI:SC1:VGC:02',name='sc1_gatevalve_downstream')
sc1_gatevalve_main_turbo = GateValve('CXI:SC1:VGC:03',name='sc1_gatevalve_main_turbo')
sc3_gatevalve_upstream = GateValve('CXI:SC3:VGC:01',name='sc3_gatevalve_upstream')
#DG3 gate valve PV has DSC and not DG3 in the PV name.  The python instantiation still calls it dg3
dg3_gatevalve_upstream = GateValve('CXI:DSC:VGC:01',name='dg3_gatevalve_upstream')

#Defining the extra PVs necessary to make the vent SSC script function    


sc3_plc_override = PV('CXI:VAC:PLC:01:OverrideMode')
#needed to disable the SSC vacuum PLC override

sc3_vgc01_override = PV('CXI:SC3:VGC:01:OVRD_SW')
#needed to disable the sc3 upstream gatevalve override


#class VacuumChamber(Device):
#    sc3 = Cpt(VentValve,'CXI:SC3:')



class Detector(AreaDetector):
    voltage_setpoint = Cpt(EpicsSignal,':SetVoltage')    
    voltage_readback = Cpt(EpicsSignalRO,':GetVoltageMeasurement')
    current_setpoint = Cpt(EpicsSignal, ':SetCurrent')
    current_readback = Cpt(EpicsSignalRO,':GetCurrentMeasurement')
    temp_readback = Cpt(EpicsSignalRO, ':GetTemperature')
    
    def quad_idle(self, inVoltage=20):
        #meant to idle a CSPAD so the default is set to 20 V
        self.voltage_setpoint.put(inVoltage)
        sleep(0.2)        
        return self.voltage_readback.get()
    
    
    
class MPOD(Detector):
    ramp_up_rate = Cpt(EpicsSignal, ':MOD::SetVoltageRiseRate')
    ramp_down_rate = Cpt(EpicsSignal, ':MOD::SetVoltageFallRate')
    
    
    
class Cspad(MPOD):
    quad0 = Cpt(MPOD,':CH:0')
    quad1 = Cpt(MPOD,':CH:1')
    quad2 = Cpt(MPOD,':CH:2')
    quad3 = Cpt(MPOD,':CH:3')
    
ds2_cspad = Cspad('CXI:D50:MPD',name='ds2_cspad')
#ds1_cspad = Cspad('CXI:D51:MPD',name='ds1_cspad') 



class DetectorChiller(Device):
    temp_setpoint = Cpt(EpicsSignal,':NEW_SETPOINT_C')
    pump_state = Cpt(EpicsSignalRO, ':PUMP_STATE')
    turn_on = Cpt(EpicsSignal, ':START')
    turn_off = Cpt(EpicsSignal, ':STOP')
    remote_state = Cpt(EpicsSignalRO,':MODE')
    set_remote = Cpt(EpicsSignal, ':REMOTE')
    set_local = Cpt(EpicsSignal, ':LOCAL')
        
    tank_level_monitor = Cpt(EpicsSignalRO,':MON:TANK')

#instantiate the dsd chiller    
dsd_chiller = DetectorChiller('CXI:DSD',name='dsd_chiller')   


#define the DG2 and DSC Be lens x and y motors
dg2_Be_lenses_x_pos = IMS('CXI:DG2:MMS:05',name = 'dg2_Be_lenses_x_pos')  
dg2_Be_lenses_y_pos = IMS('CXI:DG2:MMS:06',name = 'dg2_Be_lenses_y_pos')

with safe_load('dsc_lenses'):    
    dsc_Be_lenses_x_pos = IMS('CXI:DS1:MMS:07',name = 'dsc_Be_lenses_x_pos')
    dsc_Be_lenses_y_pos = IMS('CXI:DS1:MMS:08',name = 'dsc_Be_lenses_y_pos')
    
    #these functions are currently being defined to move the lenses in for 9.831 keV only. 
    def dsc_lenses_in():
        dsc_Be_lenses_x_pos.enable()
        dsc_Be_lenses_y_pos.enable()
        dsc_Be_lenses_x_pos.mv(0,wait=True)
        dsc_Be_lenses_y_pos.mv(38.3569, wait=True)
        dsc_Be_lenses_x_pos.mv(1.71, wait=True)
        dsc_Be_lenses_x_pos.disable()
        dsc_Be_lenses_y_pos.disable()
        print("The DSC lenses have arrived and are aligned for 9.8 keV and have been disabled")
    
    def dsc_lenses_out():
        dsc_Be_lenses_x_pos.enable()
        dsc_Be_lenses_y_pos.enable()
        dsc_Be_lenses_x_pos.mv(0,wait=True)
        dsc_Be_lenses_y_pos.mv(60, wait=True)
        dsc_Be_lenses_x_pos.disable()
        dsc_Be_lenses_y_pos.disable()
        print("The DSC lenses have been moved from the beam path and have been disabled")

def vent_sc3(rate="Normal"):    
    #defining a progress bar    
    while sc3_plc_override.get() == 1:
        sc3_plc_override.put(0)
        print("Changing the PLC override to Low from High")
        sleep(1)    
    print ("PLC override is set to low, moving on to setting the upstream gate valve override to zero")

    counter=0
    try:
        while sc3_vgc01_override.get() == 1:
            sc3_vgc01_override.put(0)
            print("Changing the GateValve override to Low from High")
            sleep(1)
            counter+=counter+1
    except counter>=15:
        if sc3_gatevalve_upstream.valve_closed.get()==1:
            print("The override is misbehaving but the gate valve is closed.  Proceeding with vent")
        else:
            print("Something is wrong with the override.  Cannot continue with venting procedure")
            sys.exit(0)
    
    print ("SC3 Gatevalve override is set to low, moving on to the turbos and detector")
    
    #idle the ds2 detector quads
    ds2_cspad.quad0.quad_idle()
    ds2_cspad.quad1.quad_idle()
    ds2_cspad.quad2.quad_idle()
    ds2_cspad.quad3.quad_idle()
    
    #Since the chamber will be open to air, raise the detector setpoint to 16 degrees C
    if dsd_chiller.remote_state.get()==1:
        dsd_chiller.set_remote.put(0)
        sleep(0.5)
    dsd_chiller.temp_setpoint.put(16)
    
    

    #close the primary turbo-foreline valve pair in sc3
    sc3_turbo01.turn_off()
    sc3_foreline01.close_valve()

    #close the second turbo-foreline valve pair in sc3
    sc3_turbo02.turn_off()
    sc3_foreline02.close_valve()
    
    #close the third turbo-foreline valve pair in sc3
    sc3_turbo03.turn_off()
    sc3_foreline03.close_valve()

    #close the primary turbo-foreline valve pair in dsd
    dsd_turbo01.turn_off()
    dsd_foreline01.close_valve()    
    
    if rate=="Fast":
        print("will do a more rapid venting procedure with a 3 min slow down of the turbos")
        sc3_ventline.vcc01.rapid_open_toggle()
        dsd_ventline.vcc01.rapid_open_toggle()
        sc3_ventline.vcc02.rapid_open_toggle()
        dsd_ventline.vcc02.rapid_open_toggle()        
        time_point=180
        
    elif rate=="Normal":
        print("Will do a normal venting procedure with a 5 min slow down of the turbos")
        time_point=300
        
    elif rate=="Slow":
        print("Who are you, Matt Hayes?  Will do a long vent cycle with a 20 min slow down of the turbos and a slow gas bleed")
        time_point=1200
        
    elif rate=="Cycle":
        print("Will do a normal venting procedure with a 5 min slow down of the turbos and then do the heavy metal scrubbing proceudre of said chamber")
        time_point=300
        
    else:
        print("You didn't select a proper option.  Choose 'Slow', 'Normal', or 'Fast'")
        sys.exit(0)
    
#    #making a progress bar and sleeping for the desired amount of wind-down time for the turbos
#    sys.stdout.write("[%s]" % (" " * time_point/20))
#    sys.stdout.flush() 
#    sys.stdout.write("\b" * (span+1))    
#    for i in range(20):
#        sleep(time_point/20)
#        sys.stdout.write("-") 
#        sys.stdout.flush() 
    sleep(time_point)
        
    
    if dsd_chiller.temp_setpoint.get() >= 16:
        print("There may be an issue bringing the detector temperature up")
        
    #disabling the cold cathodes    
    print("Disabling the cold cathodes")
    sc3_gcc01.disable()
    dsd_gcc01.disable()
    sleep(5)
    
    print("Venting started with 30s delays")
    for i in range(10):
        sc3_ventline.vcc01.rapid_open_toggle()
        dsd_ventline.vcc01.rapid_open_toggle()
        sc3_ventline.vcc02.rapid_open_toggle()
        dsd_ventline.vcc02.rapid_open_toggle()
        sleep(30)
        
    print("Venting started with 10s delays")
    span=10 
    sys.stdout.write("[%s]" % (" " * span))
    sys.stdout.flush() 
    sys.stdout.write("\b" * (span+1)) 
#    while     
    for i in range(span):
        sc3_ventline.vcc01.rapid_open_toggle(siesta=0.25)
        dsd_ventline.vcc01.rapid_open_toggle(siesta=0.25)
        sc3_ventline.vcc02.rapid_open_toggle(siesta=0.25)
        dsd_ventline.vcc02.rapid_open_toggle(siesta=0.25)        
        sleep(10)
        sys.stdout.write("-") 
        sys.stdout.flush() 
        
    
    print("Venting started with 2s delays")
    span=20 
    sys.stdout.write("[%s]" % (" " * span))
    sys.stdout.flush() 
    sys.stdout.write("\b" * (span+1)) 
    
    pressure = sc3_pirani01.get_pressure()
    while pressure <= 1:
        for i in range(span):
            sc3_ventline.vcc01.rapid_open_toggle(siesta=0.25)
            dsd_ventline.vcc01.rapid_open_toggle(siesta=0.25)
            sc3_ventline.vcc02.rapid_open_toggle(siesta=0.25)
            dsd_ventline.vcc02.rapid_open_toggle(siesta=0.25)
            sleep(2)
            sys.stdout.write("-") 
            sys.stdout.flush() 
            
    if rate == "Cycle":
        for i in range(5):
            sc3_ventline.vcc01.open_valve()
            dsd_ventline.vcc01.open_valve()
            sc3_ventline.vcc02.open_valve()
            dsd_ventline.vcc02.open_valve()
  
            #monitor the pressure while venting          
            pressure = sc3_pirani01.get_pressure()
            while pressure <= 400:
                sleep(20)
                pressure = sc3_pirani01.get_pressure()
            print("The pressure is above 350 torr and therefore the chamber will be pumped down to 0.01 torr")
            
            #close the vent valves
            sc3_ventline.vcc01.close_valve()
            dsd_ventline.vcc01.close_valve()
            sc3_ventline.vcc02.close_valve()
            dsd_ventline.vcc02.close_valve()
            
            #open the foreline valves    
            sc3_foreline01.open_valve()
            sc3_foreline02.open_valve()
            sc3_foreline03.open_valve()
            dsd_foreline01.open_valve()
            
            pressure = sc3_pirani01.get_pressure()
            while pressure >= 0.1:
                sleep(20)
                pressure = sc3_pirani01.get_pressure()
            print("The pressure is below 0.01 torr and will now be vented to above 350 torr")
            #close the foreline valves            
            sc3_foreline01.close_valve()
            sc3_foreline02.close_valve()
            sc3_foreline03.close_valve()
            dsd_foreline01.close_valve()
            
    else:
        sc3_ventline.vcc01.open_valve()
        dsd_ventline.vcc01.open_valve()
        sc3_ventline.vcc02.open_valve()
        dsd_ventline.vcc02.open_valve()
        subprocess.call(['/reg/neh/operator/cxiopr/bin/cxi-bash1.sh'])
        
        sleep(900)
        sc3_ventline.vcc01.close_valve()
        dsd_ventline.vcc01.close_valve()
        sc3_ventline.vcc02.close_valve()
        dsd_ventline.vcc02.close_valve()
    
    subprocess.call(['/reg/neh/operator/cxiopr/bin/cxi-bash1.sh'])
    
#dsc detectpr gate valve pin
dsc_detector_pin_state = PV('CXI:SC1:VGC:02:PININ_DI') 
       
       
       
       
       
def vent_sc1(rate="Normal"):    
    '''
    function for venting sc1
    only keyword is rate, and the options are "Slow", "Normal", "Fast", or "Cycle"
    
    General process is to move the DSC detector to its home position (CXI:SC:MMS:06:RBV > -10) \
    unpin the SC1-DSC gate valve, then close the three SC1 gate valves before turning off the chamber \
    turbos and closing the associated foreline valves.  After wait times defined by the rate keyword input \
    the vent valves are cycled between opened and closed to let a slow but steady gas leak into the chamber \
    The cycle option is used after heavy metal injection and generally takes a couple of hours.  It "scrubs" \
    the chamber by cycling between 0.01 and 400 torr five times before leaving the chamber under 400 torr vacuum.
        '''    
    
    #moving the dsc detector to the home position 
    for i in range(5):    
        if ds1_z_position.user_readback.get() <= -10:
            print("Need to move the detector to its home position")    
            try: 
                ds1_z_position.umv(0,wait=True)
            except TimeoutError:
                Continue
    
    if ds1_z_position.user_readback.get() >= -10:
        print("Detector is safe")
    else:
        print("The detector has not made it to a safe position, please try again")
        sys.exit(0)
    
    
    print("closing the upstream and main turbo gate valves")
    sc1_gatevalve_upstream.close_valve()
    sc1_gatevalve_main_turbo.close_valve()
    
    if dsc_detector_pin_state.get() == 1:
        print("You need to remove the detector gate valve pin")
        while dsc_detector_pin_state.get() == 1:
            sleep(10)
            print("You need to remove the detector gate valve pin")
    else:
        print("Detector gate valve pin is pulled, will proceed")        
    
    print("Will close the downstream (detector) gate valve in SC1")
    sc1_gatevalve_downstream.close_valve()
    
    #turning off the turbos and closing the associated foreline valves in sc1    
    sc1_turbo01.turn_off()
    sc1_foreline01.close_valve()
    
    sc1_turbo02.turn_off()
    sc1_foreline02.close_valve()
    
    sc1_turbo03.turn_off()
    sc1_foreline03.close_valve()
    
    if rate=="Fast":
        print("will do a more rapid venting procedure with a 3 min slow down of the turbos")
        sc1_gcc01.disable()
        sc1_ventline.vcc01.rapid_open_toggle()
        sc1_ventline.vcc02.rapid_open_toggle()      
        time_point=180
        
    elif rate=="Normal":
        print("Will do a normal venting procedure with a 5 min slow down of the turbos")
        time_point=300
        
    elif rate=="Slow":
        print("Who are you, Matt Hayes?  Will do a long vent cycle with a 20 min slow down of the turbos and a slow gas bleed")
        time_point=1200
        
    elif rate=="Cycle":
        print("Will do a normal venting procedure with a 5 min slow down of the turbos and then do the heavy metal scrubbing proceudre of said chamber")
        time_point=300
        
    else:
        print("You didn't select a proper option.  Choose 'Slow', 'Normal', 'Fast', or 'Cycle'")
        sys.exit(0)

    #making a progress bar and sleeping for the desired amount of wind-down time for the turbos
#    sys.stdout.write("[%s]" % (" " * time_point/20))
#    sys.stdout.flush() 
#    sys.stdout.write("\b" * (span+1))    
#    for i in range(20):
#        sleep(time_point/20)
#        sys.stdout.write("-") 
#        sys.stdout.flush() 
    sleep(time_point)
        
    #disabling the cold cathodes    
    print("Disabling the cold cathode")
    sc1_gcc01.disable()
    sleep(5)
    
    print("Venting started with 30s delays")
    sc1_pressure = sc1_pirani01.get_pressure()
    while sc1_pressure < 1:
        for i in range(30):
            if i < 10:            
                time_delay = 30
                Siesta = 0.1
            
            elif 10 < i < 20:
                Siesta = 0.25                
                time_delay = 10
            else: 
                Siesta = 0.25
                time_delay = 2
                
            
            sc1_ventline.vcc01.rapid_open_toggle(siesta=Siesta)
            sc1_ventline.vcc02.rapid_open_toggle(siesta=Siesta)
            sleep(time_delay)
            sc1_pressure = sc1_pirani01.get_pressure()
        
    if rate == "Cycle":
        for i in range(5):
            sc1_ventline.vcc01.open_valve()
            sc1_ventline.vcc02.open_valve()
  
            #monitor the pressure while venting          
            sc1_pressure = sc1_pirani01.get_pressure()
            while sc1_pressure <= 400:
                sleep(20)
                sc1_pressure = sc1_pirani01.get_pressure()
            print("The pressure is above 350 torr and therefore the chamber will be pumped down to 0.01 torr")
            
            #close the vent valves
            sc1_ventline.vcc01.close_valve()
            sc1_ventline.vcc02.close_valve()
            
            
            #open the foreline valves    
            sc1_foreline02.open_valve()
            sc1_foreline03.open_valve()
            
            

            sc1_pressure = sc1_pirani01.get_pressure()
            while sc1_pressure >= 0.1:
                sleep(20)
                sc1_pressure = sc1_pirani01.get_pressure()
            print("The pressure is below 0.01 torr and will now be vented to above 350 torr")
            #close the foreline valves            
            sc1_foreline02.close_valve()
            sc1_foreline03.close_valve()
         
        sc1_pressure = sc1_pirani01.get_pressure()
        sc1_ventline.vcc01.open_valve()
        sc1_ventline.vcc02.open_valve()
        while sc1_pressure <= 400:
             sleep(20)
             sc1_pressure = sc1_pirani01.get_pressure()   
        sc1_ventline.vcc01.close_valve()
        sc1_ventline.vcc02.close_valve()
        
            
    else:
        sc1_ventline.vcc01.open_valve()
        sc1_ventline.vcc02.open_valve()
        subprocess.call(['/reg/neh/operator/cxiopr/bin/cxi-bash1.sh'])        
        sleep(900)
        sc3_ventline.vcc01.close_valve()
        sc3_ventline.vcc02.close_valve()
    
    subprocess.call(['/reg/neh/operator/cxiopr/bin/cxi-bash1.sh'])

def camviewer():
    subprocess.call(['/reg/neh/operator/cxiopr/bin/yagviewer.sh'])
        
def shift_end():
    print("This does not close the SC1 gate valves, only the other gate valves")
    cxi_pulsepicker.close()
    sc3_pulsepicker.close()    
    dg1_gatevalve_upstream.close_valve()
    dg1_gatevalve_downstream.close_valve()
    kb1_gatevalve_upstream.close_valve()
    kb1_gatevalve_downstream.close_valve()
    kb2_gatevalve_upstream.close_valve()
    dg2_gatevalve_upstream.close_valve()
    dg2_gatevalve_downstream.close_valve()
    sc1_gatevalve_upstream.close_valve()
    sc3_plc_override.put(0)
    dg3_gatevalve_upstream.close_valve()


def cycle_sc3():
    for i in range(5):
            sc3_ventline.vcc01.open_valve()
            dsd_ventline.vcc01.open_valve()
            sc3_ventline.vcc02.open_valve()
            dsd_ventline.vcc02.open_valve()
  
            #monitor the pressure while venting          
            pressure = sc3_pirani01.get_pressure()
            while pressure <= 400:
                sleep(20)
                pressure = sc3_pirani01.get_pressure()
            print("The pressure is above 350 torr and therefore the chamber will be pumped down to 0.01 torr")
            
            #close the vent valves
            sc3_ventline.vcc01.close_valve()
            dsd_ventline.vcc01.close_valve()
            sc3_ventline.vcc02.close_valve()
            dsd_ventline.vcc02.close_valve()
            
            #open the foreline valves    
            sc3_foreline01.open_valve()
            sc3_foreline02.open_valve()
            sc3_foreline03.open_valve()
            dsd_foreline01.open_valve()
            
            pressure = sc3_pirani01.get_pressure()
            while pressure >= 0.1:
                sleep(20)
                pressure = sc3_pirani01.get_pressure()
            print("The pressure is below 0.01 torr and will now be vented to above 350 torr")
            #close the foreline valves            
            sc3_foreline01.close_valve()
            sc3_foreline02.close_valve()
            sc3_foreline03.close_valve()
            dsd_foreline01.close_valve()
#==============================================================================
#     if dsc_detector_pin_state.get() == 1:
#         Continue
#     else:
#         if 
#==============================================================================

#defining the dg1 and dg2 yag y motors
dg1_yag_y = IMS('CXI:DG1:MMS:08',name='dg1_yag_y')
dg2_yag_y = IMS('CXI:DG2:MMS:10',name='dg2_yag_y')

def shift_start():
    cxi_pulsepicker.close()
    sc3_pulsepicker.close()
    dg1_yag_y.umv(0)
    print("the DG1 YAG is inserted")
    dg2_yag_y.umv(0)
    print("The DG2 Yag is inserted")
#launch dg1 camera
    subprocess.call(['/reg/neh/operator/cxiopr/bin/msh/launch-startup-cameras.sh'])
  
    dg1_gatevalve_upstream.open_valve()
    dg1_gatevalve_downstream.open_valve()
    kb1_gatevalve_upstream.open_valve()
    kb1_gatevalve_downstream.open_valve()
    kb2_gatevalve_upstream.open_valve()
    dg2_gatevalve_upstream.open_valve()
    dg2_gatevalve_downstream.open_valve()
    sc1_gatevalve_upstream.open_valve()
    sc1_gatevalve_downstream.open_valve()


def end_shift():
    '''this is just a function to shut the proper upstream gate valves at CXI. It will not close the gate valve that separates the main sample chamber and the detector chamber.'''
    cxi_pulsepicker.close()
    dg1_yag_y.umv(0)
    print("the DG1 YAG is inserted")
    dg2_yag_y.umv(0)
    print("The DG2 Yag is inserted")
  
    dg1_gatevalve_upstream.close_valve()
    dg1_gatevalve_downstream.close_valve()
    kb2_gatevalve_upstream.close_valve()
    dg2_gatevalve_upstream.close_valve()
    dg2_gatevalve_downstream.close_valve()
    sc1_gatevalve_upstream.close_valve()



    
def gige_launch(camera=1,view="camViewer"):
    '''camera defines which gige to use and view defines whether to open the '''
    cam=str(camera)    
    if view=="master":
        subprocess.call(["/reg/g/pcds/engineering_tools/cxi/scripts/gige", "-c", cam, "-m", "-w", str(12)])
    else:
        subprocess.call(['/reg/g/pcds/engineering_tools/cxi/scripts/gige' ,'-c', cam, "-w", str(12)])
    
import pyaudio
import wave
import time


chunk = 1024

def play_wav(wav_filename,chunk_size = chunk):
    
    wf = wave.open(wav_filename, 'rb')

    p = pyaudio.PyAudio()

    soundfile = p.open(format=p.get_format_from_width(wf.getsampwidth()), channels = wf.getnchannels(), rate = wf.getframerate(), output=True)

    data = wf.readframes(chunk_size)
    while len(data) > 0:
        soundfile.write(data)
        data = wf.readframes(chunk_size)


    #stop stream
    soundfile.stop_stream()
    soundfile.close()

    #Close PyAudio
    p.terminate()

#def usage():
#   prog_name = os.path.basename()

with safe_load('plans'):
    from cxi.plans import *

from cxi.db import daq

def constant_run(duration=300):
    from pcdsdaq.daq import BEGIN_TIMEOUT
    BEGIN_TIMEOUT=10
    counter = 0 #for timeout errors
    try:
        while True:
            try:
                daq.connect()
                daq.begin(record=True, duration=duration, wait=False, end_run=True)
                daq.wait()
                counter = 0 # success! So we should reset counter
                daq.disconnect()
            except TimeoutError:
                daq.end_run()
                daq.disconnect()
                print("TimeoutError on previous run, starting the next run")
                counter += 1
                if counter > 3:
                    print("Multiple timeout errors exiting script")
                    break
            except KeyboardInterrupt:
                daq.end_run()
                daq.disconnect()
                break
    except KeyboardInterrupt:
        daq.end_run()
        daq.disconnect()


#defining some slits for the beamline. Will partially use the naming convention from other beamlines and name them s_location instead of s1, s2, etc.
from pcdsdevices.slits import LusiSlits
s_dsb=LusiSlits(name="s_dsb", prefix="CXI:DSB:JAWS")
s_dg1=LusiSlits(name="s_dg1", prefix="CXI:DG1:JAWS")
s_dg2=LusiSlits(name="s_dg2", prefix="CXI:DG2:JAWS")
s_kb1u=LusiSlits(name="s_kb1u", prefix="CXI:KB1:JAWS:US")
s_kb1d=LusiSlits(name="s_kb1d", prefix="CXI:KB1:JAWS:DS")


#making a gdvn shutdown function for python
def gdvn_shutdown_sc3():
    pressure_list={200,100,50,25,50,25,10,50,10,25}
    selectorbox2.valve01.requested_position.put(12)
    selectorbox2.valve02.requested_position.put(12)
    print("Switching to water port to wash out sample")
    sleep(300)
    hplc2.flowrate_setpoint.put(0)
    hplc2.status_setpoint.put(0)
    while hplc2.pressure.get() > 10:
        sleep(5)
    selectorbox2.valve02.requested_position.put(11)
    print("Switching to air port aka aeropuerto on the sample valve")
    sleep(120)
    for i in pressure_list:
        print("Setting the He sheath gas pressure to",i,"psi")
        propB.chA.pressure_setpoint.put(i)
        if i==25:
            sleep(30)
        elif i==10:
            sleep(30)
        else:
            sleep(120)
    selectorbox2.valve02.requested_position.put(10)
    print("Switching the sample valve to blocked port 10")
    sleep(180)
    propB.chA.pressure_setpoint.put(0)
    print("liquid line is on a closed port and He gas pressure is at 0 psi")



#def pump_SC1():
#    print ("ensuree the chamber door is securely closed")
