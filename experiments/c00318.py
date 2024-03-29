from subprocess import check_output

import json
import sys
import time
import os

import numpy as np
from hutch_python.utils import safe_load
from ophyd import EpicsSignalRO
from ophyd import EpicsSignal
from bluesky import RunEngine
from bluesky.plans import scan
from bluesky.plans import list_scan
from bluesky.plan_stubs import configure
#from bluesky.plans import list_grid_scan
from ophyd import Component as Cpt
from ophyd import Device
from pcdsdevices.epics_motor import Newport, IMS
from pcdsdevices.interface import BaseInterface
from pcdsdevices.device_types import Trigger
from pcdsdevices.areadetector import plugins
from cxi.db import daq, seq
from cxi.db import camviewer
from cxi.db import RE
from cxi.db import foil_x, foil_y
from cxi.db import cxi_pulsepicker as pp, seq
from cxi.db import bp, bpp, bps
#from cxi.db import cxi_pi1
from cxi.plans import serp_seq_scan
from time import sleep

class ImagerStats3():

    def __init__(self, imager=None):
        try:
            self.imager = imager
            self.prefix = imager.prefix

        except AttributeError:
            self.imager = camviewer.im1l0
            self.prefix = 'IM1L0:XTES:CAM:'
            print('defaulting to IM1L0')
       
        self.initialize()

    def initialize(self):
        self.imager_name = self.prefix[:5]
        self.image_stream = self.prefix + 'IMAGE3:'
        self.image3 = plugins.ImagePlugin(prefix=self.image_stream,
                name=self.imager_name+'_image3', parent=self.imager)
        self.roi = plugins.ROIPlugin(prefix=self.image_stream+'ROI:',
                name=self.imager_name+'_roi', parent=self.image3)
        self.proc = plugins.ProcessPlugin(prefix=self.image_stream+'Proc:',
                name=self.imager_name+'_proc', parent=self.image3)
        self.stats = self.imager.stats3
        self.binX = EpicsSignal(self.image_stream+'ROI:BinX', name='omitted')
        self.binY = EpicsSignal(self.image_stream+'ROI:BinY', name='omitted')
        self.saveBackground = EpicsSignal(self.image_stream+'Proc:SaveBackground', name='omitted') 

    def setImager(self, imager):
        try:
            self.prefix = imager.prefix
        except AttributeError:
            print('Imager not set')

        self.initialize()

    def setup_binning(self, binning):
        self.binX.set(binning)
        self.binY.set(binning)
        self.roi.scale.set(binning**2)

    def prepare(self, take_background=False):

        # set up ports
        self.proc.nd_array_port.set('CAM')
        self.roi.nd_array_port.set('IMAGE3:Proc')
        self.image3.nd_array_port.set('IMAGE3:ROI')
        self.stats.nd_array_port.set('IMAGE3:ROI')

        # set default binning to 2
        self.setup_binning(2)

        # enable all the things
        self.image3.enable.set(1)
        self.roi.enable.set(1)
        self.proc.enable.set(1)

        # make sure camera is acquiring
        self.imager.cam.acquire.put(0, wait=True)
        self.imager.cam.acquire.put(1)

        if take_background:
            self.take_background()

        # apply background
        self.proc.enable_background.set(1)

        # enable stats
        self.stats.compute_statistics.set(1)
        self.stats.compute_centroid.set(1)
        self.stats.enable.set(1)

        # get noise level
        time.sleep(.1)
        sigma = self.stats.sigma.get()

        # set offset to negative sigma
        print(sigma)
        #self.proc.offset.set(-sigma)
        # set threshold to one sigma
        self.stats.centroid_threshold.set(sigma)
        self.stats.bgd_width.put(sigma)

        # switch stats over to ROI stream
        #self.stats.nd_array_port.set('IMAGE3:ROI')


        # set scale and limits
        self.proc.scale.set(1)
        self.proc.low_clip.set(0)
        # disable high clipping for now, but enable low clipping
        self.proc.enable_low_clip.set(1)
        self.proc.enable_high_clip.set(0)
        # apply scale and offset
        self.proc.enable_offset_scale.set(1)

    def get_centroids(self):

        centroids = self.stats.centroid.get()
        centroid_x = centroids.x
        centroid_y = centroids.y

        return centroid_x, centroid_y

    def disable_background(self):
        self.proc.enable_background.set(0)
        self.proc.enable_offset_scale.set(0)
        self.proc.enable_low_clip.set(0)
        self.proc.enable_high_clip.set(0)

    def stop(self):
        self.stats.enable.set(0)

    def take_background(self, num_images=100):
        
        # set minimum number of images to 20
        if num_images <= 20:
            num_images = 20
        
        # turn off background subtraction
        self.proc.enable_background.set(0)
        self.proc.enable_offset_scale.set(0)
        self.proc.enable_low_clip.set(0)
        self.proc.enable_high_clip.set(0)
        
        # turn on averaging
        self.proc.filter_type.set('RecursiveAve')
        self.proc.num_filter.set(num_images)
        # following sets to array n only
        self.proc.filter_callbacks.set(1)
        self.proc.auto_reset_filter.set(1)
        self.proc.enable_filter.set(1)

        # wait until we have at least one averaged image
        print('waiting for averaging to finish...')
        if self.proc.num_filtered.get() < 10:
            while self.proc.num_filtered.get() <= 10:
                time.sleep(.1)
                #print(self.proc.num_filtered.get())
            while self.proc.num_filtered.get() > 10:
                time.sleep(.1)
                #print(self.proc.num_filtered.get())
        else:
            while self.proc.num_filtered.get() > 10:
                time.sleep(.1)
                #print(self.proc.num_filtered.get())
        print('finished acquiring')
        # save background
        #self.proc.save_background.set(1)
        self.saveBackground.set(1)

        # turn off averaging
        self.proc.enable_filter.set(0)


