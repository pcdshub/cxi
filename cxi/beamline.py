from hutch_python.utils import safe_load

from cxi.jet_tracking.devices import Injector, Diffract
from cxi.jet_tracking.devices import Questar, Parameters
from cxi.jet_tracking.devices import Offaxis, OffaxisParams
from cxi.jet_tracking.jet_control import JetControl

#from cxi.db import cxi
from cxi.db import cxi_pulsepicker
from cxi.db import daq
try:
	def adaq_repeat(seconds=10):
		while True:
			daq.begin(duration=seconds, wait=True)
			daq.end_run()

except KeyboardInterrupt:
	daq.end_run()

def adaq_fixed_runs(runtime, darktime = 0):
#	print "Run time =" run_time
#	print "Dark time =" dark_time
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
