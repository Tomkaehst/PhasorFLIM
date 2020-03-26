import numpy as np
import math
import scipy.optimize as optimize
from scipy import interpolate
from numba import njit

class fitter:
    def __init__(self, time_axis, data, fit_settings = None):
        self.time_axis = time_axis
        self.data = data
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
            (0, np.infty),
            (0, np.infty),
            (0, np.infty),
            (0, np.infty),
            (0, np.infty)
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
        Calculates median of last 7 % of data.
        Used for weightung of values that have 0 counts, otherwise division will
        lead to NaN.
        '''
        sample_index_right_cutoff = math.floor(len(data) * 0.97)
        sample_index_left_cutoff = math.floor(len(data) * 0.90)

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


    def interpolate_irf(self, time_axis, measured_irf, leftcutoff = 100, rightcutoff = 1000):
        """

        """

        irf_cutoff = measured_irf[leftcutoff:rightcutoff]
        irf_cutoff = irf_cutoff / np.sum(measured_irf)

        time_axis_cutoff = time_axis[leftcutoff:rightcutoff]

        irf_function = interpolate.interp1d(
            x = time_axis_cutoff,
            y = irf_cutoff,
            bounds_error = False,
            fill_value = 0 # background_counts
        )

        irf_interpolated = irf_function(time_axis)

        return(irf_interpolated)


    def add_poisson_noise(self, data, offset):
        """

        """

        decay = np.random.poisson(data, len(data))
        decay += np.random.poisson(offset, len(decay))
        return(decay)

    def convoluted_decay(self, time_axis, offset, amp, tau, IRF_mu, IRF_sigma, measured_irf = None):
        """

        """

        if(measured_irf is None):
            IRF = self.gauss_laser(time_axis, IRF_mu, IRF_sigma)
        else:
            IRF = self.interpolate_irf(time_axis, measured_irf)

        decay = self.exp_decay_mono(time_axis, tau)

        convoluted_signal = np.convolve(IRF, decay)[0:len(time_axis)]
        convoluted_signal *= 10*amp
        convoluted_signal += offset

        return(convoluted_signal)


    def residuals(self, estimated_parameters, time_axis, data, measured_irf, weighted = True):
        """

        """

        if(weighted):
            weights = self.calculate_weights(data)
            residuals = (data - self.convoluted_decay(time_axis, *estimated_parameters, measured_irf) ** 2) * weights
        else:
            residuals = (data - self.convoluted_decay(time_axis, *estimated_parameters, measured_irf) ** 2)

        return(residuals)

    def calculate_reduced_chi_square(self):
        try:
            fitted_curve = self.convoluted_decay(t, *self.optimized_parameters)
            

    ## Objective functions

    def minimization_least_squares(self, para_est, t, data, weighted = False):
        """

        """

        fitted = self.convoluted_decay(t, *para_est)

        if(weighted):
            weights = self.calculate_weights(data)
            resids = ((data - fitted)**2 * weights) / data
        else:
            resids = ((fitted - data)**2) / data

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
        measured_irf = None,
        objective_function = None,
        minimization_method = 'SLSQP',
        cutoff = 1):
        """

        """

        if(objective_function == 'least_squares'):
            objective_function = self.minimization_least_squares
        else:
            objective_function = self.minimize_poisson_deviance


        data_trimmed = self.data[0:(len(self.data) - cutoff)],
        time_axis_trimmed = self.time_axis[0:(len(self.time_axis) - cutoff)]

        try:
            self.optimized_parameters = optimize.minimize(
                objective_function,
                self.fit_settings,
                args = (time_axis_trimmed, data_trimmed, measured_irf),
                method = minimization_method,
                bounds = self.parameter_bounds,
                options = {
                    'maxiter': 1000,
                    'disp': False
                }
            )
        except:
            print('\nFitting unsucessfull. See error message above!\n')

        #print(self.optimized_parameters)

        fitted_curve = self.convoluted_decay(self.time_axis, *self.optimized_parameters['x'])

        return(fitted_curve, self.optimized_parameters)