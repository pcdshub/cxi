from hutch_python.utils import safe_load

from jet_tracking.devices import Injector, Diffract
from jet_tracking.devices import Questar, Parameters
from jet_tracking.devices import Offaxis, OffaxisParams
from jet_tracking.jet_control import JetControl

#from cxi.db import cxi
from cxi.db import cxi_pulsepicker
#from cxi.db import daq
try:
    def adaq_repeat(seconds=600):
	    while True:
		    daq.begin(duration=seconds, record=True, wait=True,end_run=True)
		

except KeyboardInterrupt:
    daq.end_run()
    daq.disconnect()

#defining pv for DsdCspad total intensity from shared memory
from pcdsdevices.device_types import IMS
from epics import PV
sc3_DsdCspad_intensity=PV('CXI:SC3:DIFFRACT:TOTAL_ADU')

#making the cxi_pulsepicker something that can be monitored by jet tracking
cxi_pulsepicker_state=PV('XRT:DIA:MMS:16:READ_DF')

#defining quick CSPAD optimization function
#tot_intensity=0
import matplotlib.pyplot as plt
from time import sleep
import statistics as stat 

def chase_jet(scale="Fine"):
    pi3_x=IMS('CXI:PI3:MMS:01',name='pi3_x')
    pi3_fine_x=IMS('CXI:PI3:MMS:04',name='pi3_fine_x')
    x_min=0.0012
    if scale=="Coarse":
        steps=50
        x_step=(-1)*steps*x_min/2
        mot=pi3_x
        accum=20
    elif scale=="Fine":
        steps=20
        x_step=(-1)*steps*x_min/2
        mot=pi3_x
        accum=20

    else:
        scale=="WAG"
        steps=50
        x_min=0.03
        x_step=(-1)*steps*x_min/2
        mot=pi3_fine_x
        accum=40

    sc3_x_pos=[]
    dsd_intensity=[]
    x_start=mot.user_readback.get()
    mot.mvr(x_step,wait=True)
#    tot_intensity=0
    for i in range(steps):
        mot.mvr(x_min, wait=True)
        sc3_x_pos.append(mot.user_readback.get())
        for j in range(20):
            tot_intensity=0
            intensity=sc3_DsdCspad_intensity.get()
            tot_intensity=tot_intensity+intensity
        dsd_intensity.append(tot_intensity)
    plt.plot(sc3_x_pos,dsd_intensity)
    best_x=dsd_intensity.index(max(dsd_intensity))
    mot.mv(sc3_x_pos[best_x])
    high=max(dsd_intensity)
    low=min(dsd_intensity)
    ratio=abs(high/low)
    std=stat.stdev(dsd_intensity)
    print("standard deviation in Dsd intensity: ",std)
    print("ratio of max and min Dsd intensities to standard deviation: ", (high/std,low/std))
    print(ratio)
    if ratio >= 2:
        print("Scan seems successful, will move to optimum x position")
        mot.mv(sc3_x_pos[best_x],wait=True)
        if scale=="Fine":
            print("Scan looks successful.  Moving to monitoring")
            JetState.trigger=1
        else:
            print("Doing a fine scan quickly to better find optimum")
            JetState.trigger=2
    else:
        mot.mv(x_start,wait=True)
        if scale=="Coarse":
            print("Will need to do a WAG scan")
            JetState.trigger=3
        elif scale=="Fine":
            print("Fine scan was unsuccessful.  Will need to do a Coarse scan")
            JetState.trigger=0
        else:
            print("Something seems wrong.  The Wild Ass Guess scan was unsuccessful.  Aborting")
            exit
    

    
#    if scale=="Fine":
#        high=max(dsd_intensity)
#        low=min(dsd_intensity)
#        ratio=high/low
#        print(ratio)
#        low=low*3
#        if high <= low:
#            JetState.trigger=0
#        else:
#            JetState.trigger=1
#    else:
#        JetState.trigger=1


class JetState(object):
    trigger=0
#    threshhold=0.85
    def __init__(self, threshold = 0.85, scale = 'Fine'):
        self.scale = 'Fine'
        self.threshold = threshold
        self.trigger = 0
    def chase(self):
        return chase_jet(self.scale)
    def monitor(self):
        return monitor_jet(self.threshold)
    def tracking(self):
        return tracking_jet(self.trigger)
    #TODO: make a function that loops state?


