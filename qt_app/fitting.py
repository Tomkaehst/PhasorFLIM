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
        self.optimized_parameters = None
        self.lifetime_image = None

        if(fit_settings is None):
            self.fit_settings = (
                1,
                np.amax(self.data),
                2500,
                2000,
                60
            )
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
        return(gauss)


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


    def get_irf_shift(self, measured_irf):
        '''
        Get best shift of *measured* IRF by brute-forcing.
        IRF shift of measured IRF cannot be optimized together with
        other model parameters using classic minimization algorithms,
        because shift is done with integer stepping.
        Brute-forcing best shift here and writing result
        into self.fit_setting[3]
        '''

        brute_range = (
            (self.fit_settings[0] - 1, self.fit_settings[0]),
            (self.fit_settings[1] - 1, self.fit_settings[1]),
            (self.fit_settings[2] - 1, self.fit_settings[2]),
            (-1000, 1000),
            (self.fit_settings[4] - 1, self.fit_settings[4])
        )

        fitted_shift = optimize.brute(
            func = self.minimize_poisson_deviance,
            ranges = brute_range,
            args=(self.time_axis, self.data, measured_irf),
            Ns = (1, 1, 1, 2000, 1)
        )

        print(fitted_shift)
        

        return(0)



    def add_poisson_noise(self, data, offset):
        """

        """

        decay = np.random.poisson(data, len(data))
        decay += np.random.poisson(offset, len(decay))
        return(decay)

    def convoluted_decay(self, time_axis, offset, amp, tau, IRF_mu, IRF_sigma, measured_irf = None ):
        """

        """

        if(measured_irf is None):
            IRF = self.gauss_laser(time_axis, IRF_mu, IRF_sigma)
        else:
           IRF = np.roll(measured_irf, int(IRF_mu)) #self.shift_irf(measured_irf, IRF_mu)

        decay = self.exp_decay_mono(time_axis, tau)

        convoluted_signal = np.convolve(IRF, decay)[0:len(time_axis)]
        convoluted_signal *= 10*amp
        convoluted_signal += offset

        return(convoluted_signal)


    def calculate_residuals(self, measured_irf = None):
        """

        """
        residuals = ((self.convoluted_decay(self.time_axis, *self.optimized_parameters['x'], measured_irf) - self.data)) / np.sqrt(self.data)

        return(residuals)


    def calculate_reduced_chi_square(self):
        try:
            fitted_curve = self.convoluted_decay(self.time_axis, *self.optimized_parameters)

        except ValueError:
            print('Error')
        return
            

    ## Objective functions
    def minimization_least_squares(self, start_parameters, time_axis, data, measured_irf = None, weighted = False):

        fitted = self.convoluted_decay(time_axis, *start_parameters, measured_irf)

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

        fitted = self.convoluted_decay(time_axis, *start_parameters, measured_irf)
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
        if(self.objective_function == 'Least Squares'):
            objective_function = self.minimization_least_squares
        else:
            objective_function = self.minimize_poisson_deviance

        decay_trimmed = decay[0:(len(decay) - cutoff)],
        time_axis_trimmed = self.time_axis[0:(len(self.time_axis) - cutoff)]

        try:
            self.optimized_parameters = optimize.minimize(
                objective_function,
                self.fit_settings,
                args = (time_axis_trimmed, decay_trimmed, measured_irf),
                method = minimization_method,
                bounds = self.parameter_bounds,
                options = {
                    'maxiter': 1000,
                    'disp': False,
                    'eps': [
                        0.1,
                        0.1,
                        0.1,
                        5,
                        0.1
                    ]
                }
            )
        except RuntimeWarning:
            print('\nFitting unsucessfull. See error message above!\n')

        fitted_curve = self.convoluted_decay(self.time_axis, *self.optimized_parameters['x'])
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
