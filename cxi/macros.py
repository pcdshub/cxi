from hutch_python.utils import safe_load

from jet_tracking.devices import JTInput, JTOutput, JTFake
import subprocess
import sys

from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO, AreaDetector
from pcdsdevices.device_types import PulsePicker

import matplotlib.pyplot as plt
from time import sleep
import statistics as stat 

from pcdsdevices.device_types import IMS
from epics import PV

#from cxi.db import cxi
from cxi.db import cxi_pulsepicker
#from cxi.db import daq

##making the cxi_pulsepicker something that can be monitored by jet tracking
#cxi_pulsepicker_state=PV('CXI:DIA:MMS:16:READ_DF')

class Jet_chaser(Device):
    sc3_broad_x = Cpt(IMS,':PI3:MMS:01')    
    sc3_fine_x = Cpt(IMS, ':PI3:MMS:04')
    DsdCspad_intensity= Cpt(EpicsSignalRO, ':SC3:DIFFRACT:TOTAL_ADU')
    jet_x_pos=[]
    det_intensity=[]
    tot_intensity=0
    accumulation=60
    trigger = 0
    chamber = 3
    
    def scan_jet(self, inScale="Fine"):
        if inScale=="Coarse":
            x_min=0.0012        
            steps=50
            x_step=(-1)*steps*x_min/2
            mot = self.sc3_broad_x
               
        elif inScale=="Fine":
            x_min=0.0012        
            steps=20
            x_step=(-1)*steps*x_min/2
            mot = self.sc3_broad_x
            
        else:
            inScale=="WAG"
            steps=50
            x_min=0.03
            x_step=(-1)*steps*x_min/2
            mot = self.sc3_fine_x
            x_start=mot.user_readback.get()
        
        mot.mvr(x_step,wait=True)            
        self.det_intensity=[]   
        self.jet_x_pos=[]
    #    tot_intensity=0
        for i in range(steps):
            mot.mvr(x_min, wait=True)
            self.jet_x_pos.append(mot.user_readback.get())
            for j in range(self.accumulation):
                tot_intensity=0
                intensity=self.DsdCspad_intensity.get()
                tot_intensity+=intensity
            self.det_intensity.append(tot_intensity)
        plt.plot(self.jet_x_pos,self.det_intensity)
        best_x=self.det_intensity.index(max(self.det_intensity))
        mot.mv(self.jet_x_pos[best_x])
        high=max(self.det_intensity)
        low=min(self.det_intensity)
        ratio=abs(high/low)
        std=stat.stdev(self.det_intensity)
        print("standard deviation in detector intensity: ",std)
        print("ratio of max and min detector intensities to standard deviation: ", (high/std,low/std))
        print(ratio)
        if ratio >= 1:
            print("Scan seems successful, will move to optimum x position")
            mot.mv(self.jet_x_pos[best_x],wait=True)
            if inScale=="Fine":
                print("Scan looks successful.  Moving to monitoring")
                self.trigger=1
            else:
                print("Doing a fine scan quickly to better find optimum")
                self.trigger=2
        else:
            mot.mv(x_start,wait=True)
            if inScale=="Coarse":
                print("Will need to do a WAG scan")
                self.trigger=3
            elif inScale=="Fine":
                print("Fine scan was unsuccessful.  Will need to do a Coarse scan")
                self.trigger=0
            else:
                print("Something seems wrong.  The Wild Ass Guess scan was unsuccessful.  Aborting")
                exit
                
    def monitor_jet(self,inThreshhold=0.75, **kwargs):
    #now make the total intensity buffer for the jet_monitor
        #global trigger
        tot_intensity=0
        nevents=120
        for i in range(nevents):
            intensity=self.DsdCspad_intensity.get()
            tot_intensity+=intensity
            sleep(0.1)
        print(tot_intensity)
        buffer_intensity=0
        curr_intensity=tot_intensity+1000000
        buffer_intensity=tot_intensity*inThreshhold
        while buffer_intensity<=curr_intensity:
            new_intensity=0
            if cxi_pulsepicker_state.get()==1:
                print("Pulse picker is closed, will pause monitoring until it is open")            
                sleep(10)
            else:
                for j in range(nevents):
                    if cxi_pulsepicker_state.get()==1:
                        sleep(10)
                        print("Pulse picker is closed, will pause monitoring until it is open")
                    else:
                        intensity=self.DsdCspad_intensity.get()
                        new_intensity+=intensity
        #               print(tot_intensity,new_intensity)
                        sleep(0.1)
                curr_intensity=new_intensity
            print(buffer_intensity,curr_intensity)
            if curr_intensity >= tot_intensity:
                tot_intensity=curr_intensity
                buffer_intensity=tot_intensity*inThreshhold
                print("The buffer intensity was increased to " "buffer_intensity")
    ##print(total_intensity,curr_intensity)
        print("the current intensity has dropped below the buffer, so I will chase the jet")
        self.trigger=2            
    
                
    def tracking_jet(self,inTrigger=0):
        self.trigger = inTrigger

        while True:
            
            if self.trigger == 0:
                self.scan_jet(inScale="Coarse")
    
            if self.trigger == 1:
                self.monitor_jet()
                                                    
            if self.trigger == 2:
                self.scan_jet(inScale="Fine")
    
            if self.trigger == 3:
                self.scan_jet(inScale="WAG")
        