def monitor_jet(threshhold=0.85):
#now make the total intensity buffer for the jet_monitor
    #global trigger
    tot_intensity=0
    for i in range(50):
        intensity=sc3_DsdCspad_intensity.get()
        tot_intensity=tot_intensity+intensity
        sleep(0.1)
    print(tot_intensity)
    buffer_intensity=0
    curr_intensity=tot_intensity+1000000
    buffer_intensity=tot_intensity*threshhold
    while buffer_intensity<=curr_intensity:
        new_intensity=0
        if cxi_pulsepicker_state.get()==1:
            print("Pulse picker is closed, will pause monitoring until it is open")            
            sleep(10)
        else:
            for j in range(50):
                if cxi_pulsepicker_state.get()==1:
                    sleep(10)
                    print("Pulse picker is closed, will pause monitoring until it is open")
                else:
                    intensity=intensity=sc3_DsdCspad_intensity.get()
                    new_intensity=new_intensity+intensity
    #               print(tot_intensity,new_intensity)
                    sleep(0.1)
            curr_intensity=new_intensity
        print(buffer_intensity,curr_intensity)
        if curr_intensity >= tot_intensity:
            tot_intensity=curr_intensity
            buffer_intensity=tot_intensity*threshhold
            print("The buffer intensity was increased to" "buffer_intensity")
##print(total_intensity,curr_intensity)
    print("the current intensity has dropped below the buffer, so I will chase the jet")
    JetState.trigger=2
#    chase_jet()

def tracking_jet(trigger=0):
    while True:
        trigger=JetState.trigger
        if trigger==0:
            chase_jet("Coarse")

        if trigger==1:
            monitor_jet()
                                                
        if trigger==2:
            chase_jet("Fine")

        if trigger==3:
            chase_jet("WAG")


#defining positions for the sc1_sample_x motor so that we can quickly move the x motor to the proper position
from pcdsdevices.device_types import IMS
sc1_led = IMS('CXI:SC1:MMS:18', name='sc1_led')
sc1_sample_x = IMS('CXI:SC1:MMS:02',name='sc1_sample_x')

def safe_samplex(position="Out"): 
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
                
        
def hplc2_clear_error():
    hplc2_error=PV('CXI:LC20:SDSB:ClearError.PROC')
    state=hplc2_error.get()
    if state==1:
        hplc2_error.put(1)
    else:
        hplc2_error.put(0)
        
def hplc2_resume():
    hplc2_error=PV('CXI:LC20:SDSB:ClearError.PROC')
    state=hplc2_error.get()
    if state==1:
        hplc2_error.put(1)
    else:
        hplc2_error.put(0)
    hplc2_status=PV('CXI:LC20:SDSB:Run')
    hplc2_status.put(1)


#def adaq_fixed_runs(runtime, darktime = 0):
#	print "Run time =" run_time
#	print "Dark time =" dark_time
#	while True:
#		if darktime > 0:
#			cxi.pulsepicker.open(wait=True)
#			daq.record(duration=run_time, wait=True)
#			daq.end_run()

#		else:
#			cxi.pulsepicker.close(wait=True)
#			daq.record(duration=darktime, wait=True)
#			cxi.pulsepicker.open(wait=True)
#			daq.record(duration=runtime,wait=True)
#			daq.end_run()

if True:
    with safe_load('PI1_injector'):
        PI1 = {'name': 'PI1_injector',
               'coarseX': 'CXI:PI1:MMS:01',
               'coarseY': 'CXI:PI1:MMS:02',
               'coarseZ': 'CXI:PI1:MMS:03',
               'fineX': 'CXI:USR:MMS:01',
               'fineY': 'CXI:USR:MMS:02',
               'fineZ': 'CXI:USR:MMS:03'}
        PI1_injector = Injector(**PI1)

    with safe_load('SC1_questar'):
        SC1_questar_ports = {'ROI_port': 'ROI1',
                             'ROI_stats_port': 'Stats1',
                             'ROI_image_port': 'IMAGE1'}
        SC1_questar = Questar(**SC1_questar_ports, prefix='CXI:SC1:INLINE', name='SC1_questar')

    with safe_load('SC1_params'):
        SC1_params = Parameters(prefix='CXI:SC1:INLINE', name='SC1_params')

    with safe_load('SC1_diffract'):
        SC1_diffract = Diffract(prefix='CXI:SC1:DIFFRACT', name='SC1_diffract')

    with safe_load('SC1_control'):
        SC1_control = JetControl('SC1_control', 
                PI1_injector, SC1_questar, SC1_params, SC1_diffract)