class ImagerHdf5():
    def __init__(self, imager=None):
        try:
            self.imagerh5 = imager.hdf51
            self.imager = imager.cam
        except:
            self.imagerh5 = None
            self.imager = None
            
    def setImager(self, imager):
        self.imagerh5 = imager.hdf51
        self.imager = imager.cam
        
    def stop(self):
        self.imagerh5.enable.set(0)

    def status(self):
        print('Enabled',self.imagerh5.enable.get())
        print('File path',self.imagerh5.file_path.get())
        print('File name',self.imagerh5.file_name.get())
        print('File template (should be %s%s_%d.h5)',self.imagerh5.file_template.get())

        print('File number',self.imagerh5.file_number.get())
        print('Frame to capture per file',self.imagerh5.num_capture.get())
        print('autoincrement ',self.imagerh5.auto_increment.get())
        print('file_write_mode ',self.imagerh5.file_write_mode.get())
        #IM1L0:XTES:CAM:HDF51:Capture_RBV 0: done, 1: capturing
        print('captureStatus ',self.imagerh5.capture.get())

    def prepare(self, baseName=None, pathName=None, nImages=None, nSec=None):
        if self.imagerh5.enable.get() != 'Enabled':
            self.imagerh5.enable.put(1)
        iocdir=self.imager.prefix.split(':')[0].lower()
        if pathName is not None:
            self.imagerh5.file_path.set(pathName)
        elif len(self.imagerh5.file_path.get())==0:
            #this is a terrible hack.
            iocdir=self.imager.prefix.split(':')[0].lower()
            camtype='opal'
            if (self.imager.prefix.find('PPM')>0): camtype='gige'
            self.imagerh5.file_path.put('/reg/d/iocData/ioc-%s-%s/images/'%(iocdir, camtype))
        if baseName is not None:
            self.imagerh5.file_name.put(baseName)
        else:
            expname = check_output('get_curr_exp').decode('utf-8').replace('\n','')
            try:
                lastRunResponse = check_output('get_lastRun').decode('utf-8').replace('\n','')
                if lastRunResponse == 'no runs yet': 
                    runnr=0
                else:
                    runnr = int(check_output('get_lastRun').decode('utf-8').replace('\n',''))
            except:
                runnr = 0
            self.imagerh5.file_name.put('%s_%s_Run%03d'%(iocdir,expname, runnr+1))

        self.imagerh5.file_template.put('%s%s_%d.h5')
        #check that file to be written does not exist
        already_present = True
        while (already_present):
            fnum = self.imagerh5.file_number.get()
            fname = self.imagerh5.file_path.get() + self.imagerh5.file_name.get() + \
                    '_%d'%fnum + '.h5'
            if os.path.isfile(fname):
                print('File %s already exists'%fname)
                self.imagerh5.file_number.put(1 + fnum)
                time.sleep(0.2)
            else:
                already_present = False

        self.imagerh5.auto_increment.put(1)
        self.imagerh5.file_write_mode.put(2)
        if nImages is not None:
            self.imagerh5.num_capture.put(nImages)
        if nSec is not None:
            if self.imager.acquire.get() > 0:
                rate = self.imager.array_rate.get()
                self.imagerh5.num_capture.put(nSec*rate)
            else:
                print('Imager is not acquiring, cannot use rate to determine number of recorded frames')

    def write(self, nImages=None):
        if nImages is not None:
            self.imagerh5.num_capture.put(nImages)
        if self.imager.acquire.get() == 0:
            self.imager.acquire.put(1)
        self.imagerh5.capture.put(1)

    def write_wait(self, nImages=None):
        while (self.imagerh5.num_capture.get() > 
               self.imagerh5.num_captured.get()):
            time.sleep(0.25)

    def write_stop(self):
        self.imagerh5.capture.put(0)

