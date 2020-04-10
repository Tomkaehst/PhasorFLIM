import numpy as np

from flimdata import flimdata

class IRF(flimdata):
    '''
    IRF() extends the flimdata class and thus inherits all methods and properties.
    An IRF is recorded using a regular PTU file. However, the spatial resolution
    is not that important.
    The IRF is created by initializing an IRF object with a path and channel ID.
    flimdata functions will load and process the file (all variables and arrays
    produced will be acceissble via the name naming scheme as in flimdata).
    Then, self.irf gets the overall_decays data, which will be the unprocessed IRF.
    Set self.irf = self.overall_decays to revert to raw IRF.
    '''
    def __init__(self, file_path: str, channel: int):

        self.file_path = file_path
        self.channel = channel
        self.spatial_binning = 5
        self.temporal_binning = 0

        super().__init__(
            file_path = self.file_path,
            channel = self.channel,
            spatial_binning = self.spatial_binning,
            temporal_binning = self.temporal_binning
        )

        self.irf = self.overall_decays
        self.irf_time_axis = self.time_axis
        self.standardize_irf()

        del self.flimarray

    def reset_irf(self):
        self.irf = self.overall_decays
        self.irf_time_axis = self.time_axis

    def standardize_irf(self):
        '''
        Standardize IRF, so that sum over array yields 1.
        Required, because otherwise amplitude parameter
        of decay model wouldn't correspond to maximum
        of decay.
        '''
        self.irf = self.irf / np.sum(self.irf)

    def cut_irf(self, left_cutoff: int = 0, right_cutoff: int = 0):
        '''
        Cut out irrelevant parts of IRF to avoid introduction
        of artifacts.
        IRF should have same length as decay.
        Thus, np.zeros() array is initialized and the trimmed
        IRF is added to the zeros array.
        '''
        self.irf = self.overall_decays
        self.irf[0:left_cutoff] = 0
        self.irf[right_cutoff:self.irf.shape[0]] = 0
        self.standardize_irf()

    def estimate_background(self):
        pass

    def set_background(self, value):
        self.irf -= int(value)
        self.irf = np.where(self.irf < 0, 0, self.irf)
        self.standardize_irf()