if False:
    with safe_load('PI2_injector'):
        PI2 = {'name': 'PI2_injector',
               'coarseX': 'CXI:PI2:MMS:01',
               'coarseY': 'CXI:PI2:MMS:02',
               'coarseZ': 'CXI:PI2:MMS:03',
               'fineX': 'CXI:PI2:MMS:04',
               'fineY': 'CXI:PI2:MMS:05',
               'fineZ': 'CXI:PI2:MMS:06'}
        PI2_injector = Injector(**PI2)

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
        SC2_params = Parameters(prefix='CXI:SC2:INLINE', name='SC2_params')

    with safe_load('SC2_paroffaxis'):
        SC2_paroffaxis = OffaxisParams(prefix='CXI:SC2:OFFAXIS', name='SC2_paroffaxis')

    with safe_load('SC2_diffract'):
        SC2_diffract = Diffract(prefix='CXI:SC2:DIFFRACT', name='SC2_diffract')

    with safe_load('SC2_control'):
        SC2_control = JetControl('SC2_control', 
                PI2_injector, SC2_questar, SC2_params, SC2_diffract)


if True:
    with safe_load('PI3_injector'):
        PI3 = {'name': 'PI3_injector',
               'coarseX': 'CXI:PI3:MMS:01',
               'coarseY': 'CXI:PI3:MMS:02',
               'coarseZ': 'CXI:PI3:MMS:03',
               'fineX': 'CXI:PI3:MMS:04',
               'fineY': 'CXI:PI3:MMS:05',
               'fineZ': 'CXI:PI3:MMS:06'}
        PI3_injector = Injector(**PI3)

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
        SC3_params = Parameters(prefix='CXI:SC3:INLINE', name='SC3_params')

    with safe_load('SC3_paroffaxis'):
        SC3_paroffaxis = OffaxisParams(prefix='CXI:SC3:OFFAXIS', name='SC3_paroffaxis')

    with safe_load('SC3_diffract'):
        SC3_diffract = Diffract(prefix='CXI:SC3:DIFFRACT', name='SC3_diffract')

    with safe_load('SC3_control'):
        SC3_control = JetControl('SC3_control', 
                PI3_injector, SC3_questar, SC3_params, SC3_diffract)



with safe_load("imprint scans"):
    from cxi.imprint import imprint_row, sequencer, beam_stats


from ophyd import Device, Component as Cpt, EpicsSignal, EpicsSignalRO

class GX_readback(Device):     
    description = Cpt(EpicsSignal, 'PressSP.DESC')
    pressure_setpoint = Cpt(EpicsSignal, 'PressSP')
    pressure_value = Cpt(EpicsSignalRO, 'PRESS')
    status = Cpt(EpicsSignal, 'Enable')
    limit = Cpt(EpicsSignal, 'HiPressLimit')

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
        self.status.put(inStatus)
        return self.status.get()
    
    def set_pressure_limit(self, inLimit):
        self.limit.put(inLimit)        
        return self.limit.get()
  

    def set_description(self, inDescription="NOPE"):
        self.description.put(inDescription)
        return self.description.get()        
        
class Proportionair(Device):
    chA = Cpt(GX_readback, '01:')
    chB = Cpt(GX_readback, '02:')
#    def __init__(self, inPressure = 0.0, inStatus=1):
#        self.pressure_setpoint = inPressure
#        self.status = inStatus
    
prop_b = Proportionair('CXI:SDS:PCM:B:', name='prop_b')

class SDS(Device):     
    status_setpoint = Cpt(EpicsSignal, 'Run')    
    status_value = Cpt(EpicsSignalRO, 'Status')
    flowrate_setpoint = Cpt(EpicsSignal, 'SetFlowRate')
    flowrate_setpoint_value = Cpt(EpicsSignalRO, 'FlowRate')
    measured_flowrate = Cpt(EpicsSignal, 'FlowRateSP' )    
    limit_setpoint = Cpt(EpicsSignal, 'SetMaxPress')    
    limit_value = Cpt(EpicsSignalRO, 'MaxPress')

#    def __init__(self, inFlowrate = 0.0, inStatus=1):
#        self.pressure_setpoint = inPressure
#        self.status = inStatus
    
    def set_flowrate_setpoint(self, inFlowrate):
        if inFlowrate >= 0.1:
            print("The units are mL/min so verify you really want this flowrate")
        if inFlowrate < 0:
            print("Stop being stupid, flowrate shouldn't be negative.  Setting the flowrate to 0")
            inFlowrate = 0
        self.flowrate_setpoint.put(inFlowrate)
        return self.flowrate_value.get()
        
    def set_status(self, inStatus):
        self.status_setpoint.put(inStatus)
        return self.status_value.get()
    
    def set_pressure_limit(self, inLimit):
        self.limit_setpoint.put(inLimit)        
        return self.limit_value.get()
    
sds_A = SDS('CXI:LC20:SDS:',name='sds_A')
sds_B = SDS('CXI:LC20:SDSB:',name='sds_B')
