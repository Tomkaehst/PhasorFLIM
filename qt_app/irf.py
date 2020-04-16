import numpy as np
from scipy import optimize

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

        self.irf = np.zeros(self.overall_decays.shape, dtype=np.float64)
        self.irf += self.overall_decays
        self.irf_time_axis = self.time_axis

        del self.flimarray


        # Initial parameters for IRF fitting by fitting
        # to sum of Gauss curves -> See self.n_gauss_terms
        self. fit_parameters = [
            2000,  # overall time shift
            0,  # mu of first component
            50,  # sigma of first component
            0,
            50,
            0,
            50,
            0,
            50
        ]

    def reset_irf(self):
        self.irf = np.zeros(self.overall_decays.shape, dtype=np.float64)
        self.irf += self.overall_decays
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
        self.irf[0:left_cutoff] = 0
        self.irf[right_cutoff:self.irf.shape[0]] = 0

    def set_background(self, value):
        self.irf -= value
        self.irf[np.where(self.irf < 0)] = 0



    def n_gauss_terms(self, t, *parameters, number_of_gauss_components = 10):
        '''
        Sum of n Gauss curves. Used to fit IRF.
        fit_paramerers is dynamically build depending
        on user-chosen number of gauss components = 
        number of Gauss curve terms.
        First term is *overall* shift of Gauss curve
        construct.
        E.g. f(x) = (1/(sigma1 * sqrt(2*pi))) * exp(-((t - mu1) - time_shift)**2 / (2*sigma1)**2) + 
                    (1/(sigma2 * sqrt(2*pi))) * exp(-((t - mu2) - time_shift)**2 / (2*sigma2)**2) + ...

        Structure of fit parameter list:
        [0]: overall time-shift of whole fuction
        [1]: IRF_mu_1, mu of first component
        [2]: IRF_sigma_2, sigma of first component
        [3]: IRF_mu_2, mu of second component

        #! First, I will hard-code a 10 component fit!
        #! It should work first, then make it pretty!
        ...
        '''


        # ! Rewrite this like fitting.gauss_laser_multiple_terms!!!
        out = \
            (1 / (parameters[2] * np.sqrt(2 * np.pi))) * np.exp(-((t - parameters[1]) - parameters[0])** 2 / (2 * parameters[2])** 2) + \
            (1 / (parameters[4] * np.sqrt(2 * np.pi))) * np.exp(-((t - parameters[3]) - parameters[0])** 2 / (2 * parameters[4])** 2) + \
            (1 / (parameters[6] * np.sqrt(2 * np.pi))) * np.exp(-((t - parameters[5]) - parameters[0])** 2 / (2 * parameters[6])** 2) + \
            (1 / (parameters[8] * np.sqrt(2 * np.pi))) * np.exp(-((t - parameters[7]) - parameters[0])** 2 / (2 * parameters[8])** 2)

        out = out / np.sum(out)

        return (out)
        
    
    def fit_irf_as_gauss(self):

        self.standardize_irf()

        try:
            optimized_parameters = optimize.curve_fit(
                self.n_gauss_terms,
                self.time_axis,
                self.irf,
                self.fit_parameters,
                method = 'trf'
                #bounds = bounds
            )

        except RuntimeError:
            print('Error during fitting of IRF: fit_irf_as_gauss()\n')

        self.fitted_irf = optimized_parameters[0]

        fitted_irf = self.n_gauss_terms(
            self.time_axis,
            *self.fitted_irf
        )

        return(fitted_irf)