class ImagerStats():
    def __init__(self, imager=None):
        try:
            self.imager = imager.cam
            self.imgstat = imager.stats1
        except:
            self.imager = None
            self.imgstat = None
            
    def setImager(self, imager):
        self.imager = imager.cam
        self.imgstat = imager.stats1

    def stop(self):
        self.imgstat.enable.set(0)

    def setThreshold(self, inSigma=1):
        self.imgstat.enable.set(1)
        computeStat = self.imgstat.compute_statistics.get()
        self.imgstat.compute_statistics.set(1)
        mean = self.imgstat.mean_value.get()
        sigma = self.imgstat.sigma.get()
        self.imgstat.centroid_threshold.set(mean+sigma*nSigma)
        self.imgstat.compute_statistics.set(computeStat)

    def prepare(self, threshold=None, thresholdSigma=None):
        self.imager.acquire.set(1)
        if self.imgstat.enable.get() != 'Enabled':
            self.imgstat.enable.set(1)
        if thresholdSigma is not None:
            self.setThreshold(inSigma=thresholdSigma)
            self.imgstat.centroid_threshold.set(threshold)
        elif threshold is not None:
            if self.imgstat.compute_centroid.get() != 'Yes':
                self.imgstat.compute_centroid.set(1)
            self.imgstat.centroid_threshold.set(threshold)
        self.imgstat.compute_profiles.set(1)
        self.imgstat.compute_centroid.set(1)

    def status(self):
        print('enabled:', self.imgstat.enable.get())
        if self.imgstat.enable.get() == 'Enabled':
            if self.imgstat.compute_statistics.get() == 'Yes':
                #IM1L0:XTES:CAM:Stats1:MeanValue_RBV
                #IM1L0:XTES:CAM:Stats1:SigmaValue_RBV
                print('Mean', self.imgstat.mean_value.get())
                print('Sigma', self.imgstat.sigma.get())
            if self.imgstat.compute_centroid.get() == 'Yes':
                print('Threshold', self.imgstat.centroid_threshold.get())
                #IM1L0:XTES:CAM:Stats1:CentroidX_RBV
                #IM1L0:XTES:CAM:Stats1:CentroidY_RBV
                #IM1L0:XTES:CAM:Stats1:SigmaX_RBV
                #IM1L0:XTES:CAM:Stats1:SigmaY_RBV
                print('X,y', self.imgstat.centroid.get())
                print('sigma x', self.imgstat.sigma_x.get())
                print('sigma y', self.imgstat.sigma_y.get())
            if self.imgstat.compute_profile.get() == 'Yes':
                #IM1L0:XTES:CAM:Stats1:CursorX
                #IM1L0:XTES:CAM:Stats1:CursorY
                print('profile cursor values: ',self.imgstat.cursor.get())
                #IM1L0:XTES:CAM:Stats1:ProfileAverageX_RBV
                #IM1L0:XTES:CAM:Stats1:ProfileAverageY_RBV
                #IM1L0:XTES:CAM:Stats1:ProfileThresholdX_RBV
                #IM1L0:XTES:CAM:Stats1:ProfileThresholdY_RBV
                #IM1L0:XTES:CAM:Stats1:ProfileCentroidX_RBV
                #IM1L0:XTES:CAM:Stats1:ProfileCentroidY_RBV
                #IM1L0:XTES:CAM:Stats1:ProfileCursorX_RBV
                #IM1L0:XTES:CAM:Stats1:ProfileCursorY_RBV
                print('profile cursor: ',self.imgstat.profile_cursor.get())
                print('profile centroid: ',self.imgstat.profile_centroid.get())
                if self.imgstat.compute_centroid.get() == 'Yes':
                    print('profile threshold: ',self.imgstat.profile_threshold.get())
                    print('profile avergage: ',self.imgstat.profile_average.get())

