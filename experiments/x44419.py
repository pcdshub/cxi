from pcdsdevices.device_types import IMS
from cxi.db import cxi_pulsepicker as pp, seq
from cxi.db import bp, bpp, bps
import logging
import numpy as np
import time

logger = logging.getLogger(__name__)

class User:
    wfs_z = IMS('CXI:DS1:MMS:06',name='wfs_z')
    sample_x = IMS('CXI:SC2:MMS:05',name='sample_x')
    sample_y = IMS('CXI:SC2:MMS:07',name='sample_y')
    sample_z = IMS('CXI:SC2:MMS:06',name='sample_z')
