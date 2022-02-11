## Work In Progress!!

from pcdsdevices.epics_motor import IMS
from ophyd.device import Device, FormattedComponent as Cpt
from numpy import linspace


class StandMotor(IMS):
    def __init__(self, *args, kb1=None, kb2=None, **kwargs):
        if kb1 is None or kb2 is None:
            raise SyntaxError('kb1 and kb2 need to be defined')
        self.__init__(self, *args, **kwargs)
        self.kb1 = kb1
        self.kb2 = kb2
        self.kb1_move_positions = []
        self.kb2_move_positions = []
        self.move_in_progress = False
        self.step_in_progress = False
        self.current_step = 0

    def calc_kb1_move(self, steps):
        if self.move_in_progress:
            raise RuntimeError('A move is still in progress. Will not recalculate.')
        self.kb1_move_positions = np.linspace(self.position, self.kb1, steps)
        self.current_step = 0
        print('The following steps will be used:')
        print(self.kb1_move_positions)

    def calc_kb2_move(self, steps):
        if self.move_in_progress:
            raise RuntimeError('A move is still in progress. Will not recalculate.')
        self.kb2_move_positions = np.linspace(self.position, self.kb2, steps)
        self.current_step = 0
        print('The following steps will be used:')
        print(self.kb2_move_positions)

    def step_kb1(self):
        if self.kb1_move_positions == []:
            raise RuntimeError('A move must be calculated first')
        if self.step_in_progress:
            raise RuntimeError('A step is still in progress. Will not attempt next step.')
        self.move_in_progress = True
        self.step_in_progress = True
        desired_pos = self.kb1_move_positions[self.current_step]
        self.umv(desired_pos)
        if self.position < desired_pos - self.tolerance or self > desired_pos + self.tolerance:
            raise RuntimeError(f'The motor did not finish in the right position within the tolerance: {self.tolerance} {self.egu}')
        self.current_step += 1
        if self.current_step == len(self.kb1_move_positions):
            self.move_in_progress = False
        self.step_in_progress = False

class Stand1MS(Device):
    Ax = FCpt(IMS, 'CXI:1MS:MMS:04', kb1=84.3998, kb2=64.18, name='Ax')
    Ax = FCpt(IMS, 'CXI:1MS:MMS:04', kb1=84.3998, kb2=64.18, name='Ax')
    Ay = FCpt(IMS, 'CXI:1MS:MMS:05', kb1=81.5299, kb2=55.2699, name='Ay')
#    Az = FCpt(IMS, 'CXI:1MS:MMS:06', kb1=9.3998, kb2=9.39978, name='Az')
    By = FCpt(IMS, 'CXI:1MS:MMS:01', kb1=52.281, kb2=31.4952, name='By')
    Cx = FCpt(IMS, 'CXI:1MS:MMS:02', kb1=54.9002, kb2=37.3503, name='Cx')
    Cy = FCpt(IMS, 'CXI:1MS:MMS:03', kb1=52.3008, kb2=31.415, name='Cy')


class StandDG2(Device):
    Ax = FCpt(IMS, 'CXI:DG2:MMS:14', kb1=36.0798, kb2=20.33, name='Ax')
    Ay = FCpt(IMS, 'CXI:DG2:MMS:15', kb1=34.41, kb2=16.58, name='Ay')
#    Az = FCpt(IMS, 'CXI:DG2:MMS:16', kb1=0.2002, kb2=0.20021, name='Az')
    By = FCpt(IMS, 'CXI:DG2:MMS:11', kb1=39.88, kb2=21.018, name='By')
    Cx = FCpt(IMS, 'CXI:DG2:MMS:12', kb1=41.8487, kb2=25.662, name='Cx')
    Cy = FCpt(IMS, 'CXI:DG2:MMS:13', kb1=39.9501, kb2=20.988, name='Cy')
 
class StandDG3(Device):
     Ax = FCpt(IMS, 'CXI:DG3:MMS:09', kb1=90.7329, kb2=70.0217, name='Ax')
     Ay = FCpt(IMS, 'CXI:DG3:MMS:10', kb1=88.406, kb2=60.16, name='Ay')
#     Az = FCpt(IMS, 'CXI:DG3:MMS:11', kb1=-0.0034, kb2=-0.00323, name='Az')
     By = FCpt(IMS, 'CXI:DG3:MMS:06', kb1=91.088, kb2=61.9193, name='By')
     Cx = FCpt(IMS, 'CXI:DG3:MMS:07', kb1=91.8417, kb2=70.53, name='Cx')
     Cy = FCpt(IMS, 'CXI:DG3:MMS:08', kb1=95.2873, kb2=65.8574, name='Cy')