class AT1L0(BaseInterface, Device):
    energy = EpicsSignalRO('SATT:FEE1:320:ETOA.E', kind='config')
    attenuation = EpicsSignalRO('SATT:FEE1:320:RACT', kind='hinted')
    transmission = EpicsSignalRO('SATT:FEE1:320:TACT', name='normal')
    r_des = EpicsSignal('SATT:FEE1:320:RDES', name='normal')
    r_floor = EpicsSignal('SATT:FEE1:320:R_FLOOR', name='omitted')
    r_ceiling = EpicsSignal('SATT:FEE1:320:R_CEIL', name='omitted')
    trans_floor = EpicsSignal('SATT:FEE1:320:T_FLOOR', name='omitted')
    trans_ceiling = EpicsSignal('SATT:FEE1:320:T_CEIL', name='omitted')
    go = EpicsSignal('SATT:FEE1:320:GO', name='omitted')
    
    def setR(self, att_des, ask=False, wait=True):
        self.att_des.put(att_des)
        if ask:
            print('possible ratios: %g (F) -  %g (C)'%(self.r_floor, self.r_ceiling))
            answer=raw_input('F/C? ')
        if answer=='C':
            self.go.put(2)
            if wait: time.sleep(5)
        else:
            self.go.put(3)
            if wait: time.sleep(5)        