def safe_samplex(position="Out"): 
    if ds1_z_distance <= -300:
        ds1_z_position.umv(-250,wait=True)
    if position == "Out":
        sc1_sample_x.umv_Out()
        print("Moving to the Out position")
    else:
        if position == "Diode":
            sc1_led.umv_Out()
            sc1_sample_x.umv_Diode()
            print("Moving to the Diode position")
        else:
            if position == "Mirror":
                sc1_led.umv_Out()
                sc1_sample_x.umv_Mirror()
                print("Moving to the Mirror position")
            else:
                print("You did not select a valid argument.  The options are Out, Diode, Mirror")
                

class GX_readback(Device):     
    description = Cpt(EpicsSignal, ':PressSP.DESC')
    pressure_setpoint_value = Cpt(EpicsSignal, ':Setpoint_RBV')
    pressure_setpoint = Cpt(EpicsSignal, ':Setpoint')
    pressure_value = Cpt(EpicsSignalRO, ':Pressure_RBV')
    status_setpoint = Cpt(EpicsSignal, ':Enable')
    status_value = Cpt(EpicsSignal, ':Enable_RBV')
    high_limit_value = Cpt(EpicsSignal, ':HighLimit_RBV')
    high_limit_setpoint = Cpt(EpicsSignal, ':HighLimit')
    low_limit_value = Cpt(EpicsSignal, ':LowLimit_RBV')
    low_limit_setpoint = Cpt(EpicsSignal, ':LowLimit')

#    def __init__(self, inPressure = 0.0, inStatus=1):
#        self.pressure_setpoint = inPressure
#        self.status = inStatus
    
    def set_pressure_setpoint(self, inPressure):
        if inPressure >= 1000:
            print("Max pressure is 1000 psi")
            inPressure = 1000
        if inPressure < 0:
            print("Stop being stupid, pressure shouldn't be negative.  Setting the pressure to 0")
            inPressure = 0
        self.pressure_setpoint.put(inPressure)
        return self.pressure_value.get()
        
    def set_status(self, inStatus):
        self.status_setpoint.put(inStatus)
        return self.status_setpoint.get()
    
    def set_max_pressure_limit(self, inLimit):
        self.high_limit_setpoint.put(inLimit)        
        return self.high_limit_setpoint.get()

    def set_description(self, inDescription="NOPE"):
        self.description.put(inDescription)
        return self.description.get()        
        
        
class Proportionair(Device):
    chA = Cpt(GX_readback, ':PropAir:01')
    chB = Cpt(GX_readback, ':PropAir:02')

#    def __init__(self, inPressure = 0.0, inStatus=1):
#        self.pressure_setpoint = inPressure
#        self.status = inStatus
prop_a = Proportionair('CXI:SDS:PCM:A', name='prop_a')   
prop_b = Proportionair('CXI:SDS:PCM:B', name='prop_b')



class HPLC(Device):     
    status_setpoint = Cpt(EpicsSignal, ':Run')    
    pressure = Cpt(EpicsSignal, ':Pressure')
    status_value = Cpt(EpicsSignalRO, ':Status')
    flowrate_setpoint = Cpt(EpicsSignal, ':SetFlowRate')
    flowrate_value = Cpt(EpicsSignalRO, ':FlowRate')
    flowrate_setpoint_value = Cpt(EpicsSignalRO, ':FlowRateSP' )    
    max_pressure_setpoint = Cpt(EpicsSignal, ':SetMaxPress')    
    max_pressure = Cpt(EpicsSignalRO, ':MaxPress')
    min_pressure_setpoint = Cpt(EpicsSignal,':SetMinPress')
    min_pressure = Cpt(EpicsSignalRO,':MinPress')
    error_state = Cpt(EpicsSignalRO,':Error')
    error_process = Cpt(EpicsSignal, ':ClearError.PROC')
    

#    def __init__(self, *args, **kwargs, inFlowrate = 0.0, inStatus=1):
#        super().__init__(*args, **kwargs)
#        self.pressure_setpoint = inPressure
#        self.status = inStatus
    
    def set_flowrate_setpoint(self, inFlowrate):
        if inFlowrate >= 0.1:
            print("The units are mL/min so verify you really want this flowrate")
        if inFlowrate < 0:
            print("Stop being stupid, flowrate shouldn't be negative.  Setting the flowrate to 0")
            inFlowrate = 0
        self.flowrate_setpoint.put(inFlowrate)
        return self.flowrate_setpoint_value.get()
        
    def set_status(self, inStatus):
        self.status_setpoint.put(inStatus)
        return self.status_value.get()
    
    def set_pressure_limit(self, inLimit):
        self.limit_setpoint.put(inLimit)        
        return self.limit_value.get()
        
    def clear_error(self):
        state=self.error_process.get()
        if state==1:
            self.error_process.put(0)
        else:
            self.error_process.put(1)
        return self.error_state.get()
        
    def hplc2_resume(self):
        self.clear_error()
        self.set_status(1)
        return self.status_value.get() 

