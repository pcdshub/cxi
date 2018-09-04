from hutch_python.utils import safe_load
from cxi.devices import Injector, Questar, Parameters

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
    port_names = {'ROI_port': 'ROI1',
                  'ROI_stats_port': 'Stats1',
                  'ROI_image_port': 'IMAGE1'}
    SC1_questar = Questar(**port_names, prefix='CXI:SC1:INLINE', name='SC1_questar')

with safe_load('SC1_params'):
    SC1_params = Parameters(prefix='CXI:SC1:ONAXIS', name='SC1_params')