class User():
    def __init__(self):
        self._sync_markers = {0.5:0, 1:1, 5:2, 10:3, 30:4, 60:5, 120:6, 360:7}
        self.evr_pp = Trigger('CXI:R48:EVR:41:TRIG0',name='evr_pp')
        self.crystal_th = Newport('CXI:BER:MCN:03', name='crystal_th')
        self.chamber_z = Newport('CXI:BER:MCN:04', name='chamber_z')
        self.chamber_x = Newport('CXI:BER:MCN:05', name='chamber_x')
        self.sample_x = Newport('CXI:BER:MCN:06', name='sample_x')
        self.sample_y = Newport('CXI:BER:MCN:07', name='sample_y')
        self.sample_z = Newport('CXI:BER:MCN:08', name='sample_z')
        self.pp_delay = EpicsSignal('CXI:R48:EVR:41:TRIG0:TDES', name='pp_delay')
        try:
            self.im1l0_h5 = ImagerHdf5(camviewer.im1l0)
            self.im2l0_h5 = ImagerHdf5(camviewer.im2l0)
            self.im3l0_h5 = ImagerHdf5(camviewer.im3l0)
            self.im4l0_h5 = ImagerHdf5(camviewer.im4l0)
            self.gige13_h5 = ImagerHdf5(camviewer.xpp_gige_13)
            self.im1l0_stats = ImagerStats(camviewer.im1l0)
            self.im2l0_stats = ImagerStats(camviewer.im2l0)
            self.im3l0_stats = ImagerStats(camviewer.im3l0)
            self.im4l0_stats = ImagerStats(camviewer.im4l0)
            self.im1l0_stats3 = ImagerStats3(camviewer.im1l0)
            self.im2l0_stats3 = ImagerStats3(camviewer.im2l0)
            self.im3l0_stats3 = ImagerStats3(camviewer.im3l0)
            self.im4l0_stats3 = ImagerStats3(camviewer.im4l0)
        except:
            self.im1l0_h5 = None
            self.im2l0_h5 = None
            self.im3l0_h5 = None
            self.im4l0_h5 = None
            self.im1l0_stats = None
            self.im2l0_stats = None
            self.im3l0_stats = None
            self.im4l0_stats = None
            self.im1l0_stats3 = None
            self.im3l0_stats3 = None
            self.im4l0_stats3 = None
            self.at2l0 = None
        self.at1l0 = AT1L0(name='at1l0')

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


    def takeRun(self, nEvents, record=True):
        daq.configure(events=120, record=record)
        daq.begin(events=nEvents)
        daq.wait()
        daq.end_run()

    def get_ascan(self, motor, start, end, nsteps, nEvents, record=True):
        daq.configure(nEvents, record=record, controls=[motor])
        return scan([daq], motor, start, end, nsteps)

    def get_dscan(self, motor, start, end, nsteps, nEvents, record=True):
        daq.configure(nEvents, record=record)
        currPos = motor.wm()
        return scan([daq], motor, currPos+start, currPos+end, nsteps)

    def ascan(self, motor, start, end, nsteps, nEvents, record=True):
        daq.configure(nEvents, record=record, controls=[motor])
        RE(scan([daq], motor, start, end, nsteps))

    def listscan(self, motor, posList, nEvents, record=True):
        daq.configure(nEvents, record=record, controls=[motor])
        RE(list_scan([daq], motor, posList))

    def dscan(self, motor, start, end, nsteps, nEvents, record=True):
        daq.configure(nEvents, record=record, controls=[motor])
        currPos = motor.wm()
        RE(scan([daq], motor, currPos+start, currPos+end, nsteps))

    def setupSequencer(self, flymotor, distance, deltaT_shots, pp_shot_delay=2):
        ## Setup sequencer for requested rate
        #sync_mark = int(self._sync_markers[self._rate])
        #leave the sync marker: assume no dropping.
        sync_mark = int(self._sync_markers[120])
        seq.sync_marker.put(sync_mark)
        #seq.play_mode.put(0) # Run sequence once
        seq.play_mode.put(1) # Run sequence N Times
    
        # Determine the different sequences needed
        beamDelay = int(120*deltaT_shots)-pp_shot_delay
        if (beamDelay+pp_shot_delay)<4:
            print('PP cannot go faster than 40 Hz in flip-flip mode, quit!')
            return
        fly_seq = [[185, beamDelay, 0, 0],
                   [187, pp_shot_delay, 0, 0]]
        #logging.debug("Sequence: {}".format(fly_seq))                  

        #calculate how often to shoot in requested distance
        flyspeed = flymotor.velocity.get()
        flytime = distance/flyspeed
        flyshots = int(flytime/deltaT_shots)
        seq.rep_count.put(flyshots) # Run sequence N Times

        seq.sequence.put_seq(fly_seq) 

    def setPP_flipflip(self, nshots=20, deltaShots=30):
        ## Setup sequencer for requested rate
        #sync_mark = int(self._sync_markers[self._rate])
        #leave the sync marker: assume no dropping.
        sync_mark = int(self._sync_markers[120])
        seq.sync_marker.put(sync_mark)
        #seq.play_mode.put(0) # Run sequence once
        seq.play_mode.put(1) # Run sequence N Times
        seq.rep_count.put(nshots) # Run sequence N Times
    
        # Determine the different sequences needed
        beamDelay = int(delta_shots)-pp_shot_delay
        if (beamDelay+pp_shot_delay)<4:
            print('PP cannot go faster than 40 Hz in flip-flip mode, quit!')
            return
        ff_seq = [[185, beamDelay, 0, 0],
                   [187, pp_shot_delay, 0, 0]]
        #logging.debug("Sequence: {}".format(fly_seq))                  
        seq.sequence.put_seq(ff_seq) 

    def set_pp_flipflop(self):
        pp.flipflop(wait=True)

    def runflipflip(self, start, end, nsteps,nshots=20, deltaShots=30):
        self.set_pp_flipflop()
        #self.setPP_flipflip(nshots=20, deltaShots=6)
        for i in nsteps:
            self.evr_pp.ns_delay.set(start+delta*i)
            seq.start()
            time.sleep(5)

    def run_evr_seq_scan(self, start, env, nsteps, record=None, use_l3t=None):
        """RE the plan."""
        self.set_pp_flipflop()
        RE(evr_seq_plan(daq, seq, self.evr_pp, start, env, nsteps,
                        record=record, use_l3t=use_l3t))

    def evr_seq_plan(self, daq, seq, evr, start, end, nsteps,
                     record=None, use_l3t=None):
        """Configure daq and do the scan, trust other code to set up the sequencer."""
        yield from configure(daq, events=None, duration=None, record=record,
                             use_l3t=use_l3t, controls=[evr])
        yield from scan([daq, seq], evr, start, end, nsteps)

    def run_serp_seq_scan(self, shiftStart, shiftStop, shiftSteps, flyStart, flyStop, deltaT_shots, record=False, pp_shot_delay=2):
        daq.disconnect() #make sure we start from fresh point.
        shiftMotor=foil_x
        flyMotor=foil_y
        self.setupSequencer(flyMotor, abs(flyStop-flyStart), deltaT_shots, pp_shot_delay=pp_shot_delay)
        daq.configure(-1, record=record, controls=[foil_x, foil_y])
        #daq.begin(-1)
            
        if isinstance(shiftSteps, int):
             RE(serp_seq_scan(shiftMotor, np.linspace(shiftStart, shiftStop, shiftSteps), flyMotor, [flyStart, flyStop], seq))
        else:
             RE(serp_seq_scan(shiftMotor, np.arange(shiftStart, shiftStop, shiftSteps), flyMotor, [flyStart, flyStop], seq))

        #daq.end()

    def dumbSnake(self, xmotor, ymotor, xStart, xEnd, yDelta, nRoundTrips, sweepTime):
        """ 
        simple rastering for running at 120Hz with shutter open/close before
        and after motion stop.
         
        Need some testing how to deal with intermittent motion errors.
        """