#        state=hplc2_error.get()
#        if state==1:
#            hplc2_error.put(0)
#        else:
#            hplc2_error.put(1)
#        hplc2_status=PV('CXI:LC20:SDSB:Run')
#        hplc2_status.put(1)
    
'''
Building the selector boxes with multiple inheritances
Building blocks will be reservoirs, valves, flow meters
'''


class SelectorBoxValve(Device):
    '''
    Selector box used to switch between different samples when running aqueous samples
    
    '''
    current_position = Cpt(EpicsSignalRO,':CurrentPos_RBV')
    requested_position_value = Cpt(EpicsSignalRO, ':ReqPos_RBV')
    requested_position = Cpt(EpicsSignal, ':ReqPos')
    
class SelectorBoxValvePair(SelectorBoxValve):
    valve01 = Cpt(SelectorBoxValve,':Valve:01')
    valve02 = Cpt(SelectorBoxValve,':Valve:02')
    
    
class SelectorBoxReservoirStates(Device):
    unit_converter = Cpt(EpicsSignalRO,':PumpUnitConverter')
    integrator_sub = Cpt(EpicsSignalRO, ':IntegratorSub')
    integrator_source_select = Cpt(EpicsSignal, ':IntegratorSrcSel')
    flow_source_select = Cpt(EpicsSignal, ':FlowSrcSelection')
    integrated_flow = Cpt(EpicsSignalRO, ':IntgFlow')
    starting_volume = Cpt(EpicsSignal, ':StartingVol')
    clear_integrated_flow = Cpt(EpicsSignal, ':ClearIntgFlow')
    clear_integrated_flow_calc = Cpt(EpicsSignal, ':ClearIntgFlowCalc')
    estimated_depletion_time = Cpt(EpicsSignal,':EstDepletionTime')

class SelectorBoxReservoir(SelectorBoxReservoirStates):
    res = Cpt(SelectorBoxReservoirStates, ':RES')    
    res1 = Cpt(SelectorBoxReservoirStates, ':RES:1')
    res2 = Cpt(SelectorBoxReservoirStates, ':RES:2')
    res3 = Cpt(SelectorBoxReservoirStates, ':RES:3')
    res4 = Cpt(SelectorBoxReservoirStates, ':RES:4')
    res5 = Cpt(SelectorBoxReservoirStates, ':RES:5')
    res6 = Cpt(SelectorBoxReservoirStates, ':RES:6')
    res7 = Cpt(SelectorBoxReservoirStates, ':RES:7')
    res8 = Cpt(SelectorBoxReservoirStates, ':RES:8')
    res9 = Cpt(SelectorBoxReservoirStates, ':RES:9')
    res10 = Cpt(SelectorBoxReservoirStates, ':RES:10')
    
class FlowMeter(Device):
    '''
    Capturing the flow meter components of the selector box
    '''
    flow_meter_mode = Cpt(EpicsSignalRO, ':FMMode')
    flow_meter_mode_readback = Cpt(EpicsSignalRO,':FMModeRb')
    flow_meter_reset = Cpt(EpicsSignal, ':FMReset')
    valid_flow = Cpt(EpicsSignalRO, ':FlowValid')
    flow_out_of_range = Cpt(EpicsSignalRO, ':FlowOor')
    measured_flow = Cpt(EpicsSignal, ':Flow')
    
    


class SelectorBox(SelectorBoxValvePair, SelectorBoxReservoir, FlowMeter):
    '''
    Making the larger Selector Box that has the reservoirs, flow meter, etc.)
    '''    
    lock = Cpt(EpicsSignal,':Lock')    
    def coupled_reservoir_switch(self,port=11):
        '''
        option is port.  Default is port 11 (water)
        '''
        if port == "Water":
            port = 11
        elif port =="water":
            port = 11
            
        self.valve01.required_position.put(port)
        self.valve02.required_position.put(port)
        time.sleep(1)
        return self.valve01.current_position.get()
        return self.valve02.current_position.get()
        
    def reservoir_prepressurize(self,port=11):
        '''
        Option is port.  Default is port 11 (water)
        '''
        curr_port = self.valve01.current_position.get()        
        for i in range(10):
            self.valve01.required_position.put(port, wait=True)
            time.sleep(2)
            self.valve01.required_position.put(curr_port, wait=True)
            time.sleep(2)
        self.valve01.required_position.put(port,wait=True)
        time.sleep(1)
        return self.valve01.current_position.get()


'''instantiate the selector box already!'''

selectorbox2 = SelectorBox('CXI:SDS:SELB', name = 'selectorbox2')
selectorbox1 = SelectorBox('CXI:SDS:SELA', name = 'selectorbox1')

    

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
ds1_cspad = Cspad('CXI:D51:MPD',name='ds1_cspad') 



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
dsc_Be_lenses_x_pos = IMS('CXI:DS1:MMS:07',name = 'dsc_Be_lenses_x_pos')
dsc_Be_lenses_y_pos = IMS('CXI:DS1:MMS:08',name = 'dsc_Be_lenses_y_pos')

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

