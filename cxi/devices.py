from ophyd import (Device, EpicsSignal, FormattedComponent as FC)

class Injector(Device):

    coarseX = FC(EpicsSignal, '{self._coarseX_name}')
    coarseY = FC(EpicsSignal, '{self._coarseY_name}')
    coarseZ = FC(EpicsSignal, '{self._coarseZ_name}')
                
    fineX = FC(EpicsSignal, '{self._fineX_name}')
    fineY = FC(EpicsSignal, '{self._fineY_name}')
    fineZ = FC(EpicsSignal, '{self._fineZ_name}')
                            
    def __init__(self, injector_name,
                       coarseX_name, coarseY_name, coarseZ_name, 
                       fineX_name, fineY_name, fineZ_name):
                                        
        self._coarseX_name = coarseX_name
        self._coarseY_name = coarseY_name
        self._coarseZ_name = coarseZ_name
                                                             
        self._fineX_name = fineX_name
        self._fineY_name = fineY_name
        self._fineZ_name = fineZ_name

        super().__init__(name=injector_name)