#        class cxi_pi1:
#            x = IMS('CXI:PI1:MMS:01',name='cxi_pi1__x')
#            y = IMS('CXI:PI1:MMS:02',name='cxi_pi1__y')
        xmotor.umv(xStart)
        daq.connect()
        daq.begin()
        sleep(2)
        print('Reached horizontal start position')
        # looping through n round trips
        for i in range(nRoundTrips):
            try:
                print('starting round trip %d' % (i+1))
                xmotor.mv(xEnd)
                sleep(0.1)
                pp.open()
                sleep(sweepTime)
                pp.close()
                xmotor.wait()
                ymotor.mvr(yDelta)
                sleep(1.2)#orignal was 1
                xmotor.mv(xStart)
                sleep(0.1)
                pp.open()
                sleep(sweepTime)
                pp.close()
                xmotor.wait()
                ymotor.mvr(yDelta)
                print('ypos',ymotor.wm())
                sleep(1.2)#original was 1
            except:
                print('round trip %d didn not end happily' % i)
        daq.end_run()
        daq.disconnect()


    #def run_serp_seq_scan_expl(self, yStart, yStop, ySteps, flyStart, flyStop, deltaT_shots, record=False, pp_shot_delay=1):
    #    daq.disconnect() #make sure we start from fresh point.
    #    self.setupSequencer(foil_y, abs(flyStop-flyStart), deltaT_shots, pp_shot_delay=pp_shot_delay)
    #    daq.configure(-1, record=record, controls=[foil_x, foil_y])
        #daq.begin(-1)
            
    #    if isinstance(ySteps, int):
    #         RE(serp_seq_scan(foil_x, np.linspace(yStart, yStop, ySteps), foil_y, [flyStart, flyStop], seq))
    #    else:
    #         RE(serp_seq_scan(foil_x, np.arange(yStart, yStop, ySteps), foil_y, [flyStart, flyStop], seq))
     #   #daq.end()
