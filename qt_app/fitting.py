import math
import numpy as np
import scipy.optimize as optimize
from scipy import interpolate
from numba import njit
import multiprocessing as mp

class fitter:
    def __init__(self, time_axis, data, objective_function = None, fit_settings = None):
        self.time_axis = time_axis
        self.data = data
        self.objective_function = objective_function
        self.irf = self.gauss_laser
        self.optimized_parameters = None
        self.lifetime_image = None

        if (fit_settings is None):
            self.decay_parameters = (
                1,
                np.amax(self.data),
                2500
            )
            self.IRF_parameters = (
                2000,
                60
            )
            self.fit_settings = self.decay_parameters + self.IRF_parameters

        else:
            self.fit_settings = fit_settings

        self.parameter_bounds = (
            (0, np.infty),  # Offset
            (0.01, np.infty),# Amplitide
            (1, np.infty),# Tau
            (-np.infty, np.infty),# IRF Mu
            (0.01, np.infty)  # IRF sigma
        )

        self.parameter_names = (
            'offset',
            'amplitude',
            'tau',
            'IRF_mu',
            'IRF_sigma'
        )


    def estimate_background(self, data):
        '''
        Calculates median of last 3 % of data.
        Used for weightung of values that have 0 counts, otherwise division will
        lead to NaN.
        '''
        sample_index_right_cutoff = math.floor(len(data) * 0.99)
        sample_index_left_cutoff = math.floor(len(data) * 0.96)

        background = np.median(data[sample_index_left_cutoff : sample_index_right_cutoff])

        return(background)


    def calculate_weights(self, data):
        """

        """

        weights = np.zeros((len(data)))
        weights = 1.0/np.sqrt(data, where = (data != 0))
        weights[np.where(data == 0)] = 1.0/np.sqrt(self.estimate_background(data))

        return(weights)

    @staticmethod
    @njit
    def exp_decay_mono(t, tau):
        """

        """
        return(np.exp(-t/tau))

    @staticmethod
    @njit
    def gauss_laser(t, mu, sigma):
        """

        """
        gauss = (1/(sigma*np.sqrt(2*np.pi))) * np.exp(-(t - mu)**2/(2*sigma)**2)
        return (gauss)
        
    def gauss_laser_multiple_terms(t, parameters):
        


    # def interpolate_irf(self, time_axis, measured_irf):
    #     """

    #     """

    #     irf_function = interpolate.interp1d(
    #         x = time_axis,
    #         y = measured_irf,
    #         bounds_error = False,
    #         fill_value = 0 # background_counts
    #     )

    #     irf_interpolated = irf_function(time_axis)

    #     return(irf_interpolated)

    #@staticmethod
    #@njit
    # def process_irf(IRF, time_axis, shift, background = 0):
    #     '''
    #     Processing IRF based on current model parameters: IRF_mu = shift, ...
    #     '''
    #     irf = IRF
    #     irf_time_axis = time_axis - np.max(time_axis)
    #     np.add(irf_time_axis, shift)

    #     return(irf, irf_time_axis)


    @staticmethod
    def shift_irf(shift, measured_irf):
        '''
        Shift measured IRF on time axis by rolling array.
        '''
        shifted_irf = np.roll(measured_irf, int(shift))
        
        return(shifted_irf)


    def shift_irf_2(self, irf_shift):

        # 1. Find IRF maximum peak: either max peak or where user defined left cut
        # 2. Shift IRF to left side of array -> np.roll
        # 3. Interpolate processed IRF 
        # 4. 
        pass



    def add_poisson_noise(self, data, offset):
        """

        """

        decay = np.random.poisson(data, len(data))
        decay += np.random.poisson(offset, len(decay))
        return(decay)


    def convoluted_decay(self, time_axis, parameters, measured_irf = None ):
        """

        """

        offset, amp, tau = parameters[0:3]
        IRF_parameters = parameters[3:len(parameters)]

        decay = self.exp_decay_mono(time_axis, tau)
        IRF = self.IRF(time_axis, *IRF_parameters)

        convoluted_signal = np.convolve(IRF, decay)[0:len(time_axis)]
        convoluted_signal *= 10*amp
        convoluted_signal += offset

        return(convoluted_signal)


    def calculate_residuals(self, measured_irf = None):
        """

        """
        residuals = ((self.convoluted_decay(self.time_axis, self.optimized_parameters['x'], measured_irf) - self.data)) / np.sqrt(self.data)

        return(residuals)


    def calculate_reduced_chi_square(self):
        try:
            fitted_curve = self.convoluted_decay(self.time_axis, self.optimized_parameters)

        except ValueError:
            print('Error')
        return
            

    ## Objective functions
    def minimization_least_squares(self, start_parameters, time_axis, data, measured_irf = None, weighted = False):

        fitted = self.convoluted_decay(time_axis, start_parameters, measured_irf)

        if(weighted):
            weights = self.calculate_weights(data)
            resids = ((data - fitted)**2 * weights) / fitted
        else:
            resids = ((data - fitted)**2) / fitted
            
        resids = np.sum(resids)

        return(resids)

    def minimize_poisson_deviance(self, start_parameters, time_axis, data, measured_irf = None):
        """
        From Bajzer et al., 1991
        """

        fitted = self.convoluted_decay(time_axis, start_parameters, measured_irf)
        with np.errstate(divide = 'ignore'):
            deviance = 2 * np.nansum(
                data * np.log(data / fitted) - (data - fitted)
            )
        return(deviance)


    def fit_decay(
        self,
        decay = None,
        measured_irf=None,
        minimization_method = 'L-BFGS-B',
        cutoff = 1):
        """

        """

        # Selecting objective function
        if(self.objective_function == 'Least Squares'):
            objective_function = self.minimization_least_squares
        else:
            objective_function = self.minimize_poisson_deviance


        # Check if measured IRF has been defined
        if (measured_irf is None):
            self.IRF = self.gauss_laser
        else:
            self.IRF = measured_irf
            serf.fit_settings

        # Trim data according to user-set cutoffs
        decay_trimmed = decay[0:(len(decay) - cutoff)],
        time_axis_trimmed = self.time_axis[0:(len(self.time_axis) - cutoff)]

        # Perform fit while catching Runtime Errors
        try:
            self.optimized_parameters = optimize.minimize(
                objective_function,
                self.fit_settings,
                args = (time_axis_trimmed, decay_trimmed, measured_irf),
                method = minimization_method,
                bounds = self.parameter_bounds,
                options = {
                    'maxiter': 1000,
                    'disp': False
                }
            )
        except RuntimeWarning:
            print('\nFitting unsucessfull. See error message above!\n')

        # Calculate fit with optimized parameters and weigted residuals
        fitted_curve = self.convoluted_decay(self.time_axis, self.optimized_parameters['x'])
        residuals = self.calculate_residuals()

        return(fitted_curve, residuals)



    def fit_image(self, photon_threshold = 100):
        ''' 

        ''' 
        if(len(self.data.shape) < 3):
            raise ValueError('fit object was not initialized with a FLIM array!')

        # Initialzing flat array for optimized values
        lifetime_image = np.zeros((self.data.shape[0] + self.data.shape[1]))

        # Flatten data array to map cores to pixels
        self.data = self.data.flatten()
        self.data = mp.Array('f', self.data)


        #print('Fitting line', x)

        #self.lifetime_image = lifetime_image


    def apply_function_multiprocessing(self, args):
        pass
